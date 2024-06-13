"""Source: https://circleci.com/blog/authentication-decorators-flask/"""

from functools import wraps

import jwt
from flask import jsonify, make_response, request

from anki_sync_server import APP_NAME
from anki_sync_server.setup.credential_storage import CredentialStorage


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        # ensure the jwt-token is passed with the headers
        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]
        if not token:  # throw error if no token provided
            return make_response(jsonify({"message": "A valid token is missing!"}), 401)
        try:
            # decode the token to obtain user public_id
            secret_key = CredentialStorage().get_server_secret_key()
            data = jwt.decode(token, secret_key, algorithms=["HS256"])
            if APP_NAME != data["appName"] or not data["exp"]:
                return make_response(jsonify({"message": "Invalid token!"}), 401)
        except jwt.ExpiredSignatureError:
            return make_response(jsonify({"message": "Token expired!"}), 401)
        except Exception:
            return make_response(jsonify({"message": "Invalid token!"}), 401)
        # Return the user information attached to the token
        return f(*args, **kwargs)

    return decorator
