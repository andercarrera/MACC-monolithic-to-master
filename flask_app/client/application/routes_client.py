import traceback

import bcrypt
from flask import current_app as app
from flask import request, jsonify, abort
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.exceptions import NotFound, InternalServerError, BadRequest, UnsupportedMediaType, Unauthorized, \
    ServiceUnavailable

from . import Session, log
from .auth import RsaSingleton
from .model_client import Client, Role


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
