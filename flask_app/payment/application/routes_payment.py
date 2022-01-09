from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import NotFound, BadRequest, UnsupportedMediaType, Unauthorized, ServiceUnavailable

from . import Session
from .auth import RsaSingleton
from .config_payment import Config
from .model_payment import Payment

piece_price_A = 10
piece_price_B = 5

base_url_payment = "http://{}:{}/".format(Config.PAYMENT_IP, Config.GUNICORN_PORT)


# Payment Routes #######################################################################################################


# Deletes past payments, returns money amount
def delete_payment(client_id):
    session = Session()
    payment = session.query(Payment).filter(Payment.client_id == client_id)
    if not payment:
        abort(NotFound.code, "No payment entity found with the given client id")
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

    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt)

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


def get_jwt_from_request():
    auth = request.headers.get('Authorization')
    if auth is None:
        abort(Unauthorized.code, "No JWT authorization in the request")
    jwt = auth.split(" ")[1]
    return jwt


@app.route('/payments', methods=['GET'])
def view_payments():
    session = Session()

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt_token)

    payments = session.query(Payment).all()
    response = jsonify(Payment.list_as_dict(payments))
    session.close()
    return response


# Health Check #######################################################################################################
@app.route('/payment/health', methods=['HEAD', 'GET'])
@app.route('/health', methods=['HEAD', 'GET'])
def health_check():
    public_key = RsaSingleton.get_public_key()
    if not public_key:
        abort(ServiceUnavailable.code)

    return 'OK', 200
