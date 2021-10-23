# !/usr/bin/env python
import pika
import threading
from .machine import Machine
from .model_machine import Piece
from . import Config, Session

my_machine = Machine()


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
        dictionary = eval(body)
        number_of_pieces = dictionary['number_of_pieces']
        order_id = dictionary['order_id']
        session = Session()
        pieces = []
        for i in range(number_of_pieces):
            piece = Piece()
            piece.order_id = order_id
            pieces.append(piece)
            session.add(piece)
        session.commit()
        my_machine.add_pieces_to_queue(pieces)
        session.commit()

