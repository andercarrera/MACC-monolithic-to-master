import json
from datetime import datetime
from time import sleep

import jwt
import requests
from jwt import InvalidSignatureError
from werkzeug.exceptions import abort, Unauthorized, Forbidden

from . import Config, BLConsul


class RsaSingleton(object):
    public_key = None

    @staticmethod
    def get_public_key():
        return RsaSingleton.public_key

    @staticmethod
    def request_public_key():
        while RsaSingleton.public_key is None:
            ret_message, status_code = external_service_response("client", "get_public_key")
            if status_code == 200:
                json_tree = json.loads(ret_message)
                resp = json.loads(json_tree["response"])
                RsaSingleton.public_key = resp["public_key"]
            else:
                print('Payment waiting for public key', flush=True)
                sleep(3)

    @staticmethod
    def check_jwt_admin(jwt_token):
        try:
            payload = jwt.decode(str.encode(jwt_token), RsaSingleton.public_key, algorithms='RS256')
            # comprobar tiempo de expiración
            if payload['exp'] < datetime.timestamp(datetime.utcnow()):
                abort(Forbidden.code, "JWT Token expired")
            # comprobar rol
            if [payload['sub'], 1] not in payload['roles']:
                abort(Forbidden.code, "Resource only allowed to 'admin' users")
        except InvalidSignatureError:
            abort(Unauthorized.code, "JWT signature verification failed")

    @staticmethod
    def check_jwt_any_role(jwt_token):
        try:
            payload = jwt.decode(str.encode(jwt_token), RsaSingleton.public_key, algorithms='RS256')
            # comprobar tiempo de expiración
            if payload['exp'] < datetime.timestamp(datetime.utcnow()):
                abort(Forbidden.code, "JWT Token expired")
        except InvalidSignatureError:
            abort(Unauthorized.code, "JWT signature verification failed")


# Consul external ####################################################################################################
def external_service_response(external_service_name, path):
    service = BLConsul.get_instance().get_service(external_service_name)
    service['Name'] = external_service_name
    if service['Address'] is None or service['Port'] is None:
        ret_message = "The service does not exist or there is no healthy replica"
        status_code = 404
    else:
        service['Path'] = path
        ret_message, status_code = call_external_service(service)
    return ret_message, status_code


def call_external_service(service):
    config = Config.get_instance()
    url = "http://{host}:{port}/{service}/{path}".format(
        host=service['Address'],
        port=service['Port'],
        service=service['Name'],
        path=service['Path']
    )
    response = requests.get(url)
    if response:
        ret_message = json.dumps({
            "caller": config.SERVICE_NAME,
            "callerURL": "{}:{}".format(config.IP, config.PORT),
            "answerer": service['Name'],
            "answererURL": "{}:{}".format(service['Address'], service['Port']),
            "response": response.text,
            "status_code": response.status_code
        })
        status_code = response.status_code
    else:
        ret_message = "Could not get message"
        status_code = 500
    return ret_message, status_code
