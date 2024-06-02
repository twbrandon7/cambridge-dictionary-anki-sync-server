from flask import Blueprint, request
from flask_restful import Api, Resource, abort
from marshmallow import Schema, ValidationError, fields

from anki_sync_server.server import anki

bp = Blueprint("api_v1", __name__)
api = Api(bp)


class ClozeNote(Resource, Schema):
    word = fields.Str(required=True)
    partOfSpeech = fields.Str(required=True)
    guideWord = fields.Str(required=True)
    englishDefinition = fields.Str(required=True)
    definitionTranslation = fields.Str(required=True)
    cefrLevel = fields.Str(required=True)
    code = fields.Str(required=True)
    englishExample = fields.Str(required=True)
    exampleTranslation = fields.Str(required=True)

    def post(self):
        try:
            note = ClozeNote().load(request.json)
        except ValidationError as err:
            abort(400, message=err.messages)
            return

        anki.add_cloze_note(
            text=note["englishExample"],
            text_translation=note["exampleTranslation"],
            english_definition=note["englishDefinition"],
            definition_translation=note["definitionTranslation"],
            word=note["word"],
            part_of_speech=note["partOfSpeech"],
            cefr_level=note["cefrLevel"],
            code=note["code"],
        )

        return {"status": "ok"}


api.add_resource(ClozeNote, "/clozeNotes")
