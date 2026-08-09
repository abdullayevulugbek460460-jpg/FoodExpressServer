import json
from config import DATA_FILE


def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "menu": [],
            "orders": []
        }


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
