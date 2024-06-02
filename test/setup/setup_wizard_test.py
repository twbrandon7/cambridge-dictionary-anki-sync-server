import unittest

from anki_sync_server.setup.setup_step import SetupStep
from anki_sync_server.setup.setup_wizard import SetupWizard


class SetupWizardTest(unittest.TestCase):
    def test_run_all(self):
        class MockSetupStep(SetupStep):
            def __init__(self):
                self._run_called = False

            def run(self):
                self._run_called = True

        step1 = MockSetupStep()
        step2 = MockSetupStep()
        wizard = SetupWizard()
        wizard.append(step1)
        wizard.append(step2)

        wizard.run_all()

        self.assertTrue(step1._run_called)
        self.assertTrue(step2._run_called)


if __name__ == '__main__':
    unittest.main()
