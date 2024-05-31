import os
import tempfile
import unittest

from anki.collection import Collection

from anki_sync_server.anki.model_creator import ModelCreator


class ModelCreatorTest(unittest.TestCase):
    def test_create_model_when_not_exists(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            col = Collection(os.path.join(tmpdirname, "collection.anki2"))
            all_model_names = [model["name"] for model in col.models.all()]
            self.assertNotIn(ModelCreator.MODEL_NAME, all_model_names)

            creator = ModelCreator(col)
            model = creator.create_model()

            self.assertEqual(ModelCreator.MODEL_NAME, model["name"])

            model = col.models.get(model["id"])  # make sure model is saved
            self.assertIsNotNone(model)
            self.assertEqual(ModelCreator.MODEL_NAME, model["name"])

    def test_create_model_when_exists(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            col = Collection(os.path.join(tmpdirname, "collection.anki2"))
            self.assertIsNone(col.models.by_name(ModelCreator.MODEL_NAME))
            template = col.models.new_template("Custom Cloze")
            template.update(
                {
                    "ord": 0,
                    "qfmt": "{{cloze:Text}}\n<br>\n{{type:cloze:Text}}",
                    "afmt": "{{cloze:Text}}<br>\n{{type:cloze:Text}}\n{{ExtraOnBack}}",
                    "bqfmt": "",
                    "bafmt": "",
                    "did": None,
                    "bfont": "",
                    "bsize": 0,
                }
            )

            field_text = col.models.new_field("Text")
            field_text.update(
                {
                    "ord": 0,
                    "sticky": False,
                    "rtl": False,
                    "font": "Arial",
                    "size": 20,
                    "description": "",
                    "plainText": False,
                    "collapsed": False,
                    "excludeFromSearch": False,
                    "tag": 0,
                    "preventDeletion": True,
                }
            )

            field_back = col.models.new_field("ExtraOnBack")
            field_back.update(
                {
                    "ord": 1,
                    "sticky": False,
                    "rtl": False,
                    "font": "Arial",
                    "size": 20,
                    "description": "",
                    "plainText": False,
                    "collapsed": False,
                    "excludeFromSearch": False,
                    "tag": 1,
                    "preventDeletion": False,
                }
            )

            new_model = col.models.new("Custom Cloze")
            new_model.update(
                {
                    "type": 1,
                    "mod": 1715785492,
                    "usn": 0,
                    "sortf": 0,
                    "did": None,
                    "tmpls": [template],
                    "flds": [field_text, field_back],
                    "css": ".test {}",
                    "latexPre": "\\documentclass[12pt]{article}\n"
                    + "\\special{papersize=3in,5in}\n\\usepackage[utf8]{inputenc}\n"
                    + "\\usepackage{amssymb,amsmath}\n\\pagestyle{empty}\n"
                    + "\\setlength{\\parindent}{0in}\n\\begin{document}\n",
                    "latexPost": "\\end{document}",
                    "latexsvg": False,
                    "req": [[0, "any", [0]]],
                    "originalStockKind": 5,
                }
            )
            col.models.save(new_model)

            all_model_names = [model["name"] for model in col.models.all()]
            self.assertIn(ModelCreator.MODEL_NAME, all_model_names)

            creator = ModelCreator(col)
            model = creator.create_model()

            model = col.models.get(model["id"])

            self.assertEqual(ModelCreator.MODEL_NAME, model["name"])
            self.assertEqual(".test {}", model["css"])


if __name__ == "__main__":
    unittest.main()
