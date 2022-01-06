# !/usr/bin/env python
import json
import ssl
import threading

import pika
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import NotFound, abort

from . import Config, Session, log
from .log import create_log
from .model_warehouse import Order, Piece
from .publisher_warehouse import publish_msg, publish_round_robin_msg

# solves the following: https://stackoverflow.com/questions/28768530/certificateerror-hostname-doesnt-match
ssl.match_hostname = lambda cert, hostname: True


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
                number_of_pieces=content['number_of_pieces'],
                pieces_created=0,
                status=Order.STATUS_PREPARING
            )
            print(new_order.as_dict(), flush=True)
            session.add(new_order)
            session.commit()

            number_of_pieces = content['number_of_pieces']

            warehouse_pieces = session.query(Piece).filter(Piece.order_id == None).all()
            print("warehouse Pieces:", flush=True)
            print(warehouse_pieces, flush=True)

            pieces_left_to_produce = number_of_pieces - len(warehouse_pieces)

            print("pieces_left_to_produce", flush=True)
            print(pieces_left_to_produce, flush=True)

            pieces_to_take = ThreadedConsumer.calculate_pieces_to_take_from_warehouse(number_of_pieces,
                                                                                      warehouse_pieces)

            order = session.query(Order).get(order_id)
            for warehouse_piece in range(pieces_to_take):
                piece = session.query(Piece).filter(Piece.order_id == None).first()
                piece.order_id = order_id
                order.pieces_created += 1
                session.commit()

            if pieces_left_to_produce > 0:
                for i in range(pieces_left_to_produce):
                    publish_round_robin_msg("event_exchange", "machine.produce_piece", str(content['order_id']))
            else:
                order.status = order.STATUS_ACCEPTED
                publish_msg("event_exchange", "order.accepted", str(order_id))
                publish_msg("event_exchange", "delivery.ready", str(order_id))
                session.commit()

        except KeyError as e:
            log.create_log(e, 'error')
            session.rollback()
            session.close()
        session.close()

    @staticmethod
    def calculate_pieces_to_take_from_warehouse(number_of_pieces, warehouse_pieces):
        if len(warehouse_pieces) >= number_of_pieces:
            pieces_to_take = number_of_pieces
        else:
            pieces_to_take = len(warehouse_pieces)
        return pieces_to_take

    @staticmethod
    def piece_finished(channel, method, properties, body):
        print(" [x] %r:%r" % (method.routing_key, body))
        print("Warehouse piece finished", flush=True)
        session = Session()
        order_id = int(body)
        try:
            order = session.query(Order).get(order_id)
            if order.pieces_created < order.number_of_pieces:
                piece = Piece(order_id=order_id)
                session.add(piece)
                order.pieces_created += 1
                session.commit()
            if order.pieces_created == order.number_of_pieces:
                order.status = order.STATUS_ACCEPTED
                publish_msg("event_exchange", "order.accepted", body)
                publish_msg("event_exchange", "delivery.ready", body)
                session.commit()
        except NoResultFound:
            abort(NotFound.code, "Order not found for given order id")
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

            pieces = session.query(Piece).filter(Piece.order_id == order_id)

            for piece in pieces:
                print("Removing piece from order ID: {}".format(order_id), flush=True)
                session.delete(piece)
                session.commit()

        except NoResultFound:
            session.close()
        except KeyError as e:
            log.create_log(e, 'error')
            session.rollback()
            session.close()
        session.close()

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
        session.close()
