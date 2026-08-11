import os

PORT = int(os.environ.get("PORT", 8080))

DATA_FILE = "data.json"

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")
