import os
import tempfile
import unittest
from unittest import mock

from anki_sync_server.tts.google import GcpTtsService


class GcpTtsServiceTest(unittest.TestCase):
    def test_generate_file(self):
        with mock.patch.object(GcpTtsService, "_make_request") as mock_make_request:
            mock_make_request.return_value = {"audioContent": "aGVsbG8="}
            with tempfile.NamedTemporaryFile() as f:
                tts = GcpTtsService(api_key="test")
                tts.generate_audio(output_file=f.name, text="hello")
                f.seek(0)
                self.assertEqual(f.read(), b"hello")

    def test_audio_not_found_exception(self):
        with mock.patch.object(GcpTtsService, "_make_request") as mock_make_request:
            mock_make_request.return_value = {}
            with tempfile.TemporaryDirectory() as d:
                temp_file = os.path.join(d, "temp.wav")
                tts = GcpTtsService(api_key="test")
                with self.assertRaises(Exception, msg="No audio content"):
                    tts.generate_audio(output_file=temp_file, text="hello")
                # make sure the file was not created
                self.assertFalse(os.path.exists(temp_file))


if __name__ == "__main__":
    unittest.main()
