import uuid

from anki.collection import Collection

from anki_sync_server.thread import ThreadWithReturnValue


class MediaCreator:
    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def create_media(self, data: bytes, filename_prefix: str, extension: str) -> str:
        media_filename = f"{filename_prefix}-{uuid.uuid4()}.{extension}"
        thread = ThreadWithReturnValue(
            target=self._collection.media.write_data,
            args=(
                media_filename,
                data,
            ),
        )
        thread.start()
        return thread.join()
