# !/usr/bin/env python
import ssl
import threading
import time

import pika

from . import Config, Session
from .machine import Machine
from .model_machine import Piece

machine = Machine()

# solves the following: https://stackoverflow.com/questions/28768530/certificateerror-hostname-doesnt-match
ssl.match_hostname = lambda cert, hostname: True


class ThreadedConsumer:
    context = ssl.create_default_context(
        cafile=Config.CA_CERTS)
    context.load_cert_chain(Config.CERT_FILE,
                            Config.KEY_FILE)
    ssl_options = pika.SSLOptions(context, Config.RABBITMQ_IP)

    def __init__(self, exchange_name, routing_key, callback_func, queue):
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self.callback_func = callback_func
        self.queue = queue
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
        result = channel.queue_declare(queue=self.queue, durable=True)
        queue_name = result.method.queue
        channel.queue_bind(exchange=self.exchange_name, queue=queue_name, routing_key=self.routing_key)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue_name, on_message_callback=self.callback_func)
        thread = threading.Thread(target=channel.start_consuming)
        thread.start()

    @staticmethod
    def produce_piece_A(channel, method, properties, body):
        print("Producing A piece in machine_2", flush=True)
        order_id = int(body)
        session = Session()

        piece = Piece(order_id=order_id,
                      type="A")

        session.add(piece)
        session.commit()

        machine.add_piece_to_queue(piece)
        session.commit()

        time.sleep(2)
        channel.basic_ack(delivery_tag=method.delivery_tag)

    @staticmethod
    def produce_piece_B(channel, method, properties, body):
        print("Producing B piece in machine_2", flush=True)
        order_id = int(body)
        session = Session()

        piece = Piece(order_id=order_id,
                      type="B")

        session.add(piece)
        session.commit()

        machine.add_piece_to_queue(piece)
        session.commit()

        time.sleep(2)
        channel.basic_ack(delivery_tag=method.delivery_tag)
