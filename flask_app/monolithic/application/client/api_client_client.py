from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import NotFound

from .model_client import Client
from .. import Session

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
