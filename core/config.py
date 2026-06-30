import json
import os
import sys


def get_app_dir():
    if getattr(sys, "frozen", False):
        # running as a bundled exe — use the folder the exe is in
        return os.path.dirname(sys.executable)
    else:
        # running from source
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


CONFIG_PATH = os.path.join(get_app_dir(), "config.json")

DEFAULTS = {
    "hotkey": "f9",
    "wake_word": "fin",
    "voice_mode": "always",
    "voice_hotkey": "f8",
    "app_toggle_hotkey": "f7",
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
