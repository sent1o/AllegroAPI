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
