from flask import jsonify
from ..payment import routes_payment
import requests


def hm_pieces(order_id):
    url = "http://localhost:13000/npieces/{}".format(order_id)
    response = requests.post(url)


def order_accepted(order_id, payed):
    if payed:
        payment_status = "Accepted"
    else:
        payment_status = "Denied"

    url = "http://localhost:13000/payment_status"
    datos = {"order_id": order_id,
             "payment_status": payment_status}
    response = requests.post(url, json=datos)
