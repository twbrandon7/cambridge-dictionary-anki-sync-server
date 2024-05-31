import os

from anki.collection import Collection
from anki.models import NoteType

from anki_sync_server import ASSET_PATH
from anki_sync_server.anki.fields_injector import FieldsInjector
from anki_sync_server.anki.template_injector import TemplateInjector


class ModelCreator:
    MODEL_NAME = "Custom Cloze"

    def __init__(self, collection: Collection):
        self._collection = collection
        self._template_injector = TemplateInjector(collection)
        self._fields_injector = FieldsInjector(collection)

    def create_model(self, name: str = MODEL_NAME) -> NoteType:
        if self._is_model_exists():
            return self._collection.models.by_name(name)
        model = self._get_new_model()
        self._collection.models.save(model)
        return self._collection.models.by_name(name)

    def _is_model_exists(self) -> bool:
        return self._collection.models.by_name(self.MODEL_NAME) is not None

    def _get_new_model(self) -> NoteType:
        with open(os.path.join(ASSET_PATH, "template", "styling.css"), "r") as file:
            css = file.read()

        with open(os.path.join(ASSET_PATH, "template", "pre.tex"), "r") as file:
            latex_pre = file.read()

        with open(os.path.join(ASSET_PATH, "template", "post.tex"), "r") as file:
            latex_post = file.read()

        model = self._collection.models.new(self.MODEL_NAME)
        model.update(
            {
                "type": 1,
                "usn": 0,
                "sortf": 0,
                "did": None,
                "tmpls": [],
                "flds": [],
                "css": css,
                "latexPre": latex_pre,
                "latexPost": latex_post,
                "latexsvg": False,
            }
        )
        self._template_injector.inject(model)
        self._fields_injector.inject(model)
        return model
