import os
import tempfile
import unittest

from anki.collection import Collection

from anki_sync_server.anki.fields_injector import FieldsInjector


class FieldsInjectorTest(unittest.TestCase):
    def test_inject_fields_when_no_existing_filed(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            col = Collection(os.path.join(tmpdirname, "collection.anki2"))
            injector = FieldsInjector(col)

            model = col.models.new("Custom Cloze")
            self.assertEqual([], model["flds"])

            injector.inject(model)

            model_fields = [field["name"] for field in model["flds"]]
            for field in FieldsInjector.TARGET_FIELDS:
                self.assertIn(field, model_fields)

    def test_inject_fields_when_existing_fields(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            col = Collection(os.path.join(tmpdirname, "collection.anki2"))
            injector = FieldsInjector(col)

            model = col.models.new("Custom Cloze")
            self.assertEqual([], model["flds"])

            for field in FieldsInjector.TARGET_FIELDS:
                default_field = col.models.new_field(field)
                default_field["size"] = 30
                model["flds"].append(default_field)
            injector.inject(model)

            model_fields = [field["name"] for field in model["flds"]]
            for field in FieldsInjector.TARGET_FIELDS:
                self.assertIn(field, model_fields)

            # make sure size is not overwritten
            for field in model["flds"]:
                self.assertEqual(30, field["size"])

    def test_inject_fields_and_fill_missing_fields(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            col = Collection(os.path.join(tmpdirname, "collection.anki2"))
            injector = FieldsInjector(col)

            model = col.models.new("Custom Cloze")
            self.assertEqual([], model["flds"])

            for i, field in enumerate(FieldsInjector.TARGET_FIELDS):
                default_field = col.models.new_field(field)
                default_field["size"] = 30
                model["flds"].append(default_field)
                if i > 5:
                    break

            self.assertEqual(7, len(model["flds"]))

            injector.inject(model)

            model_fields = [field["name"] for field in model["flds"]]
            for field in FieldsInjector.TARGET_FIELDS:
                self.assertIn(field, model_fields)

            # make sure size is not overwritten
            for i, field in enumerate(model["flds"]):
                self.assertEqual(30, field["size"])
                if i > 5:
                    break


if __name__ == "__main__":
    unittest.main()
