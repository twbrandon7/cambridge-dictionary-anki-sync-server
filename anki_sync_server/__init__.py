import os

__current_directory = os.path.dirname(os.path.abspath(__file__))
ASSET_PATH = os.path.join(__current_directory, "assets")
CREDENTIAL_FILE_PATH = os.path.join(os.getcwd(), "data", ".credentials")
APP_NAME = "Anki Sync Server"
