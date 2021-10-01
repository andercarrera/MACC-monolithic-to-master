from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import BadRequest, UnsupportedMediaType, NotFound

from .model_client import Client
from .. import Session


# Client Routes #########################################################################################################
@app.route('/client', methods=['POST'])
def create_client():
    session = Session()
    new_client = None
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    try:
        new_client = Client(
            email=content['email'],
            status=Client.STATUS_CREATED
        )
        session.add(new_client)
        session.commit()
    except KeyError:
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(new_client.as_dict())
    session.close()
    return response

@app.route('/clients', methods=['GET'])
def view_clients():
    session = Session()
    print("GET All Clients.")
    clients = session.query(Client).all()
    response = jsonify(Client.list_as_dict(clients))
    session.close()
    return response

@app.route('/client/<int:client_id>', methods=['GET'])
def view_client(client_id):
    session = Session()
    client = session.query(Client).get(client_id)
    if not client:
        abort(NotFound.code)
    print("GET Client {}: {}".format(client_id, client))
    response = jsonify(client.as_dict())
    session.close()
    return response
