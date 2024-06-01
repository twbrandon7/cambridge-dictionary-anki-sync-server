import base64
import os
import tempfile
import unittest
from unittest import mock

from anki_sync_server.tts.google import GcpTtsService


class GcpTtsServiceTest(unittest.TestCase):
    def test_generate_file(self):
        with mock.patch.object(GcpTtsService, "_make_request") as mock_make_request:
            mock_make_request.return_value = {"audioContent": "aGVsbG8="}
            tts = GcpTtsService(api_key="test")
            audio_bytes = tts.generate_audio("hello")
            self.assertEqual(audio_bytes, base64.b64decode("aGVsbG8="))

    def test_audio_not_found_exception(self):
        with mock.patch.object(GcpTtsService, "_make_request") as mock_make_request:
            mock_make_request.return_value = {}
            tts = GcpTtsService(api_key="test")
            with self.assertRaises(Exception, msg="No audio content"):
                tts.generate_audio("hello")


if __name__ == "__main__":
    unittest.main()
