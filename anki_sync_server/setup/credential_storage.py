import pickle
import threading
from multiprocessing import Lock

from anki.sync import SyncAuth


class CredentialStorage:
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    _initialized_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(CredentialStorage, cls).__new__(cls)
                    cls._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        with self._initialized_lock:
            if self._initialized:
                return
            self._reader_lock = Lock()
            self._writer_lock = Lock()
            self._reader_count = 0

            self._data = {
                "anki_session": None,
                "gcp_tts_api_key": None,
                "hashed_api_key": None,
                "server_secret_key": None,
                "refresh_token_created_at": None,
            }
            self._initialized = True

    @staticmethod
    def _writer(func):
        """The writer part of the first reader-writer algorithm."""

        def wrapper(*args, **kwargs):
            with CredentialStorage()._writer_lock:
                return func(*args, **kwargs)

        return wrapper

    @staticmethod
    def _reader(func):
        """The reader part of the first reader-writer algorithm."""

        def wrapper(*args, **kwargs):
            with CredentialStorage()._reader_lock:
                CredentialStorage()._reader_count += 1
                if CredentialStorage()._reader_count == 1:
                    CredentialStorage()._writer_lock.acquire()

            result = func(*args, **kwargs)

            with CredentialStorage()._reader_lock:
                CredentialStorage()._reader_count -= 1
                if CredentialStorage()._reader_count == 0:
                    CredentialStorage()._writer_lock.release()

            return result

        return wrapper

    @_reader
    def get_anki_session(self) -> SyncAuth | None:
        return self._data.get("anki_session")

    @_reader
    def get_gcp_tts_api_key(self) -> str | None:
        return self._data.get("gcp_tts_api_key")

    @_reader
    def get_hashed_api_key(self) -> bytes | None:
        return self._data.get("hashed_api_key")

    @_reader
    def get_server_secret_key(self) -> str | None:
        return self._data.get("server_secret_key")

    @_reader
    def get_refresh_token_created_at(self) -> int | None:
        return self._data.get("refresh_token_created_at")

    @_writer
    def set_anki_session(self, session: SyncAuth) -> None:
        self._data["anki_session"] = session

    @_writer
    def set_gcp_tts_api_key(self, api_key: str) -> None:
        self._data["gcp_tts_api_key"] = api_key

    @_writer
    def set_hashed_api_key(self, api_key: bytes) -> None:
        self._data["hashed_api_key"] = api_key

    @_writer
    def set_server_secret_key(self, server_secret_key: str) -> None:
        self._data["server_secret_key"] = server_secret_key

    @_writer
    def set_refresh_token_created_at(self, created_at: int) -> None:
        self._data["refresh_token_created_at"] = created_at

    @_writer
    def save(self, credential_name: str = ".credentials") -> None:
        with open(credential_name, "wb") as file:
            pickle.dump(self._data, file)

    @_writer
    def load(self, credential_name: str = ".credentials") -> None:
        with open(credential_name, "rb") as file:
            self._data = pickle.load(file)
