# !/usr/bin/env python
import pika
import threading
from .model_order import Order
from . import Config, Session, publisher_order


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
