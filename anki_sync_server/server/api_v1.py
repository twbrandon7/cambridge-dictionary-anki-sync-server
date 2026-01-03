from datetime import datetime, timedelta, timezone

import bcrypt
from flask import Blueprint, jsonify, make_response, request
from flask_restful import Api, Resource, abort
from marshmallow import ValidationError

from anki_sync_server.anki.cloze_note import ClozeNote as ClozeNoteScheme
from anki_sync_server.server import anki
from anki_sync_server.server.authentication import token_required
from anki_sync_server.server.task_status import TaskStatus
from anki_sync_server.server.token_issuer import TokenIssuer
from anki_sync_server.setup.credential_storage import CredentialStorage
from anki_sync_server.tasks.card_creation_task import add_cloze_note_task

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

        # Check if synchronous mode is requested
        async_mode = request.args.get("async", "true").lower() == "true"

        if not async_mode:
            # Legacy synchronous mode
            anki.add_cloze_note([note])
            return {"status": "ok"}

        # Asynchronous mode: queue task and return task ID
        task = add_cloze_note_task.delay(ClozeNoteScheme().dump(note))

        return {
            "taskId": task.id,
            "status": "pending",
            "statusUrl": f"/api/v1/tasks/{task.id}",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }, 202


api.add_resource(ClozeNote, "/clozeNotes")


class TaskStatusResource(Resource):
    @token_required
    def get(self, task_id):
        """Get status of an async task."""
        task_status = TaskStatus.get_task_status(task_id)

        if task_status is None:
            abort(404, message=f"Task {task_id} not found")

        return task_status


api.add_resource(TaskStatusResource, "/tasks/<task_id>")


@bp.route("/health", methods=["GET"])
@token_required
def health():
    return make_response(jsonify({"status": "ok"}), 200)


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
