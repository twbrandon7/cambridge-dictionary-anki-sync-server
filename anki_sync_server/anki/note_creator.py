from typing import Tuple

from anki.notes import Note

from anki_sync_server.anki.cloze_note import ClozeNote
from anki_sync_server.anki.media_creator import MediaCreator
from anki_sync_server.tts.base import TtsService
from anki_sync_server.utils import remove_anki_cloze_tags, remove_html_tags


class NoteCreator:
    def __init__(self, media_creator: MediaCreator, tts_service: TtsService) -> None:
        self._media_creator = media_creator
        self._tts_service = tts_service

    def convert(self, empty_note: Note, cloze_note: ClozeNote) -> Note:
        empty_note["Text"] = cloze_note["englishExample"]
        empty_note["TextTranslation"] = cloze_note["exampleTranslation"]
        empty_note["EnDefinition"] = cloze_note["englishDefinition"]
        empty_note["DefinitionTranslation"] = cloze_note["definitionTranslation"]
        empty_note["Word"] = cloze_note["word"]
        empty_note["PartOfSpeech"] = cloze_note["partOfSpeech"]
        empty_note["CefrLevel"] = cloze_note["cefrLevel"]
        empty_note["Code"] = cloze_note["code"]

        word_audio_file, text_audio_file = self._create_audio_files(
            cloze_note["word"], cloze_note["englishExample"]
        )

        empty_note["DefinitionAudio"] = "[sound:{}]".format(word_audio_file)
        empty_note["TextAudio"] = "[sound:{}]".format(text_audio_file)

        return empty_note

    def _create_audio_files(self, word: str, english_example: str) -> Tuple[str, str]:
        word_audio_file = self._media_creator.create_media(
            self._tts_service.generate_audio(word),
            "googletts",
            ".mp3",
        )
        text_audio_file = self._media_creator.create_media(
            self._tts_service.generate_audio(
                remove_anki_cloze_tags(remove_html_tags(english_example))
            ),
            "googletts",
            ".mp3",
        )
        return word_audio_file, text_audio_file
