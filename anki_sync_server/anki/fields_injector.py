from anki.collection import Collection
from anki.models import CardType, FieldDict


class FieldsInjector:
    TARGET_FIELDS = [
        "Text",  # Example of the vocabulary word
        "Word",  # The vocabulary word
        "TextTranslation",  # Translation of the example
        "EnDefinition",  # Definition in English
        "DefinitionTranslation",  # Translation of the definition
        "PartOfSpeech",  # Part of speech
        "CefrLevel",  # CEFR level
        "Code",  # Code of the word
        # see https://dictionary.cambridge.org/help/codes.html
        "DefinitionAudio",  # Audio of the definition
        "TextAudio",  # Audio of the example
    ]

    def __init__(self, collection: Collection):
        self._collection = collection

    def inject(self, model: CardType) -> None:
        for field in self.TARGET_FIELDS:
            if not self._field_name_exists(model, field):
                model["flds"].append(self._new_field(field))

    def _field_name_exists(self, model: CardType, field_name: str) -> bool:
        return any(field["name"] == field_name for field in model["flds"])

    def _new_field(self, name: str) -> FieldDict:
        field = self._collection.models.new_field(name)
        field.update(
            {
                "sticky": False,
                "rtl": False,
                "font": "Arial",
                "size": 20,
                "description": "",
                "plainText": False,
                "collapsed": False,
                "excludeFromSearch": False,
                "tag": None,
                "preventDeletion": False,
            }
        )
        return field
