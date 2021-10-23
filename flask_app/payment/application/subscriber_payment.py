# !/usr/bin/env python
import pika
import threading
import requests
from .model_payment import Payment
from . import Session, Config

base_url_order = "http://{}:{}/".format(Config.ORDER_IP, Config.GUNICORN_PORT)
piece_price = 10


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
    def check_balance(channel, method, properties, body):
        print(" [x] %r:%r" % (method.routing_key, body))
        dictionary = eval(body)
        number_of_pieces = dictionary['number_of_pieces']
        client_id = dictionary['client_id']
        order_id = dictionary['order_id']

        # pieces_id(number_of_pieces, client_id, order_id)
        order_cost = number_of_pieces * piece_price
        balance = 0
        session = Session()
        try:
            payment = session.query(Payment).filter_by(client_id=client_id).first()
            if payment is not None:
                balance = payment.payment_amount
                print(balance)
        except KeyError:
            session.close()
            print("No client id")

        if order_cost > balance:
            print(order_cost)
            print("order_cost > balance")
            order_accepted(order_id, False)
        else:
            try:
                balance = del_payment(client_id) - order_cost
                new_payment = Payment(
                    description="Order payment",
                    payment_amount=balance,
                    client_id=client_id
                )
                session.add(new_payment)
                order_accepted(order_id, True)
                session.commit()
            except KeyError:
                session.rollback()
                session.close()
        session.close()


def order_accepted(order_id, payed):
    print("Hola")
    if payed:
        payment_status = "Accepted"
    else:
        payment_status = "Denied"

    url = "{}payment_status".format(base_url_order)
    datos = {"order_id": order_id,
             "payment_status": payment_status}
    requests.post(url, json=datos)


def del_payment(client_id):
    session = Session()
    payment = session.query(Payment).filter(Payment.client_id == client_id)
    if not payment:
        session.close()
    money = 0
    for p in payment:
        print("Usr id: {} money: {}\n".format(p.client_id, p.payment_amount))
        money += p.payment_amount
        session.delete(p)
        session.commit()
    session.close()
    return money

