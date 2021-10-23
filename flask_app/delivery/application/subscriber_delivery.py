# !/usr/bin/env python
import pika
import threading
from flask import abort
from werkzeug.exceptions import NotFound, BadRequest
from .model_delivery import Delivery
from . import Config, Session


class ThreadedConsumer:
    def __init__(self, exchange_name, routing_key, callback_func):
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.callback_func = callback_func
        self.rabbitMQConnection()

    def rabbitMQConnection(self):
        credentials = pika.PlainCredentials(username='guest', password='guest')
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=Config.RABBITMQ_IP, port=5672, credentials=credentials))
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
        dictionary = eval(body)
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
