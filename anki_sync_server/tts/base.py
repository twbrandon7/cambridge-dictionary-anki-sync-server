from abc import ABC, abstractmethod


class TtsService(ABC):
    def generate_audio(self, text: str) -> bytes:
        return self._generate_audio(text)

    @abstractmethod
    def _generate_audio(self, text: str) -> bytes:
        raise NotImplementedError
