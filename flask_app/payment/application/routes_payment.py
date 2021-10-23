import requests
from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import NotFound, BadRequest, UnsupportedMediaType
from .config_payment import Config
from .model_payment import Payment
from . import Session

piece_price = 10
base_url_payment = "http://{}:{}/".format(Config.PAYMENT_IP, Config.GUNICORN_PORT)


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
