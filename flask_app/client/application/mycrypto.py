from datetime import datetime

import jwt
from Crypto.PublicKey import RSA
from jwt import InvalidSignatureError
from werkzeug.exceptions import Forbidden, abort, Unauthorized

with open('/app/application/private_key.pem', 'rb') as private_file:
    private_key = RSA.importKey(private_file.read(), 'group3').exportKey()

with open('/app/application/public_key.pem', 'rb') as public_file:
    public_key = RSA.importKey(public_file.read()).exportKey()


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
