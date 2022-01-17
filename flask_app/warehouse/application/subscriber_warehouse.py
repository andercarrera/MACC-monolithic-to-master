# !/usr/bin/env python
import json
import ssl
import threading

import pika
from sqlalchemy.orm.exc import NoResultFound

from . import Config, Session, log
from .log import create_log
from .model_warehouse import Order, Piece
from .publisher_warehouse import publish_msg, publish_round_robin_msg

# solves the following: https://stackoverflow.com/questions/28768530/certificateerror-hostname-doesnt-match
ssl.match_hostname = lambda cert, hostname: True


def save_piece_without_order_id(machine_id, piece_type):
    session = Session()
    piece = Piece(type=piece_type,
                  machine_id=machine_id)
    session.add(piece)
    session.commit()
    session.flush()
    session.close()


class ThreadedConsumer:
    context = ssl.create_default_context(
        cafile=Config.CA_CERTS)
    context.load_cert_chain(Config.CERT_FILE,
                            Config.KEY_FILE)
    ssl_options = pika.SSLOptions(context, Config.RABBITMQ_IP)

    def __init__(self, exchange_name, routing_key, callback_func):
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.callback_func = callback_func
        self.rabbitMQConnection()

    def rabbitMQConnection(self):
        credentials = pika.PlainCredentials(username='rabbitmq', password='rabbitmq')
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                ssl_options=self.ssl_options,
                host=Config.RABBITMQ_IP, port=5671, credentials=credentials))
        channel = connection.channel()
        channel.exchange_declare(exchange=self.exchange_name, exchange_type='topic')

        # Create queue
        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=self.exchange_name, queue=queue_name, routing_key=self.routing_key)
        channel.basic_consume(queue=queue_name, on_message_callback=self.callback_func, auto_ack=True)
        thread = threading.Thread(target=channel.start_consuming)
        thread.start()

    @staticmethod
    def start_producing(channel, method, properties, body):
        print('New order warehouse callback', flush=True)
        content = json.loads(body)
        session = Session()

        order_id = content['order_id']
        try:
            new_order = Order(
                id=order_id,
                client_id=content['client_id'],
                number_of_pieces_A=content['number_of_pieces_A'],
                number_of_pieces_B=content['number_of_pieces_B'],
                status=Order.STATUS_PREPARING
            )
            print(new_order.as_dict(), flush=True)
            session.add(new_order)
            session.commit()
            session.flush()

            number_of_pieces_A = content['number_of_pieces_A']
            number_of_pieces_B = content['number_of_pieces_B']

            warehouse_pieces_A = session.query(Piece).filter(Piece.order_id == None, Piece.type == "A").all()
            warehouse_pieces_B = session.query(Piece).filter(Piece.order_id == None, Piece.type == "B").all()

            pieces_left_to_produce_A = number_of_pieces_A - len(warehouse_pieces_A)
            pieces_left_to_produce_B = number_of_pieces_B - len(warehouse_pieces_B)

            pieces_to_take_A = ThreadedConsumer.calculate_pieces_to_take_from_warehouse(number_of_pieces_A,
                                                                                        warehouse_pieces_A)
            pieces_to_take_B = ThreadedConsumer.calculate_pieces_to_take_from_warehouse(number_of_pieces_B,
                                                                                        warehouse_pieces_B)

            order = session.query(Order).get(order_id)

            for warehouse_piece in range(pieces_to_take_A):
                piece = session.query(Piece).filter(Piece.order_id == None, Piece.type == "A").first()
                piece.order_id = order_id
                order.pieces_created_A += 1
                session.commit()
                session.flush()

            for warehouse_piece in range(pieces_to_take_B):
                piece = session.query(Piece).filter(Piece.order_id == None, Piece.type == "B").first()
                piece.order_id = order_id
                order.pieces_created_B += 1
                session.commit()
                session.flush()

            if pieces_left_to_produce_A > 0:
                for i in range(pieces_left_to_produce_A):
                    publish_round_robin_msg("event_exchange", "machine.produce_piece_A", str(content['order_id']),
                                            'piece_A')
            else:
                ThreadedConsumer.order_ready(order, order_id, session)

            if pieces_left_to_produce_B > 0:
                for i in range(pieces_left_to_produce_B):
                    publish_round_robin_msg("event_exchange", "machine.produce_piece_B", str(content['order_id']),
                                            'piece_B')
            else:
                ThreadedConsumer.order_ready(order, order_id, session)
        except KeyError as e:
            log.create_log(e, 'error')
            session.rollback()
            session.close()
        session.close()

    @staticmethod
    def order_ready(order, order_id, session):
        order.status = order.STATUS_ACCEPTED
        publish_msg("event_exchange", "order.accepted", str(order_id))
        publish_msg("event_exchange", "delivery.ready", str(order_id))
        session.commit()
        session.flush()

    @staticmethod
    def calculate_pieces_to_take_from_warehouse(number_of_pieces, warehouse_pieces):
        if len(warehouse_pieces) >= number_of_pieces:
            pieces_to_take = number_of_pieces
        else:
            pieces_to_take = len(warehouse_pieces)
        return pieces_to_take

    @staticmethod
    def piece_finished(channel, method, properties, body):
        print("Warehouse piece finished callback", flush=True)
        print(" [x] %r:%r" % (method.routing_key, body))
        session = Session()
        content = json.loads(body)
        order_id = content['order_id']
        piece_type = content['type']
        machine_id = content['machine']

        print_msg = str(piece_type + " piece type received in warehouse by machine " + str(machine_id))
        create_log(print_msg, 'info')
        print(print_msg, flush=True)

        if order_id is None:
            save_piece_without_order_id(machine_id, piece_type)
        else:
            try:
                order = session.query(Order).get(order_id)
                if order.status == order.STATUS_CANCELLED:
                    save_piece_without_order_id(machine_id, piece_type)

                if order.status == order.STATUS_PREPARING:
                    piece = Piece(order_id=order_id,
                                  type=piece_type,
                                  machine_id=machine_id)
                    session.add(piece)

                    if piece_type == "A":
                        order.pieces_created_A += 1
                    if piece_type == "B":
                        order.pieces_created_B += 1
                    session.commit()
                    session.flush()

                    if order.pieces_created_A == order.number_of_pieces_A and order.pieces_created_B == order.number_of_pieces_B:
                        ThreadedConsumer.order_ready(order, order_id, session)
            except NoResultFound:
                # Si no encuentra la order -≥ Añadir pieza sin order (viene de warehouse, adelantar producción)
                print("Warehouse piece {} finished without order_id, forwarding production...".format(piece_type),
                      flush=True)
                save_piece_without_order_id(machine_id, piece_type)
            except KeyError as e:
                log.create_log(e, 'error')
                session.rollback()
                session.close()
            session.close()

    @staticmethod
    def pieces_delivered(channel, method, properties, body):
        print(" [x] %r:%r" % (method.routing_key, body))
        order_id = int(body)
        session = Session()
        try:
            order = session.query(Order).get(order_id)
            order.status = order.STATUS_DELIVERED
            session.commit()
            session.flush()

            pieces = session.query(Piece).filter(Piece.order_id == order_id)

            for piece in pieces:
                print("Removing piece from order ID: {}".format(order_id), flush=True)
                session.delete(piece)
                session.commit()
                session.flush()

        except NoResultFound:
            session.close()
        except KeyError as e:
            log.create_log(e, 'error')
            session.rollback()
            session.close()
        session.close()

    # TODO: cuando se cancela la orden, warehouse se queda atascado.
    @staticmethod
    def cancel_order(channel, method, properties, body):
        print("Warehouse order cancel callback", flush=True)
        session = Session()
        content = json.loads(body)

        order_id = content['order_id']
        try:
            order = session.query(Order).get(order_id)
            order.status = order.STATUS_CANCELLED
            session.commit()

            pieces = session.query(Piece).filter(Piece.order_id == order_id)

            for piece in pieces:
                print("Cancelling piece from order ID: {}".format(order_id), flush=True)
                piece.order_id = None
                session.commit()

        except NoResultFound:
            session.close()
        except Exception as e:
            create_log(str(e), 'error')
            session.rollback()

    @staticmethod
    def forward_production(channel, method, properties, body):
        print('Forward production', flush=True)
        content = json.loads(body)
        session = Session()
        try:
            number_of_pieces_A = content['number_of_pieces_A']
            number_of_pieces_B = content['number_of_pieces_B']

            for i in range(number_of_pieces_A):
                publish_round_robin_msg("event_exchange", "machine.produce_piece_A", '',
                                        'piece_A')

            for i in range(number_of_pieces_B):
                publish_round_robin_msg("event_exchange", "machine.produce_piece_B", '',
                                        'piece_B')
        except KeyError as e:
            log.create_log(e, 'error')
            session.rollback()
            session.close()
        session.close()
