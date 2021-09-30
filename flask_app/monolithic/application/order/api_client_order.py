from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from .model_order import Order
from .. import Session


@app.route('/order_status', methods=['POST'])
def changeOrderStatus():
    session = Session()
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    try:
        orderStatus = content['order_status']
        order_id = content['order_id']
        order = session.query(Order).get(order_id)
        order.status = orderStatus
        session.commit()
    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(order.as_dict())
    session.close()
    return response
