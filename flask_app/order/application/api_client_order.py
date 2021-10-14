import requests
from .config_order import Config

base_url_delivery = "http://{}:{}/".format(Config.DELIVERY_IP, Config.GUNICORN_PORT)
base_url_machine = "http://{}:{}/".format(Config.MACHINE_IP, Config.GUNICORN_PORT)
base_url_payment = "http://{}:{}/".format(Config.PAYMENT_IP, Config.GUNICORN_PORT)



def send_pieces(new_order):
    pieces_url = str(base_url_machine + "pieces")
    pieces_data = {"number_of_pieces": new_order.number_of_pieces,
                   "order_id": new_order.id}
    requests.post(pieces_url, json=pieces_data)


def create_delivery(new_order):
    delivery_url = str(base_url_delivery + "delivery")
    delivery_data = {"order_id": new_order.id}
    requests.post(delivery_url, json=delivery_data)


def check_balance(order_id):
    balance_url = str(base_url_payment + "neworder/{}".format(order_id))
    requests.post(balance_url, None)


def send_number_of_pieces(order):
    nop_url = str(base_url_payment + "pieces_id")
    nop_data = {"order_id": order.id,
                "client_id": order.client_id,
                "number_of_pieces": order.number_of_pieces}
    requests.post(nop_url, json=nop_data)


def update_delivery_status(order_id, status):
    status_url = str(base_url_delivery + "update-delivery-status/{}".format(order_id))
    status_data = {"status": status}
    requests.post(status_url, json=status_data)


def delete_pieces(order):
    delete_url = str(base_url_machine + "delete_pieces")
    delete_data = {"order_id": order.id}
    requests.post(delete_url, json=delete_data)
