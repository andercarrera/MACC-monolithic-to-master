from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import NotFound, BadRequest, UnsupportedMediaType, Unauthorized, ServiceUnavailable

# Delivery Routes ######################################################################################################
from . import Session
from . import publisher_delivery
from .auth import RsaSingleton
from .model_delivery import Delivery

my_delivery = Delivery()


def init_req():
    session = Session()
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    return content, session


# Delivery Routes ######################################################################################################


@app.route('/delivery/confirm/<int:order_id>', methods=['POST'])
def update_delivery_address(order_id):
    content, session = init_req()

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt_token)

    delivery = session.query(Delivery).filter_by(order_id=order_id).first()
    if delivery is None:
        abort(NotFound.code)

    try:
        new_address = content['address']
        delivery.address = new_address
        session.commit()
        delivery.status = Delivery.STATUS_DELIVERED
        publisher_delivery.publish_msg("event_exchange", "delivery.delivered", str(order_id))
        session.commit()
    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(delivery.as_dict())
    session.close()
    return response


def get_jwt_from_request():
    auth = request.headers.get('Authorization')
    if auth is None:
        abort(Unauthorized.code, "No JWT authorization in the request")
    jwt = auth.split(" ")[1]
    return jwt


@app.route('/delivery', methods=['GET'])
def view_deliveries():
    session = Session()

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt_token)

    deliveries = session.query(Delivery).all()
    response = jsonify(Delivery.list_as_dict(deliveries))
    session.close()
    return response


@app.route('/delivery/<int:delivery_id>', methods=['GET'])
def view_delivery(delivery_id):
    session = Session()

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt_token)

    delivery = session.query(Delivery).get(delivery_id)
    if not delivery:
        abort(NotFound.code, "Given delivery id not found in the Database")
    response = jsonify(delivery.as_dict())
    session.close()
    return response


# Health Check #######################################################################################################
@app.route('/delivery/health', methods=['HEAD', 'GET'])
@app.route('/health', methods=['HEAD', 'GET'])
def health_check():
    public_key = RsaSingleton.get_public_key()
    if not public_key:
        abort(ServiceUnavailable.code)

    return 'OK', 200
