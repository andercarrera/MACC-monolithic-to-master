from flask import request, jsonify, abort
from flask import current_app as app
from .model_machine import Piece
from werkzeug.exceptions import NotFound, InternalServerError, BadRequest, UnsupportedMediaType
import traceback
from .machine import Machine
from .. import Session

my_machine = Machine()

# Piece Routes #########################################################################################################

@app.route('/piece', methods=['GET'])
@app.route('/pieces', methods=['GET'])
def view_pieces():
    session = Session()
    order_id = request.args.get('order_id')
    if order_id:
        pieces = session.query(Piece).filter_by(order_id=order_id).all()
    else:
        pieces = session.query(Piece).all()
    response = jsonify(Piece.list_as_dict(pieces))
    session.close()
    return response


@app.route('/piece/<int:piece_ref>', methods=['GET'])
def view_piece(piece_ref):
    session = Session()
    piece = session.query(Piece).get(piece_ref)
    if not piece:
        session.close()
        abort(NotFound.code)
    print(piece)
    response = jsonify(piece.as_dict())
    session.close()
    return response

# Machine Routes #######################################################################################################
@app.route('/machine/status', methods=['GET'])
def view_machine_status():
    working_piece = my_machine.working_piece
    queue = my_machine.queue
    if working_piece:
        working_piece = working_piece.as_dict()
    response = {"status": my_machine.status, "working_piece": working_piece, "queue": list(queue)}
    return jsonify(response)


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
    return jsonify({"error_code":e.code, "error_message": e.description}), e.code


