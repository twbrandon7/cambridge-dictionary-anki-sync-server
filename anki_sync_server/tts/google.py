import base64
import http.client
import json

from anki_sync_server.tts.base import TtsService


class GcpTtsService(TtsService):
    def __init__(self, api_key: str):
        self._api_key = api_key

    def _generate_audio(self, output_file: str, text: str) -> None:
        """
        Raises:
            JSONDecodeError: If the response is not a valid JSON
            Exception: If the response does not contain audio content
        """
        data_json = self._make_request(text)
        audio_content = data_json.get("audioContent")
        if audio_content is None:
            raise Exception("No audio content")

        audio_content = base64.b64decode(audio_content)
        with open(output_file, "wb") as f:
            f.write(audio_content)

    def _make_request(self, text: str) -> dict:
        """
        Raises:
            JSONDecodeError: If the response is not a valid JSON
        """
        conn = http.client.HTTPSConnection("texttospeech.googleapis.com")
        headers = {"content-type": "application/json", "X-Goog-Api-Key": self._api_key}
        conn.request(
            "POST", "/v1/text:synthesize", self._get_payload(text=text), headers
        )
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return json.loads(data)

    def _get_payload(self, text: str) -> str:
        data = {
            "audioConfig": {
                "audioEncoding": "LINEAR16",
                "effectsProfileId": ["large-home-entertainment-class-device"],
                "pitch": 0,
                "speakingRate": 1,
            },
            "input": {"text": text},
            "voice": {"languageCode": "en-US", "name": "en-US-Wavenet-D"},
        }
        return json.dumps(data)
