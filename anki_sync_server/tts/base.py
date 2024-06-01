from abc import ABC, abstractmethod


class TtsService(ABC):
    def generate_audio(self, output_file: str, text: str) -> None:
        self._generate_audio(output_file, text)

    @abstractmethod
    def _generate_audio(self, output_file: str, text: str) -> None:
        raise NotImplementedError
