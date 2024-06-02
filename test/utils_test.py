import os
import tempfile
import unittest
import unittest.mock as mock

from anki_sync_server.utils import (
    create_anki_collection,
    remove_anki_cloze_tags,
    remove_html_tags,
)


class UtilsTest(unittest.TestCase):
    def test_remove_anki_cloze_tags_with_no_tags(self):
        text = "I love Australian wines, especially the white wines."
        self.assertEqual(text, remove_anki_cloze_tags(text))

    def test_remove_anki_cloze_tags_with_one_tag(self):
        text = "I love Australian wines, {{c1::especially}} the white wines."
        self.assertEqual(
            "I love Australian wines, especially the white wines.",
            remove_anki_cloze_tags(text),
        )

    def test_remove_anki_cloze_tags_with_multiple_tags(self):
        text = "I love {{c1::Australian}} wines, {{c2::especially}} the white wines."
        self.assertEqual(
            "I love Australian wines, especially the white wines.",
            remove_anki_cloze_tags(text),
        )

    def test_remove_anki_cloze_tags_with_multiple_tags_large_tag_ids(self):
        text = (
            "I love {{c1100::Australian}} wines, {{c2345::especially}} the white wines."
        )
        self.assertEqual(
            "I love Australian wines, especially the white wines.",
            remove_anki_cloze_tags(text),
        )

    def test_remove_anki_cloze_tags_with_one_broken_tag(self):
        text = "I love Australian wines, {{c1::especially the white wines."
        self.assertEqual(
            "I love Australian wines, {{c1::especially the white wines.",
            remove_anki_cloze_tags(text),
        )

    def test_remove_anki_cloze_tags_with_multiple_broken_tags(self):
        text = "I love {{c1::Australian wines, {{c2::especially the white wines."
        self.assertEqual(
            "I love {{c1::Australian wines, {{c2::especially the white wines.",
            remove_anki_cloze_tags(text),
        )

    def test_remove_anki_cloze_tags_with_left_curly_braces(self):
        text = "I love {{Australian wines, especially the white wines."
        self.assertEqual(
            "I love {{Australian wines, especially the white wines.",
            remove_anki_cloze_tags(text),
        )

    def test_remove_anki_cloze_tags_with_right_curly_braces(self):
        text = "I love Australian}} wines, especially the white wines."
        self.assertEqual(
            "I love Australian}} wines, especially the white wines.",
            remove_anki_cloze_tags(text),
        )

    def test_remove_html_tags(self):
        text = "<p>I love Australian wines, especially the white wines.</p>"
        self.assertEqual(
            "I love Australian wines, especially the white wines.",
            remove_html_tags(text),
        )

    def test_remove_html_tags_bold(self):
        text = "<b>I love Australian wines, especially the white wines.</b>"
        self.assertEqual(
            "I love Australian wines, especially the white wines.",
            remove_html_tags(text),
        )

    def test_remove_html_tags_broken_bold_left(self):
        text = "<b>I love Australian wines, especially the white wines."
        self.assertEqual(
            "I love Australian wines, especially the white wines.",
            remove_html_tags(text),
        )

    def test_remove_html_tags_broken_bold_right(self):
        text = "I love Australian wines, especially the white wines.</b>"
        self.assertEqual(
            "I love Australian wines, especially the white wines.",
            remove_html_tags(text),
        )

    def test_create_anki_collection_dir_not_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch("anki_sync_server.utils.Collection"):
                data_dir = os.path.join(temp_dir, "data2")
                self.assertFalse(os.path.exists(data_dir))
                create_anki_collection(data_dir=data_dir)
                self.assertTrue(os.path.exists(data_dir))
    
    def test_create_anki_collection_dir_not_specified(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch("anki_sync_server.utils.Collection"):
                with mock.patch("os.getcwd", return_value=temp_dir):
                    data_dir = os.path.join(temp_dir, "data")
                    self.assertFalse(os.path.exists(data_dir))
                    create_anki_collection()
                    self.assertTrue(os.path.exists(data_dir))


if __name__ == "__main__":
    unittest.main()
