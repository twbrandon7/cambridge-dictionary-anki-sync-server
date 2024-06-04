import os
import tempfile
import unittest
from unittest import mock

from anki.collection import Collection

from anki_sync_server.anki.cloze_note import ClozeNote
from anki_sync_server.anki.model_creator import ModelCreator
from anki_sync_server.anki.note_creator import NoteCreator


class NoteCreatorTest(unittest.TestCase):
    def test_convert_cloze_note(self):
        cloze_note = ClozeNote().load(
            {
                "word": "construction",
                "partOfSpeech": "noun",
                "guideWord": "BUILDING",
                "englishDefinition": "the work of building or making something, "
                + "especially buildings, bridges, etc.",
                "definitionTranslation": "建造;構築;建設",
                "cefrLevel": "B2",
                "code": "[ U ]",
                "englishExample": "The bridge is a marvellous work of engineering and "
                + "construction.",
                "exampleTranslation": "這座橋樑是工程學和建築業的傑作。",
            }
        )

        with tempfile.TemporaryDirectory() as tmpdirname:
            collection = Collection(os.path.join(tmpdirname, "collection.anki2"))
            model_creator = ModelCreator(collection)
            model = model_creator.create_model()
            new_note = collection.new_note(model)

        mock_media_creator = mock.MagicMock()
        mock_tts_service = mock.MagicMock()

        def mock_create_media(data, filename_prefix, extension):
            dummy_filename = {
                b"definition": "definition.mp3",
                b"text": "text.mp3",
            }
            return dummy_filename.get(data)

        def mock_tts_service_generate_audio(text):
            example_str = "The bridge is a marvellous work of engineering and "
            +"construction."
            dummy_data = {
                "construction": b"definition",
                example_str: b"text",
            }
            return dummy_data.get(text)

        mock_media_creator.create_media.side_effect = mock_create_media
        mock_tts_service.generate_audio.side_effect = mock_tts_service_generate_audio

        creator = NoteCreator(mock_media_creator, mock_tts_service)
        note = creator.convert(new_note, cloze_note)

        self.assertEqual(
            note["Text"],
            "The bridge is a marvellous work of engineering and construction.",
        )
        self.assertEqual(
            note["TextTranslation"],
            "這座橋樑是工程學和建築業的傑作。",
        )
        self.assertEqual(
            note["EnDefinition"],
            "the work of building or making something, especially buildings, bridges, "
            + "etc.",
        )
        self.assertEqual(note["DefinitionTranslation"], "建造;構築;建設")
        self.assertEqual(note["Word"], "construction")
        self.assertEqual(note["PartOfSpeech"], "noun")
        self.assertEqual(note["CefrLevel"], "B2")
        self.assertEqual(note["Code"], "[ U ]")
        self.assertEqual(note["DefinitionAudio"], "[sound:definition.mp3]")
        self.assertEqual(note["TextAudio"], "[sound:text.mp3]")


if __name__ == "__main__":
    unittest.main()
