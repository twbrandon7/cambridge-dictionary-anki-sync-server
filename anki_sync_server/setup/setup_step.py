from abc import ABC


class SetupStep(ABC):
    def run(self) -> None:
        raise NotImplementedError
