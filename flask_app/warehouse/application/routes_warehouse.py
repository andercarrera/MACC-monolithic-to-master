import json

from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import NotFound, Unauthorized, ServiceUnavailable, UnsupportedMediaType, BadRequest

from . import Session
from .auth import RsaSingleton
from .model_warehouse import Piece, Order
# Order Routes #####################################################################################################
from .publisher_warehouse import publish_msg


@app.route('/warehouse', methods=['POST'])
def forward_production():
    session = Session()
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json

    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt)

    try:
        publish_msg("event_exchange", "warehouse.forward", json.dumps(content))
    except KeyError as e:
        session.rollback()
        session.close()
        abort(BadRequest.code, e)
    session.close()
    return 'OK', 200


@app.route('/warehouse/order', methods=['GET'])
@app.route('/warehouse/orders', methods=['GET'])
def view_orders():
    session = Session()

    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt)

    orders = session.query(Order).all()
    response = jsonify(Order.list_as_dict(orders))
    session.close()
    return response


@app.route('/warehouse/order/<int:order_id>', methods=['GET'])
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


# Pieces Routes #####################################################################################################

def get_jwt_from_request():
    auth = request.headers.get('Authorization')
    if auth is None:
        abort(Unauthorized.code, "No JWT authorization in the request")
    jwt = auth.split(" ")[1]
    return jwt


@app.route('/warehouse/piece', methods=['GET'])
@app.route('/warehouse/pieces', methods=['GET'])
def view_pieces():
    session = Session()

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt_token)

    order_id = request.args.get('order_id')
    if order_id:
        pieces = session.query(Piece).filter_by(order_id=order_id).all()
    else:
        pieces = session.query(Piece).all()
    response = jsonify(Piece.list_as_dict(pieces))
    session.close()
    return response


@app.route('/warehouse/piece/<int:piece_id>', methods=['GET'])
def view_piece(piece_id):
    session = Session()

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt_token)

    piece = session.query(Piece).get(piece_id)
    if not piece:
        abort(NotFound.code, "Given piece id not found in the database")
    response = jsonify(piece.as_dict())
    session.close()
    return response


# Health Check #######################################################################################################
@app.route('/warehouse/health', methods=['HEAD', 'GET'])
@app.route('/health', methods=['HEAD', 'GET'])
def health_check():
    public_key = RsaSingleton.get_public_key()
    if not public_key:
        abort(ServiceUnavailable.code)

    return 'OK', 200
