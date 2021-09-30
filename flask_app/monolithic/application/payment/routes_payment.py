from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import NotFound, BadRequest, UnsupportedMediaType

from .api_client_payment import hm_pieces
from .model_payment import Payment
from .. import Session



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
            usr_id=content['usr_id']
        )
        new_payment.payment_amount += delete_payment(new_payment.usr_id)
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


def view_usr_payment(usr_id):
    session = Session()
    payment = session.query(Payment).filter(Payment.usr_id == usr_id)
    response = payment.payment_amount
    session.close()
    return response


#Deletes past payments, returns money amount
def delete_payment(usr_id):
    session = Session()
    payment = session.query(Payment).filter(Payment.usr_id == usr_id)
    if not payment:
        session.close()
        abort(NotFound.code)
    money = 0
    for p in payment:
        print("DELETE Order {}.".format(p.id))
        print("usr id: {} money: {}\n".format(p.usr_id, p.payment_amount))
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
