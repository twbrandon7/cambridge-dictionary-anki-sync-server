import unittest

from anki_sync_server.utils import remove_anki_cloze_tags, remove_html_tags


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


if __name__ == "__main__":
    unittest.main()
