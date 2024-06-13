"""Source: https://circleci.com/blog/authentication-decorators-flask/"""

from functools import wraps

from flask import jsonify, make_response, request

from anki_sync_server.server.token_issuer import TokenIssuer
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
        secret_key = CredentialStorage().get_server_secret_key()
        token_issuer = TokenIssuer(secret_key)
        is_valid, error = token_issuer.verify(token, "access")
        if not is_valid:
            return make_response(jsonify({"message": error}), 401)
        return f(*args, **kwargs)

    return decorator
