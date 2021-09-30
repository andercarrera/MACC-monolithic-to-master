import requests
from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from .model_order import Order
from .. import Session

base_url = "http://localhost:13000/"


def create_delivery(new_order):
    delivery_url = str(base_url + "delivery")
    delivery_data = {"order_id": new_order.id}
    requests.post(delivery_url, json=delivery_data)


def add_pieces(new_order):
    pieces_url = str(base_url + "pieces")
    pieces_data = {"number_of_pieces": new_order.number_of_pieces,
                   "order_id": new_order.id}
    requests.post(pieces_url, json=pieces_data)


@app.route('/order_status', methods=['POST'])
def changeOrderStatus():
    session = Session()
    order = None
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    try:
        order_status = content['order_status']
        order_id = content['order_id']
        order = session.query(Order).get(order_id)
        order.status = order_status
        session.commit()
    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(order.as_dict())
    session.close()
    return response
