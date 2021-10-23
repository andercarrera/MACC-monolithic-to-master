#!/usr/bin/env python
import pika
from . import Config


def publish_msg(exchange, routing_key, message):
    credentials = pika.PlainCredentials(username='guest', password='guest')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=Config.RABBITMQ_IP, port=5672, credentials=credentials))
    channel = connection.channel()

    channel.exchange_declare(exchange=exchange, exchange_type='topic')
    channel.basic_publish(
        exchange=exchange, routing_key=routing_key, body=message)
    print(" [x] Sent %r:%r" % (routing_key, message))
    connection.close()
