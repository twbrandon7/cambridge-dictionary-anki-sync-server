import time
from threading import Lock

from anki.collection import Collection, SyncStatus
from anki.notes import Note

from anki_sync_server.anki.model_creator import ModelCreator
from anki_sync_server.thread import ThreadWithReturnValue


class Anki:
    def __init__(
        self,
        collection: Collection,
        username: str,
        password: str,
        deck_name: str = "English Vocabulary",
        media_sync_timeout_seconds: int = 600,
    ) -> None:
        self._lock = Lock()
        self._collection = collection
        self._deck_id = self._collection.decks.id_for_name(deck_name)
        self._model_creator = ModelCreator(collection)
        self._anki_model = None
        self._username = username
        self._password = password
        sync_thread = ThreadWithReturnValue(
            target=collection.sync_login,
            args=(
                username,
                password,
                "https://sync.ankiweb.net",
            ),
        )
        sync_thread.start()
        self._auth = sync_thread.join()
        self._new_auth = None
        self._media_sync_timeout_seconds = media_sync_timeout_seconds

    def add_cloze_note(
        self,
        text: str,
        text_translation: str,
        english_definition: str,
        definition_translation: str,
        word: str,
        part_of_speech: str,
        cefr_level: str,
        code: str,
    ) -> Note:
        with self._lock:
            self._sync(True)

            if self._anki_model is None:
                self._anki_model = self._model_creator.create_model()

            note = self._collection.new_note(self._anki_model)
            note["Text"] = text
            note["TextTranslation"] = text_translation
            note["EnDefinition"] = english_definition
            note["DefinitionTranslation"] = definition_translation
            note["Word"] = word
            note["PartOfSpeech"] = part_of_speech
            note["CefrLevel"] = cefr_level
            note["Code"] = code
            self._collection.add_note(note, self._deck_id)

            self._sync()
            return note

    def _sync(self, allow_force_download: bool = False) -> None:
        sync_status = self._collection.sync_status(self._auth)
        if sync_status.required == SyncStatus.NO_CHANGES:
            return
        print(sync_status.new_endpoint)
        if self._new_auth is None and sync_status.new_endpoint is not None:
            self._new_auth = self._collection.sync_login(
                self._username, self._password, sync_status.new_endpoint
            )
        auth = self._new_auth or self._auth
        if sync_status.required == SyncStatus.FULL_SYNC:
            if not allow_force_download:
                raise Exception("Full sync required")
            self._collection.full_upload_or_download(auth=auth, upload=False)
        if sync_status.required == SyncStatus.NORMAL_SYNC:
            self._collection.sync_collection(auth=auth, sync_media=False)

        self._collection.sync_media(auth=auth)
        synced = False
        for _ in range(self._media_sync_timeout_seconds):
            sync_status = self._collection.media_sync_status()
            if not sync_status.active:
                synced = True
                break
            time.sleep(1)

        if not synced:
            raise Exception("Media sync timed out")
