import json

from flask import current_app as app
from flask import request, jsonify, abort
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import NotFound, BadRequest, UnsupportedMediaType, Unauthorized, ServiceUnavailable

from . import Session
from . import publisher_order
from .auth import RsaSingleton
from .model_order import Order, Saga, PieceType
from .publisher_order import publish_msg
# Order Routes #########################################################################################################
from .sagas_cancel_order import CancelOrderState
from .sagas_create_order import CreateOrderState
from .state_machine import get_coordinator


@app.route('/order', methods=['POST'])
def create_order():
    session = Session()
    new_order = None
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json

    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt)

    catalog_pieces = session.query(PieceType.type).all()

    matching_pieces = [s for s in content.keys() if "number_of_pieces" in s]

    if len(catalog_pieces) != len(matching_pieces) or \
            "number_of_pieces_A" not in content.keys() or \
            "number_of_pieces_B" not in content.keys():
        abort(BadRequest.code, str("Only allowing number_of_pieces_A and number_of_pieces_B"))

    try:
        new_order = Order(
            description=content['description'],
            client_id=content['client_id'],
            number_of_pieces_A=content['number_of_pieces_A'],
            number_of_pieces_B=content['number_of_pieces_B'],
            status=Order.STATUS_WAITING_FOR_PAYMENT
        )
        session.add(new_order)
        session.commit()

        zip = content['zip']
        address = content['address']

        datos = {"number_of_pieces_A": new_order.number_of_pieces_A,
                 "number_of_pieces_B": new_order.number_of_pieces_B,
                 "client_id": new_order.client_id,
                 "order_id": new_order.id,
                 "zip": zip,
                 "address": address}

        coordinator = get_coordinator()
        order_state = CreateOrderState(datos['order_id'], datos['client_id'], datos['number_of_pieces_A'],
                                       datos['number_of_pieces_B'])
        coordinator.order_state_list.append(order_state)

        print("\ndatos: {}\njson datos: {} \n".format(datos, json.dumps(datos)))
        publish_msg("sagas_commands", "payment.reserved", json.dumps(datos))
    except KeyError as e:
        session.rollback()
        session.close()
        abort(BadRequest.code, e)
    response = jsonify(new_order.as_dict())
    session.close()
    return response


def get_jwt_from_request():
    auth = request.headers.get('Authorization')
    if auth is None:
        abort(Unauthorized.code, "No JWT authorization in the request")
    jwt = auth.split(" ")[1]
    return jwt


@app.route('/order', methods=['GET'])
@app.route('/orders', methods=['GET'])
def view_orders():
    session = Session()

    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt)

    orders = session.query(Order).all()
    response = jsonify(Order.list_as_dict(orders))
    session.close()
    return response


@app.route('/order/<int:order_id>', methods=['GET'])
def view_order(order_id):
    session = Session()

    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt)

    order = session.query(Order).get(order_id)
    if not order:
        abort(NotFound.code, "Given order id not found in the Database")
    response = jsonify(order.as_dict())
    session.close()
    return response


@app.route('/order/deliver/<int:order_id>', methods=['POST'])
def deliver_order(order_id):
    session = Session()

    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_admin(jwt)

    response = None
    try:
        order = session.query(Order).get(order_id)
        order.status = Order.STATUS_DELIVERED
        session.commit()
        response = jsonify(order.as_dict())
    except NoResultFound:
        abort(NotFound.code, "Order not found for given order id")
    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)

    publisher_order.publish_msg("event_exchange", "delivery.delivered", str(order_id))
    session.close()
    return response


@app.route('/order/cancel/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    session = Session()

    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_admin(jwt)

    response = None
    try:
        order = session.query(Order).get(order_id)
        if not order:
            abort(NotFound.code, "Order not found for given order id")
        if order.status == Order.STATUS_CANCELLED:
            abort(BadRequest.code, "Order already cancelled")
        if order.status == Order.STATUS_PREPARING:
            abort(BadRequest.code, "Order still in process, can't be cancelled")
        if order.status == Order.STATUS_DELIVERED:
            abort(BadRequest.code, "Order already delivered, can't be cancelled")
        if order.status == Order.STATUS_ACCEPTED:
            coordinator = get_coordinator()
            order_state = CancelOrderState(order_id)
            coordinator.order_state_list.append(order_state)

            content = {"order_id": order_id,
                       "client_id": order.client_id,
                       "number_of_pieces_A": order.number_of_pieces_A,
                       "number_of_pieces_B": order.number_of_pieces_B,
                       "type": 'DELIVERY',
                       }
            publish_msg("sagas_response_exchange", "sagas_process.cancel_order", json.dumps(content))

            response = "The order {} was successfully cancelled".format(order.id), 200
    except NoResultFound:
        abort(NotFound.code, "Order not found for given order id")
    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)

    session.close()
    return response


# Health Check #######################################################################################################
@app.route('/order/catalog', methods=['GET'])
def view_catalog():
    session = Session()

    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt)

    orders = session.query(PieceType).all()
    response = jsonify(PieceType.list_as_dict(orders))
    session.close()
    return response


# Health Check #######################################################################################################
@app.route('/order/health', methods=['HEAD', 'GET'])
@app.route('/health', methods=['HEAD', 'GET'])
def health_check():
    public_key = RsaSingleton.get_public_key()
    if not public_key:
        abort(ServiceUnavailable.code)

    return 'OK', 200


# Sagas ##################################################################################################
@app.route('/order/saga', methods=['GET'])
@app.route('/order/sagas', methods=['GET'])
def view_sagas():
    session = Session()

    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt)

    sagas = session.query(Saga).all()
    response = jsonify(Saga.list_as_dict(sagas))
    session.close()
    return response
