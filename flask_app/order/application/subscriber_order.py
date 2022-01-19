# !/usr/bin/env python
import json
import ssl
import threading

import pika
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import abort, NotFound

from . import Config, Session
from .log import create_log
from .model_order import Order, Saga
from .publisher_order import publish_msg
from .state_machine import get_coordinator

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
        credentials = pika.PlainCredentials(username=Config.RABBITMQ_USER, password=Config.RABBITMQ_PASS)
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
    def reject_order(channel, method, properties, body):
        print("Order cancel callback", flush=True)
        session = Session()
        content = json.loads(body)
        try:
            order = session.query(Order).get(content['order_id'])
            order.status = order.STATUS_CANCELLED
            session.commit()
        except Exception as e:
            create_log(str(e), 'error')
            session.rollback()

        content = {"order_id": content['order_id'],
                   "state_machine": Saga.SAGAS_CREATE_ORDER,
                   "status": "Order rejected",
                   "description": content['description']}
        publish_msg("sagas_response_exchange", "sagas_persist.create_order", json.dumps(content))
        session.close()

    @staticmethod
    def cancel_order(channel, method, properties, body):
        print("Order cancel callback", flush=True)
        session = Session()
        content = json.loads(body)
        try:
            order = session.query(Order).get(content['order_id'])
            order.status = order.STATUS_CANCELLED
            session.commit()
        except Exception as e:
            create_log(str(e), 'error')
            session.rollback()

        content = {"order_id": content['order_id'],
                   "state_machine": Saga.SAGAS_CANCEL_ORDER,
                   "status": "Order cancelled",
                   "description": None}
        publish_msg("sagas_response_exchange", "sagas_persist.create_order", json.dumps(content))
        session.close()

    @staticmethod
    def order_preparing(channel, method, properties, body):
        print(" [x] %r:%r" % (method.routing_key, body))
        content = json.loads(body)
        order_id = content['order_id']
        session = Session()
        try:
            order = session.query(Order).get(order_id)
            order.status = order.STATUS_PREPARING
            session.commit()
        except NoResultFound:
            abort(NotFound.code, "Order not found for given order id")
        except KeyError:
            session.rollback()
            session.close()
        session.close()

    @staticmethod
    def order_accepted(channel, method, properties, body):
        print(" [x] %r:%r" % (method.routing_key, body))
        order_id = int(body)
        session = Session()
        try:
            order = session.query(Order).get(order_id)
            order.status = order.STATUS_ACCEPTED
            session.commit()
        except NoResultFound:
            abort(NotFound.code, "Order not found for given order id")
        except KeyError:
            session.rollback()
            session.close()
        session.close()

    # Sagas callback
    @staticmethod
    def sagas_create_order_response(ch, method, properties, body):
        content = json.loads(body)
        coordinator = get_coordinator()
        coordinator.process_create_order(content)

    @staticmethod
    def sagas_cancel_order_response(ch, method, properties, body):
        content = json.loads(body)
        coordinator = get_coordinator()
        coordinator.process_cancel_order(content)

    @staticmethod
    def persist_state(ch, method, properties, body):
        session = Session()
        content = json.loads(body)
        try:
            new_state = Saga(
                order_id=content['order_id'],
                state_machine=content['state_machine'],
                status=content['status'],
                description=content['description']
            )
            session.add(new_state)
            session.commit()
            create_log('SAGAS: ' + new_state.state_machine + ' ' + new_state.status, 'sagas')
        except KeyError:
            session.rollback()
            session.close()
        session.close()
