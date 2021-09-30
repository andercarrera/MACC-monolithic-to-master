from flask import jsonify
from .routes_payment import view_usr_payment
import requests

piece_price = 10

def hm_pieces(order_id):

    #post preguntando piezas y user id
    order_user_id = 0
    npieces = 0


    order_cost = npieces * piece_price
    usr_balance = view_usr_payment(order_user_id)
    response = jsonify("Not enough balance")
    if order_cost > usr_balance:
        """notify order that user has not enough credit """
    else:
        new_balance = usr_balance - order_cost
        url = "http://localhost:13000/payment"
        datos = {"description": "Order payment",
                 "payment_amount": new_balance,
                 "usr_id": order_user_id}
        response = requests.post(url, json=datos)
        """Notify order that the payment was done correctly"""

    return response