import os
from anki.collection import Collection
from anki.models import NoteType, TemplateDict
from anki_sync_server import ASSET_PATH


class TemplateInjector:
    TEMPLATE_NAME = "Custom Cloze"

    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def inject(self, model: NoteType) -> None:
        for template in model["tmpls"]:
            if template["name"] == TemplateInjector.TEMPLATE_NAME:
                return

        template = self._load_template()
        self._collection.models.add_template(model, template)

    def _load_template(self) -> TemplateDict:
        template = self._collection.models.new_template(TemplateInjector.TEMPLATE_NAME)
        with open(
            os.path.join(ASSET_PATH, "template", "front.html"), "r", encoding="utf-8"
        ) as f:
            qfmt = f.read()

        with open(
            os.path.join(ASSET_PATH, "template", "back.html"), "r", encoding="utf-8"
        ) as f:
            afmt = f.read()

        template.update(
            {
                "qfmt": qfmt,
                "afmt": afmt,
                "bqfmt": "",
                "bafmt": "",
                "did": None,
                "bfont": "",
                "bsize": 0,
            }
        )
        return template
