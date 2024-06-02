import os

from anki_sync_server.server import app

__current_directory = os.path.dirname(os.path.abspath(__file__))
ASSET_PATH = os.path.join(__current_directory, "assets")
