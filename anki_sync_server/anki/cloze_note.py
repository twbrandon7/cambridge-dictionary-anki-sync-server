from marshmallow import Schema, fields


class ClozeNote(Schema):
    word = fields.Str(required=True)
    partOfSpeech = fields.Str(required=True)
    guideWord = fields.Str(required=True)
    englishDefinition = fields.Str(required=True)
    definitionTranslation = fields.Str(required=True)
    cefrLevel = fields.Str(required=True)
    code = fields.Str(required=True)
    englishExample = fields.Str(required=True)
    exampleTranslation = fields.Str(required=True)
