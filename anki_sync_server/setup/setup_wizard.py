from typing import List

from anki_sync_server.setup.setup_step import SetupStep


class SetupWizard:
    def __init__(self) -> None:
        self._steps: List[SetupStep] = []

    def append(self, step: SetupStep) -> None:
        self._steps.append(step)

    def run_all(self):
        for step in self._steps:
            step.run()
