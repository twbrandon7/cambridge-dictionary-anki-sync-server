from datetime import timedelta

import bcrypt
from flask import Blueprint, jsonify, make_response, request
from flask_restful import Api, Resource, abort
from marshmallow import ValidationError

from anki_sync_server.anki.cloze_note import ClozeNote as ClozeNoteScheme
from anki_sync_server.server import anki
from anki_sync_server.server.authentication import token_required
from anki_sync_server.server.token_issuer import TokenIssuer
from anki_sync_server.setup.credential_storage import CredentialStorage

bp = Blueprint("api_v1", __name__)
api = Api(bp)


class ClozeNote(Resource):
    @token_required
    def post(self):
        try:
            note = ClozeNoteScheme().load(request.json)
        except ValidationError as err:
            abort(400, message=err.messages)
            return

        anki.add_cloze_note([note])

        return {"status": "ok"}


api.add_resource(ClozeNote, "/clozeNotes")


# user login route
@bp.route("/login", methods=["POST"])
def login():
    auth = request.get_json()
    if not auth or not auth.get("key"):
        return make_response(
            jsonify({"message": "Could not verify!"}),
            401,
            {"WWW-Authenticate": 'Basic-realm= "Login required!"'},
        )

    hashed_api_key = CredentialStorage().get_hashed_api_key()
    if not bcrypt.checkpw(auth["key"].encode(), hashed_api_key):
        return make_response(
            jsonify({"message": "Could not verify API key!"}),
            403,
            {"WWW-Authenticate": 'Basic-realm= "No user found!"'},
        )

    token_issuer = TokenIssuer(CredentialStorage().get_server_secret_key())
    access_token = token_issuer.issue("access", timedelta(hours=1))
    refresh_token = token_issuer.issue("refresh", timedelta(days=180))
    return make_response(
        jsonify(
            {
                "accessToken": access_token,
                "refreshToken": refresh_token,
            }
        ),
        201,
    )


@bp.route("/refresh", methods=["POST"])
def refresh_token():
    auth = request.get_json()
    if not auth or not auth.get("refreshToken"):
        return make_response(
            jsonify({"message": "Could not verify!"}),
            401,
            {"WWW-Authenticate": 'Basic-realm= "Login required!"'},
        )

    token_issuer = TokenIssuer(CredentialStorage().get_server_secret_key())
    is_valid, error = token_issuer.verify(auth["refreshToken"], "refresh")
    if not is_valid:
        return make_response(
            jsonify({"message": error}),
            403,
            {"WWW-Authenticate": 'Basic-realm= "No user found!"'},
        )

    access_token = token_issuer.issue("access", timedelta(hours=1))
    refresh_token = token_issuer.issue("refresh", timedelta(days=180))
    return make_response(
        jsonify(
            {
                "accessToken": access_token,
                "refreshToken": refresh_token,
            }
        ),
        201,
    )
