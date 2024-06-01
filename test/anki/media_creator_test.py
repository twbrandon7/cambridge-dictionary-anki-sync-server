import os
import tempfile
import unittest
import uuid
from unittest.mock import MagicMock, patch

from anki.collection import Collection

from anki_sync_server.anki.media_creator import MediaCreator


def mock_uuid4(determined_uuid: str):
    return patch.object(uuid, "uuid4", return_value=uuid.UUID(determined_uuid))


class MediaCreatorTest(unittest.TestCase):
    def test_create_media(self):
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            col = Collection(os.path.join(tmp_dir_name, "collection.anki2"))
            media_creator = MediaCreator(col)
            with mock_uuid4("00000000-0000-0000-0000-000000000000"):
                input_bytes = "hello world".encode("utf-8")
                filename = media_creator.create_media(input_bytes, "test", "txt")
                self.assertEqual(
                    "test-00000000-0000-0000-0000-000000000000.txt", filename
                )
            self.assertTrue(col.media.have(filename))
            _file_path = os.path.join(col.media.dir(), filename)
            self.assertTrue(os.path.exists(_file_path))

            with open(_file_path, "rb") as file:
                self.assertEqual(input_bytes, file.read())


if __name__ == "__main__":
    unittest.main()
