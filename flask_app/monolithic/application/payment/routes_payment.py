import requests
from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import NotFound, BadRequest, UnsupportedMediaType

from .api_client_payment import hm_pieces, order_accepted
from .model_payment import Payment
from .. import Session

piece_price = 10


@app.route('/payment', methods=['POST'])
def create_payment():
    session = Session()
    new_payment = None
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    try:
        new_payment = Payment(
            description=content['description'],
            payment_amount=content['payment_amount'],
            client_id=content['client_id']
        )
        new_payment.payment_amount += delete_payment(new_payment.client_id)
        session.add(new_payment)
        session.commit()
    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(new_payment.as_dict())
    session.close()
    return response


@app.route('/payments', methods=['GET'])
def view_payments():
    session = Session()
    print("GET All Payments.")
    payments = session.query(Payment).all()
    response = jsonify(Payment.list_as_dict(payments))
    session.close()
    return response


def view_usr_payment(client_id):
    session = Session()
    payment = session.query(Payment).filter(Payment.client_id == client_id)
    response = payment.payment_amount
    session.close()
    return response


# Deletes past payments, returns money amount
def delete_payment(client_id):
    session = Session()
    payment = session.query(Payment).filter(Payment.client_id == client_id)
    if not payment:
        session.close()
        abort(NotFound.code)
    money = 0
    for p in payment:
        print("Usr id: {} money: {}\n".format(p.client_id, p.payment_amount))
        money += p.payment_amount
        session.delete(p)
        session.commit()
    session.close()
    return money


@app.route('/neworder/<int:order_id>', methods=['POST'])
def new_order(order_id):
    hm_pieces(order_id)
    response = jsonify("Order id recieved")
    return response


@app.route('/pieces_id', methods=['POST'])
def pieces_id():
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    client_id = 0
    number_of_pieces = 0
    order_id = 0
    try:
        order_id = content['order_id']
        client_id = content['client_id']
        number_of_pieces = content['number_of_pieces']
    except KeyError:
        abort(BadRequest.code)

    order_cost = number_of_pieces * piece_price
    usr_balance = view_usr_payment(client_id)
    response = jsonify("Order cancelled")
    if order_cost > usr_balance:
        order_accepted(order_id, False)
    else:
        new_balance = usr_balance - order_cost
        url = "http://localhost:13000/payment"
        datos = {"description": "Order payment",
                 "payment_amount": new_balance,
                 "client_id": client_id}
        response = requests.post(url, json=datos)
        order_accepted(order_id, True)

    return response
