from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import NotFound, BadRequest, UnsupportedMediaType

from . import Session
from .auth import RsaSingleton
from .model_delivery import Delivery

my_delivery = Delivery()


def init_req():
    session = Session()
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    return content, session


# Delivery Routes
# #########################################################################################################
@app.route('/delivery', methods=['POST'])
def create_delivery():
    content, session = init_req()
    new_delivery = None
    try:
        order_id = content['order_id']
        new_delivery = Delivery(
            order_id=order_id,
            status=Delivery.STATUS_PREPARING
        )
        session.add(new_delivery)
        session.commit()
    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(new_delivery.as_dict())
    session.close()
    return response


@app.route('/delivery/confirm/<int:order_id>', methods=['POST'])
def update_delivery_address(order_id):
    content, session = init_req()
    delivery = session.query(Delivery).filter_by(order_id=order_id).first()
    if delivery is None:
        abort(NotFound.code)

    RsaSingleton.check_jwt(content['jwt'])
    try:
        new_address = content['address']
        delivery.address = new_address
        session.commit()
        delivery.status = "delivered"
        session.commit()
    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(delivery.as_dict())
    session.close()
    return response
