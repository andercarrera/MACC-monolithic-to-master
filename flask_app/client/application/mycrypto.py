from datetime import datetime

import jwt
from Crypto.PublicKey import RSA
from jwt import InvalidSignatureError
from werkzeug.exceptions import Forbidden, abort, Unauthorized

key = RSA.generate(2048)
private_key = key.export_key()
public_key = key.publickey().export_key()


class RsaSingleton(object):
    @staticmethod
    def get_public_key():
        return public_key

    @staticmethod
    def get_private_key():
        return private_key

    @staticmethod
    def check_jwt_any_role(jwt_token):
        try:
            payload = jwt.decode(str.encode(jwt_token), public_key, algorithms='RS256')
            # comprobar tiempo de expiración
            if payload['exp'] < datetime.timestamp(datetime.utcnow()):
                abort(Forbidden.code, "JWT Token expired")
        except InvalidSignatureError:
            abort(Unauthorized.code, "JWT signature verification failed")

    @staticmethod
    def check_jwt_admin(jwt_token):
        try:
            payload = jwt.decode(str.encode(jwt_token), public_key, algorithms='RS256')
            # comprobar tiempo de expiración
            if payload['exp'] < datetime.timestamp(datetime.utcnow()):
                abort(Forbidden.code, "JWT Token expired")
            # comprobar rol
            if [payload['sub'], 1] not in payload['roles']:
                abort(Forbidden.code, "Resource only allowed to 'admin' users")
        except InvalidSignatureError:
            abort(Unauthorized.code, "JWT signature verification failed")
