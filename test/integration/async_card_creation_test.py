import os
import tempfile
import unittest

from anki_sync_server.server.main import app


class TestAsyncCardCreation(unittest.TestCase):
    """Integration tests for async card creation workflow."""

    def setUp(self):
        """Set up test client and temporary database."""
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Create temporary database directory
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_api_endpoints_registered(self):
        """Test that API endpoints are properly registered."""
        # Verify endpoints exist by checking route map
        rules = [rule.rule for rule in self.app.url_map.iter_rules()]

        # Should have cloze notes endpoint
        self.assertIn("/api/v1/clozeNotes", rules)

        # Should have task status endpoint
        self.assertIn("/api/v1/tasks/<task_id>", rules)


if __name__ == "__main__":
    unittest.main()
