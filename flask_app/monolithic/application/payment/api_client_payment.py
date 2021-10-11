from flask import jsonify
from ..payment import routes_payment
import requests

base_url_order = "http://localhost:13003/"


def hm_pieces(order_id):
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
