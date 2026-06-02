import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

DEFAULTS = {
    "hotkey": "f9",
    "wake_word": "fin",
    "voice_mode": "always",
    "voice_hotkey": "f8",
    "voice_cancel_timeout": 5,
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULTS)
        return DEFAULTS.copy()
    with open(CONFIG_PATH) as f:
        data = json.load(f)
    for key, value in DEFAULTS.items():
        if key not in data:
            data[key] = value
    return data


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def get(key):
    return load_config().get(key, DEFAULTS.get(key))


def set(key, value):
    config = load_config()
    config[key] = value
    save_config(config)
