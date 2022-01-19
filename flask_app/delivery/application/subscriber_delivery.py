# !/usr/bin/env python
import json
import ssl
import threading

import pika
from flask import abort
from werkzeug.exceptions import NotFound, BadRequest

from . import Config, Session
from .log import create_log
from .model_delivery import Delivery
from .publisher_delivery import publish_msg

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
    def delivery_ready(channel, method, properties, body):
        print(" [x] %r:%r" % (method.routing_key, body), flush=True)
        order_id = int(body)
        session = Session()
        delivery = session.query(Delivery).filter_by(order_id=order_id).first()
        if not delivery:
            abort(NotFound.code)
        try:
            delivery.status = Delivery.STATUS_READY
            session.commit()
        except KeyError:
            session.rollback()
            session.close()
            abort(BadRequest.code)
        session.close()

    @staticmethod
    def create_delivery(ch, method, properties, body):
        print("Delivery create callback", flush=True)
        session = Session()
        print("Delivery create body ", flush=True)
        print(body, flush=True)
        content = json.loads(body)

        try:
            new_delivery = Delivery(
                order_id=content['order_id'],
                status=Delivery.STATUS_PREPARING,
                address=content['address']
            )
            if content['zip'].startswith('01') or content['zip'].startswith('20') or content['zip'].startswith('48'):
                session.add(new_delivery)
                session.commit()
                session.close()
                content['status'] = True
                content['type'] = 'DELIVERY'
            else:
                session.close()
                create_log('Delivery cancelled, wrong ZIP code', 'info')
                content['status'] = False
                content['type'] = 'DELIVERY'

            publish_msg("sagas_response_exchange", "sagas_process.create_order", json.dumps(content))

        except KeyError:
            session.rollback()
            session.close()

    # Delivery reserve cancel
    @staticmethod
    def remove_delivery(ch, method, properties, body):
        print("Remove delivery callback", flush=True)
        session = Session()
        content = json.loads(body)
        try:
            session.query(Delivery).filter(Delivery.order_id == content['order_id']).one().delete()
            session.commit()
        except Exception as e:
            create_log(str(e), 'error')
            session.rollback()
        session.close()

    @staticmethod
    def delivery_delivered(ch, method, properties, body):
        print("Delivery delivered callback", flush=True)
        session = Session()
        order_id = int(body)
        try:
            new_delivery = Delivery(
                order_id=order_id,
                status=Delivery.STATUS_DELIVERED,
            )
            delivery = session.query(Delivery).filter(Delivery.order_id == new_delivery.order_id).one()
            delivery.status = Delivery.STATUS_DELIVERED
            session.commit()
            create_log('Delivery delivered', 'info')
        except Exception as e:
            session.rollback()
            create_log(str(e), 'error')
        session.close()

    @staticmethod
    def cancel_delivery(ch, method, properties, body):
        print("Delivery cancel callback", flush=True)
        session = Session()
        content = json.loads(body)
        try:
            new_delivery = Delivery(
                order_id=content['order_id'],
                status=Delivery.STATUS_CANCELLED,
            )
            delivery = session.query(Delivery).filter(Delivery.order_id == new_delivery.order_id).one()
            delivery.status = Delivery.STATUS_CANCELLED
            session.commit()
            create_log('Delivery cancelled', 'info')
        except Exception as e:
            session.rollback()
            create_log(str(e), 'error')
        content['type'] = 'PAYMENT'
        publish_msg("sagas_response_exchange", "sagas_process.cancel_order", json.dumps(content))
        session.close()
