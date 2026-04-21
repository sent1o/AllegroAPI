import os
import sys
from dotenv import load_dotenv

if getattr(sys, "frozen", False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_path, ".env")
load_dotenv(dotenv_path)

CLIENT_ID = os.getenv("ID")
CLIENT_SECRET = os.getenv("SECRET")


def get_base_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_path()
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
CORE_PATH = os.path.join(BASE_DIR, "core.json")
RAW_DATA_FILE = os.path.join(BASE_DIR, "raw_allegro_data.json")
