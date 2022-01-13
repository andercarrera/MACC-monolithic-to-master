import json
import ssl
import threading

import pika

from . import Session, Config
from .log import create_log
from .model_payment import Payment
from .publisher_payment import publish_msg

piece_price_A = 10
piece_price_B = 5

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
                host=Config.RABBITMQ_IP, port=5671, virtual_host='/', credentials=credentials))
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
    def payment_reserved_accepted(channel, method, properties, body):
        print("Payment reserve callback", flush=True)
        session = Session()
        content = json.loads(body)

        try:
            client = session.query(Payment).filter(Payment.client_id == content['client_id']).one()
            money = content['number_of_pieces_A'] * piece_price_A
            money += content['number_of_pieces_B'] * piece_price_B

            if client.payment_amount < money:
                raise Exception("Client does not have enough money")

            client.payment_amount -= money
            client.payment_reserved += money
            session.commit()
            create_log('Payment reserved', 'info')
            content['status'] = True
            content['type'] = 'PAYMENT'
            publish_msg("sagas_response_exchange", "sagas_process.create_order", json.dumps(content))
        except KeyError as e:
            create_log(str(e), 'error')
            session.rollback()
        except Exception as e:
            create_log(str(e), 'error')
            content['status'] = False
            content['type'] = 'PAYMENT'
            content['description'] = "Not enough credit"
            publish_msg("sagas_response_exchange", "sagas_process.create_order", json.dumps(content))
            session.rollback()
        session.close()

    @staticmethod
    def payment_reserve_cancelled(channel, method, properties, body):
        print("Payment cancel callback", flush=True)
        session = Session()
        content = json.loads(body)
        try:
            client = session.query(Payment).filter(Payment.client_id == content['client_id']).one()
            money = content['number_of_pieces_A'] * piece_price_A
            money += content['number_of_pieces_B'] * piece_price_B
            client.payment_amount += money
            client.payment_reserved -= money
            session.commit()
            content['description'] = "Invalid ZIP code"
            publish_msg("sagas_commands", "order.reject", json.dumps(content))
        except Exception as e:
            create_log(str(e), 'error')
            session.rollback()
        session.close()

    @staticmethod
    def payment_accepted(channel, method, properties, body):
        print("Payment accepted, removing reserved money callback", flush=True)
        session = Session()
        content = json.loads(body)
        try:
            client = session.query(Payment).filter(Payment.client_id == content['client_id']).one()
            money = content['number_of_pieces_A'] * piece_price_A
            money += content['number_of_pieces_B'] * piece_price_B
            client.payment_reserved -= money
            session.commit()
        except Exception as e:
            create_log(str(e), 'error')
            session.rollback()
        session.close()

    @staticmethod
    def payment_refund(channel, method, properties, body):
        print("Payment refund callback", flush=True)
        session = Session()
        content = json.loads(body)
        try:
            client = session.query(Payment).filter(Payment.client_id == content['client_id']).one()
            money = content['number_of_pieces_A'] * piece_price_A
            money += content['number_of_pieces_B'] * piece_price_B
            client.payment_amount += money
            session.commit()
            content['description'] = None
        except Exception as e:
            create_log(str(e), 'error')
            session.rollback()

        content['type'] = 'ORDER'
        publish_msg("sagas_response_exchange", "sagas_process.cancel_order", json.dumps(content))
        session.close()
