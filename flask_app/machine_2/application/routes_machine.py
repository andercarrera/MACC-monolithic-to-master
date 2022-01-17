import traceback

from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import NotFound, InternalServerError, BadRequest, UnsupportedMediaType, Unauthorized, \
    ServiceUnavailable

from . import Session
from .auth import RsaSingleton
from .model_machine import Piece


def get_jwt_from_request():
    auth = request.headers.get('Authorization')
    if auth is None:
        abort(Unauthorized.code, "No JWT authorization in the request")
    jwt = auth.split(" ")[1]
    return jwt


# Machine Routes #######################################################################################################


@app.route('/machine2/piece', methods=['GET'])
@app.route('/machine2/pieces', methods=['GET'])
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


@app.route('/machine2/piece/<int:piece_ref>', methods=['GET'])
def view_piece(piece_ref):
    session = Session()

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt_token)

    piece = session.query(Piece).get(piece_ref)
    if not piece:
        abort(NotFound.code, "Given piece id not found in the database")
    response = jsonify(piece.as_dict())
    session.close()
    return response


# Health Check #######################################################################################################
@app.route('/machine2/health', methods=['HEAD', 'GET'])
@app.route('/health', methods=['HEAD', 'GET'])
def health_check():
    public_key = RsaSingleton.get_public_key()
    if not public_key:
        abort(ServiceUnavailable.code)

    return 'OK', 200


# Error Handling #######################################################################################################
@app.errorhandler(UnsupportedMediaType)
def unsupported_media_type_handler(e):
    return get_jsonified_error(e)


@app.errorhandler(BadRequest)
def bad_request_handler(e):
    return get_jsonified_error(e)


@app.errorhandler(NotFound)
def resource_not_found_handler(e):
    return get_jsonified_error(e)


@app.errorhandler(InternalServerError)
def server_error_handler(e):
    return get_jsonified_error(e)


def get_jsonified_error(e):
    traceback.print_tb(e.__traceback__)
    return jsonify({"error_code": e.code, "error_message": e.description}), e.code
