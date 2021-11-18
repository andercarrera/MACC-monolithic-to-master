# !/usr/bin/env python
import json
import ssl
import threading
import pika
from flask import abort
from werkzeug.exceptions import NotFound, BadRequest
from . import Config, Session
from .model_delivery import Delivery

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
    def create_delivery(channel, method, properties, body):
        print(" [x] %r:%r" % (method.routing_key, body), flush=True)
        dictionary = json.loads(body)
        order_id = dictionary['order_id']
        session = Session()
        try:
            new_delivery = Delivery(
                order_id=order_id,
                status=Delivery.STATUS_PREPARING
            )
            session.add(new_delivery)
            session.commit()
        except KeyError:
            session.rollback()
            session.close()
            abort(BadRequest.code)
        session.close()
