import time
from threading import Lock

from anki.collection import Collection, SyncOutput, SyncStatus
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
        
        sync_attempt_result = self._collection.sync_collection(self._auth, True)

        if sync_attempt_result.new_endpoint != '':
            new_auth = self._collection.sync_login(
                self._username,
                self._password,
                sync_attempt_result.new_endpoint
            )
        else:
            new_auth = self._auth

        if sync_attempt_result.required == SyncOutput.NO_CHANGES:
            print("No changes is required")
            self._sync_media(new_auth)
            return
        
        if sync_attempt_result.required == SyncOutput.NORMAL_SYNC:
            print("Normal sync is required")
            self._collection.sync_collection(self._auth, True)
            self._sync_media(new_auth)
            return

        if sync_attempt_result.required == SyncOutput.FULL_UPLOAD:
            print("No data on server, skip.")
            return

        if (sync_attempt_result.required == SyncOutput.FULL_SYNC
            or sync_attempt_result.required == SyncOutput.FULL_DOWNLOAD):
            if not allow_force_download:
                raise Exception("Failed to sync, force download is not allowed")
            self._collection.full_upload_or_download(
                auth=new_auth,
                server_usn=None,
                upload=False
            )
            self._sync_media(new_auth)

    def _sync_media(self, new_auth) -> None:
        print("Syncing media")
        self._collection.sync_media(auth=new_auth)
        synced = False
        for _ in range(self._media_sync_timeout_seconds):
            sync_status = self._collection.media_sync_status()
            print(sync_status.progress)
            if not sync_status.active:
                synced = True
                break
            time.sleep(1)

        if not synced:
            raise Exception("Media sync timed out")
