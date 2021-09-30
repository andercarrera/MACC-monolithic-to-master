from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import BadRequest, UnsupportedMediaType

from .model_delivery import Delivery
from .. import Session

my_delivery = Delivery()


# Delivery Routes
# #########################################################################################################
@app.route('/delivery', methods=['POST'])
def create_delivery():
    session = Session()
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
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
