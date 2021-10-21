import requests
from .config_payment import Config

base_url_order = "http://{}:{}/".format(Config.ORDER_IP, Config.GUNICORN_PORT)


def how_many_pieces(order_id):
    url = "{}npieces/{}".format(base_url_order, order_id)
    requests.post(url, None)


def order_accepted(order_id, payed):
    if payed:
        payment_status = "Accepted"
    else:
        payment_status = "Denied"

    url = "{}payment_status".format(base_url_order)
    datos = {"order_id": order_id,
             "payment_status": payment_status}
    requests.post(url, json=datos)
