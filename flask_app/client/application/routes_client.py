import datetime
import traceback

import bcrypt
import jwt
from flask import current_app as app
from flask import request, jsonify, abort
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import NotFound, InternalServerError, BadRequest, UnsupportedMediaType, Unauthorized

from . import Session
from .model_client import Client
from .mycrypto import RsaSingleton


# Client Routes
# #########################################################################################################
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
            status=Client.STATUS_CREATED,
            username=content['username'],
            password=bcrypt.hashpw(content['password'].encode(), bcrypt.gensalt()).decode('utf-8'),
            role=content['role']
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


@app.route('/client/create_jwt', methods=['GET'])
def create_jwt():
    session = Session()
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json
    response = None
    try:
        user = session.query(Client).filter(Client.id == content['id']).one()
        if not bcrypt.checkpw(content['password'].encode('utf-8'), user.password.encode('utf-8')):
            raise Exception
        payload = {
            'id': user.id,
            'username': user.username,
            'service': False,
            'role': user.role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        response = {
            'jwt': jwt.encode(payload, RsaSingleton.get_private_key(), algorithm='RS256')
        }

    except NoResultFound:
        abort(NotFound.code, "Given user id not found in the Database")
    except Exception as e:
        print(e, flush=True)
        session.rollback()
        session.close()
        abort(BadRequest.code)

    session.close()
    return response


@app.route('/auth/get_public_key', methods=['GET'])
def get_public_key():
    content = {'public_key': RsaSingleton.get_public_key().decode()}
    return content


@app.route('/clients', methods=['GET'])
def view_clients():
    session = Session()

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt_token)

    clients = session.query(Client).all()
    response = jsonify(Client.list_as_dict(clients))
    session.close()
    return response


@app.route('/client/<int:client_id>', methods=['GET'])
def view_client(client_id):
    session = Session()

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt_token)

    client = session.query(Client).get(client_id)
    if not client:
        abort(NotFound.code, "Given user id not found in the Database")
    response = jsonify(client.as_dict())
    session.close()
    return response


def get_jwt_from_request():
    auth = request.headers.get('Authorization')
    if auth is None:
        abort(Unauthorized.code, "No JWT authorization in the request")
    jwt_token = auth.split(" ")[1]
    return jwt_token


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
