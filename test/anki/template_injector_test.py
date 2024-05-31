import os
import tempfile
import unittest
from anki.collection import Collection

from anki_sync_server.anki.template_injector import TemplateInjector


class TemplateInjectorTest(unittest.TestCase):
    def test_inject_when_not_exists(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            col = Collection(os.path.join(tmpdirname, "collection.anki2"))
            noteType = col.models.new("Custom Cloze")
            self.assertEqual([], noteType["tmpls"])
            injector = TemplateInjector(col)
            injector.inject(noteType)
            self.assertEqual(1, len(noteType["tmpls"]))
            self.assertEqual("Custom Cloze", noteType["tmpls"][0]["name"])

    def test_inject_when_exists(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            col = Collection(os.path.join(tmpdirname, "collection.anki2"))
            noteType = col.models.new("Custom Cloze")
            template = col.models.new_template("Custom Cloze")
            template["qfmt"] = ""
            noteType["tmpls"].append(template)
            self.assertEqual(1, len(noteType["tmpls"]))

            injector = TemplateInjector(col)
            injector.inject(noteType)
            self.assertEqual(1, len(noteType["tmpls"]))
            self.assertEqual("Custom Cloze", noteType["tmpls"][0]["name"])

            # make sure qfmt is not overwritten
            self.assertEqual("", noteType["tmpls"][0]["qfmt"])


if __name__ == "__main__":
    unittest.main()
