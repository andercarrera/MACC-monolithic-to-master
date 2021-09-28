from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from .machine import Machine
from .model_machine import Piece
from .. import Session

my_machine = Machine()


# Piece routes #########################################################################################################
@app.route('/pieces', methods=['POST'])
def create_piece():
    session = Session()
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    piece = None
    pieces = []
    try:
        number_of_pieces = content['number_of_pieces']
        order_id = content['order_id']
        for i in range(number_of_pieces):
            piece = Piece()
            piece.order_id = order_id
            pieces.append(piece)
            session.add(piece)
        session.commit()
        my_machine.add_pieces_to_queue(pieces)
        session.commit()
    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(piece.as_dict())
    session.close()
    return response


@app.route('/delete_pieces', methods=['POST'])
def delete_pieces():
    session = Session()
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    try:
        order_id = content['order_id']
        pieces = session.query(Piece).filter_by(order_id=order_id).all()
        my_machine.remove_pieces_from_queue(pieces)
        # session.delete(pieces)
        session.commit()

    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = "Piezas eliminadas"
    session.close()
    return response
