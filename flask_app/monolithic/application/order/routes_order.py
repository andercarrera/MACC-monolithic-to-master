import requests
from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import NotFound, BadRequest, UnsupportedMediaType

from .model_order import Order
from .. import Session
from ..order import api_client_order


# Order Routes #########################################################################################################
@app.route('/order', methods=['POST'])
def create_order():
    session = Session()
    new_order = None
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    try:
        new_order = Order(
            description=content['description'],
            number_of_pieces=content['number_of_pieces'],
            pieces_created=0,
            status=Order.STATUS_CREATED
        )
        session.add(new_order)
        session.commit()

        api_client_order.send_pieces(new_order)
        api_client_order.create_delivery(new_order)
    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(new_order.as_dict())
    session.close()
    return response


@app.route('/piece_finished/<int:order_id>', methods=['POST'])
def changeOrderStatus(order_id):
    session = Session()
    response = ""
    try:
        order = session.query(Order).get(order_id)
        if order:
            if order.pieces_created < order.number_of_pieces:
                order.pieces_created += 1
            if order.pieces_created == order.number_of_pieces:
                order.status = order.STATUS_FINISHED
            session.commit()
            response = jsonify(order.as_dict())
    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)
    session.close()
    return response


@app.route('/order', methods=['GET'])
@app.route('/orders', methods=['GET'])
def view_orders():
    session = Session()
    print("GET All Orders.")
    orders = session.query(Order).all()
    response = jsonify(Order.list_as_dict(orders))
    session.close()
    return response


@app.route('/order/<int:order_id>', methods=['GET'])
def view_order(order_id):
    session = Session()
    order = session.query(Order).get(order_id)
    if not order:
        abort(NotFound.code)
    print("GET Order {}: {}".format(order_id, order))
    response = jsonify(order.as_dict())
    session.close()
    return response


@app.route('/order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    session = Session()
    order = session.query(Order).get(order_id)
    if not order:
        session.close()
        abort(NotFound.code)
    print("DELETE Order {}.".format(order_id))
    api_client_order.delete_order(order)
    session.delete(order)
    session.commit()
    response = jsonify(order.as_dict())
    session.close()
    return response
