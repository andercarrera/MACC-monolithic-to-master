from datetime import datetime
from time import sleep

import jwt
import requests
from jwt import InvalidSignatureError
from werkzeug.exceptions import Unauthorized, abort, Forbidden

from . import Config, publisher_order

base_url_client = "http://{}:{}/".format(Config.CLIENT_IP, Config.GUNICORN_PORT)


class RsaSingleton(object):
    public_key = None

    @staticmethod
    def get_public_key():
        return RsaSingleton.public_key

    @staticmethod
    def request_public_key():
        while RsaSingleton.public_key is None:
            try:
                response = requests.get(str(base_url_client + 'client/get_public_key'), verify=False).json()
                RsaSingleton.public_key = response['public_key']
                publisher_order.publish_msg("event_exchange", "auth.certificate", "New certificate created for Order")
            except:
                print('Order waiting for public key', flush=True)
                sleep(3)

    @staticmethod
    def check_jwt_admin(jwt_token):
        try:
            payload = jwt.decode(str.encode(jwt_token), RsaSingleton.public_key, algorithms='RS256')
            # comprobar tiempo de expiración
            if payload['exp'] < datetime.timestamp(datetime.utcnow()):
                abort(Forbidden.code, "JWT Token expired")
            # comprobar rol
            if [payload['id'], 1] not in payload['roles']:
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
