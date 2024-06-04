from flask import Blueprint, request
from flask_restful import Api, Resource, abort
from marshmallow import ValidationError

from anki_sync_server.anki.cloze_note import ClozeNote as ClozeNoteScheme
from anki_sync_server.server import anki

bp = Blueprint("api_v1", __name__)
api = Api(bp)


class ClozeNote(Resource):
    def post(self):
        try:
            note = ClozeNoteScheme().load(request.json)
        except ValidationError as err:
            abort(400, message=err.messages)
            return

        anki.add_cloze_note([note])

        return {"status": "ok"}


api.add_resource(ClozeNote, "/clozeNotes")
