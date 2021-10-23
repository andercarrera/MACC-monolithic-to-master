# !/usr/bin/env python
import ssl
import threading

import pika

from . import Config, Session, publisher_order
from .model_order import Order

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
    def check_status(channel, method, properties, body):
        print(" [x] %r:%r" % (method.routing_key, body))
        dictionary = eval(body)
        order_id = dictionary['order_id']
        status = dictionary['payment_status']
        session = Session()
        order = session.query(Order).get(order_id)
        if status == "Accepted":
            datos = {"number_of_pieces": order.number_of_pieces,
                     "order_id": order_id}
            order.status = order.STATUS_CREATED
            publisher_order.publish_msg("event_exchange", "order.payed", str(datos))
        elif status == "Denied":
            order.status = order.STATUS_CANCELLED
        session.commit()
