import datetime
import secrets
import traceback

import bcrypt
import jwt
from flask import current_app as app
from flask import request, jsonify, abort
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import NotFound, InternalServerError, BadRequest, UnsupportedMediaType, Unauthorized, \
    ServiceUnavailable

from . import Session, log
from .model_client import Client, Role, client_role_table
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

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_admin(jwt_token)

    try:
        new_client = Client(
            email=content['email'],
            status=Client.STATUS_CREATED,
            username=content['username'],
            password=bcrypt.hashpw(content['password'].encode(), bcrypt.gensalt()).decode('utf-8'),
        )
        role = session.query(Role).filter_by(id=content['role_id']).one()

        new_client.roles.append(role)

        session.add(new_client)
        session.commit()
    except NoResultFound:
        abort(NotFound.code, "Given role_id not found")
    except KeyError as e:
        log.create_log(e, 'error')
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(new_client.as_dict())
    session.close()
    return response


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


@app.route('/client/<client_id>', methods=['PUT'])
def update_client(client_id):
    session = Session()
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_admin(jwt_token)

    client = session.query(Client).get(client_id)
    if not client:
        abort(NotFound.code, "Given user id not found in the Database")

    try:
        client.email = content['email']
        client.username = content['username']
        client.password = bcrypt.hashpw(content['password'].encode(), bcrypt.gensalt()).decode('utf-8')

        session.commit()
    except NoResultFound:
        abort(NotFound.code, "Given user_id not found")
    except KeyError as e:
        log.create_log(e, 'error')
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(client.as_dict())
    session.close()
    return response


@app.route('/client/<client_id>', methods=['DELETE'])
def delete_client(client_id):
    session = Session()

    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_admin(jwt)

    client = session.query(Client).get(client_id)
    if not client:
        abort(NotFound.code, "Role not found for given order id")

    session.delete(client)
    session.commit()
    response = jsonify(client.as_dict())
    session.close()
    return response


# JWT Routes
# #########################################################################################################

@app.route('/client/create_jwt', methods=['GET'])
def create_jwt():
    session = Session()
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    auth = request.authorization
    response = None
    try:
        roles = session.query(client_role_table).filter_by(client_id=auth['username']).all()
        user = session.query(Client).filter(Client.id == auth['username']).one()

        if not bcrypt.checkpw(auth['password'].encode('utf-8'), user.password.encode('utf-8')):
            raise Exception
        payload = {
            'sub': user.id,
            'roles': roles,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        refresh_token = secrets.token_urlsafe(32)

        response = {
            'jwt_token': jwt.encode(payload, RsaSingleton.get_private_key(), algorithm='RS256'),
            'refresh_token': refresh_token
        }

        user.refresh_token = refresh_token
        session.commit()
    except NoResultFound:
        abort(NotFound.code, "Given user id not found in the Database")
    except KeyError as e:
        log.create_log(e, 'error')
        session.rollback()
        session.close()
        abort(BadRequest.code)
    except Exception as e:
        print(e, flush=True)
        session.rollback()
        session.close()
        abort(Unauthorized.code, "Invalid password")

    session.close()
    return response


@app.route('/client/refresh_jwt', methods=['GET'])
def refresh_jwt():
    session = Session()
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    response = None
    try:
        refresh_token = get_jwt_from_request()
        user = session.query(Client).filter(Client.refresh_token == refresh_token).one()
        roles = session.query(client_role_table).filter_by(client_id=user.id).all()

        payload = {
            'sub': user.id,
            'roles': roles,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        response = {
            'jwt_token': jwt.encode(payload, RsaSingleton.get_private_key(), algorithm='RS256'),
        }
    except NoResultFound:
        abort(NotFound.code, "No user found with the given refresh token")

    session.close()
    return response


@app.route('/client/get_public_key', methods=['GET'])
def get_public_key():
    content = {'public_key': RsaSingleton.get_public_key().decode()}
    return content


def get_jwt_from_request():
    auth = request.headers.get('Authorization')
    if auth is None:
        abort(Unauthorized.code, "No JWT authorization in the request")
    jwt_token = auth.split(" ")[1]
    return jwt_token


# Role Routes
# #########################################################################################################
@app.route('/client/role', methods=['GET'])
def view_roles():
    session = Session()

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt_token)

    roles = session.query(Role).all()
    response = jsonify(Role.list_as_dict(roles))
    session.close()
    return response


@app.route('/client/role', methods=['POST'])
def creat_role():
    session = Session()
    new_role = None
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_admin(jwt_token)

    try:
        new_role = Role(
            name=content['name']
        )
        session.add(new_role)
        session.commit()
    except KeyError as e:
        log.create_log(e, 'error')
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(new_role.as_dict())
    session.close()
    return response


@app.route('/client/role/<role_id>', methods=['PUT'])
def update_role(role_id):
    session = Session()
    if request.headers['Content-Type'] != 'application/json':
        abort(UnsupportedMediaType.code)
    content = request.json

    jwt_token = get_jwt_from_request()
    RsaSingleton.check_jwt_admin(jwt_token)

    role = session.query(Role).get(role_id)
    if not role:
        abort(NotFound.code, "Given role id not found in the Database")

    try:
        role.name = content['name']
        session.commit()
    except KeyError as e:
        log.create_log(e, 'error')
        session.rollback()
        session.close()
        abort(BadRequest.code)
    response = jsonify(role.as_dict())
    session.close()
    return response


@app.route('/client/role/<role_id>', methods=['DELETE'])
def delete_role(role_id):
    session = Session()

    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_admin(jwt)

    role = session.query(Role).get(role_id)
    if not role:
        abort(NotFound.code, "Role not found for given order id")

    session.delete(role)
    session.commit()
    response = jsonify(role.as_dict())
    session.close()
    return response


# Health Check #######################################################################################################
@app.route('/client/health', methods=['HEAD', 'GET'])
@app.route('/health', methods=['HEAD', 'GET'])
def health_check():
    public_key = RsaSingleton.get_public_key()
    if not public_key:
        abort(ServiceUnavailable.code)

    return 'Client 2 OK', 200


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
