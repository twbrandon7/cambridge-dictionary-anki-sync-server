import os
import sys
import tempfile
import unittest
import unittest.mock as mock


class AnkiLazyInitializationTest(unittest.TestCase):
    """Tests for lazy initialization of Anki collection in multi-process environment."""

    def setUp(self):
        """Set up test environment with mocked credential file."""
        # Create a temporary credentials file
        self.temp_creds = tempfile.NamedTemporaryFile(delete=False, mode='wb')
        # Write a minimal pickle-compatible credential structure
        import pickle
        pickle.dump({}, self.temp_creds)
        self.temp_creds.close()
        
        # Patch the credential file path before importing
        self.creds_patcher = mock.patch(
            'anki_sync_server.CREDENTIAL_FILE_PATH',
            self.temp_creds.name
        )
        self.creds_patcher.start()
        
        # Patch CredentialStorage.load to do nothing
        self.load_patcher = mock.patch(
            'anki_sync_server.setup.credential_storage.CredentialStorage.load'
        )
        self.load_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.load_patcher.stop()
        self.creds_patcher.stop()
        os.unlink(self.temp_creds.name)
        
        # Clear the module from cache to reset state
        if 'anki_sync_server.server' in sys.modules:
            del sys.modules['anki_sync_server.server']

    def test_proxy_object_pattern(self):
        """Test the proxy pattern implementation."""
        from anki_sync_server.server import _AnkiProxy
        
        proxy = _AnkiProxy()
        self.assertIsInstance(proxy, _AnkiProxy)

    @mock.patch('anki_sync_server.server.create_anki_collection')
    @mock.patch('anki_sync_server.server.GcpTtsService')
    @mock.patch('anki_sync_server.server.Anki')
    @mock.patch('anki_sync_server.server.CredentialStorage')
    def test_lazy_initialization_on_first_access(
        self, mock_creds, mock_anki_cls, mock_tts, mock_create_collection
    ):
        """Test that Anki instance is created only when accessed."""
        # Import after patches are in place
        import anki_sync_server.server as server_module
        
        # Reset the global state
        server_module._anki = None
        
        # Mock credentials
        mock_creds_instance = mock.Mock()
        mock_creds_instance.get_gcp_tts_api_key.return_value = "test_key"
        mock_creds.return_value = mock_creds_instance
        
        # Mock collection creation
        mock_collection = mock.Mock()
        mock_create_collection.return_value = mock_collection
        
        # Mock TTS service
        mock_tts_instance = mock.Mock()
        mock_tts.return_value = mock_tts_instance
        
        # Mock Anki instance
        mock_anki_instance = mock.Mock()
        mock_anki_instance.add_cloze_note = mock.Mock(return_value=None)
        mock_anki_cls.return_value = mock_anki_instance
        
        # Create a fresh proxy
        proxy = server_module._AnkiProxy()
        
        # Reset call counts after module import
        mock_create_collection.reset_mock()
        mock_anki_cls.reset_mock()
        
        # Access a method - should trigger initialization
        _ = proxy.add_cloze_note
        
        # Verify initialization happened
        mock_create_collection.assert_called_once()
        mock_tts.assert_called_once_with("test_key")
        mock_anki_cls.assert_called_once_with(mock_collection, mock_tts_instance)

    @mock.patch('anki_sync_server.server.create_anki_collection')
    @mock.patch('anki_sync_server.server.GcpTtsService')
    @mock.patch('anki_sync_server.server.Anki')
    @mock.patch('anki_sync_server.server.CredentialStorage')
    def test_singleton_pattern(
        self, mock_creds, mock_anki_cls, mock_tts, mock_create_collection
    ):
        """Test that only one Anki instance is created across multiple accesses."""
        # Import after patches are in place
        import anki_sync_server.server as server_module
        
        # Reset the global state
        server_module._anki = None
        
        # Mock credentials
        mock_creds_instance = mock.Mock()
        mock_creds_instance.get_gcp_tts_api_key.return_value = "test_key"
        mock_creds.return_value = mock_creds_instance
        
        # Mock collection creation
        mock_collection = mock.Mock()
        mock_create_collection.return_value = mock_collection
        
        # Mock TTS service
        mock_tts_instance = mock.Mock()
        mock_tts.return_value = mock_tts_instance
        
        # Mock Anki instance
        mock_anki_instance = mock.Mock()
        mock_anki_cls.return_value = mock_anki_instance
        
        # Reset call counts
        mock_create_collection.reset_mock()
        mock_anki_cls.reset_mock()
        
        # Multiple accesses
        server_module._get_anki()
        server_module._get_anki()
        server_module._get_anki()
        
        # Verify initialization happened only once
        mock_create_collection.assert_called_once()
        mock_anki_cls.assert_called_once()

    @mock.patch('anki_sync_server.server.create_anki_collection')
    @mock.patch('anki_sync_server.server.GcpTtsService')
    @mock.patch('anki_sync_server.server.Anki')
    @mock.patch('anki_sync_server.server.CredentialStorage')
    def test_proxy_attribute_error_handling(
        self, mock_creds, mock_anki_cls, mock_tts, mock_create_collection
    ):
        """Test that proxy provides helpful error messages for missing attributes."""
        # Import after patches are in place
        import anki_sync_server.server as server_module
        
        # Reset the global state
        server_module._anki = None
        
        # Mock credentials
        mock_creds_instance = mock.Mock()
        mock_creds_instance.get_gcp_tts_api_key.return_value = "test_key"
        mock_creds.return_value = mock_creds_instance
        
        # Mock collection creation
        mock_collection = mock.Mock()
        mock_create_collection.return_value = mock_collection
        
        # Mock TTS service
        mock_tts_instance = mock.Mock()
        mock_tts.return_value = mock_tts_instance
        
        # Mock Anki instance without the attribute
        mock_anki_instance = mock.Mock(spec=['add_cloze_note'])
        mock_anki_cls.return_value = mock_anki_instance
        
        # Create proxy
        proxy = server_module._AnkiProxy()
        
        # Try to access a non-existent attribute
        with self.assertRaises(AttributeError) as context:
            _ = proxy.non_existent_method
        
        # Verify the error message is helpful
        self.assertIn("_AnkiProxy", str(context.exception))
        self.assertIn("non_existent_method", str(context.exception))


if __name__ == "__main__":
    unittest.main()
