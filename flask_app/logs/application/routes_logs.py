from flask import current_app as app
from flask import request, jsonify, abort
from werkzeug.exceptions import Unauthorized, ServiceUnavailable

from . import Session
from .auth import RsaSingleton
from .model_logs import Log


# Delivery Routes ######################################################################################################

def get_jwt_from_request():
    auth = request.headers.get('Authorization')
    if auth is None:
        abort(Unauthorized.code, "No JWT authorization in the request")
    jwt = auth.split(" ")[1]
    return jwt


@app.route('/logs', methods=['GET'])
def get_logs():
    session = Session()
    jwt = get_jwt_from_request()
    RsaSingleton.check_jwt_any_role(jwt)

    logs = session.query(Log).all()
    print(logs, flush=True)
    response = jsonify(Log.list_as_dict(logs))
    session.close()
    return response


# Health Check #######################################################################################################
@app.route('/logs/health', methods=['HEAD', 'GET'])
@app.route('/health', methods=['HEAD', 'GET'])
def health_check():
    public_key = RsaSingleton.get_public_key()
    if not public_key:
        abort(ServiceUnavailable.code)

    return 'OK', 200
