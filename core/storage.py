import json
import os

from core.models import Player, Session, SplitConfig, Transaction, TransactionType

# Where the session data is saved
SAVE_PATH = os.path.expanduser("~/.FinTrack/sessions.json")


# Ensures the save file exists and is initialized
def _ensure_file():
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    if not os.path.exists(SAVE_PATH):
        with open(SAVE_PATH, "w") as f:
            json.dump({}, f)


# Loads all session data from the save file
def _load_all():
    _ensure_file()
    with open(SAVE_PATH) as f:
        return json.load(f)


# Saves all session data to the save file
def _save_all(data):
    with open(SAVE_PATH, "w") as f:
        json.dump(data, f, indent=2)


# Lists all sessions by loading all data and converting each dictionary to a session object
def list_sessions():
    return [_dict_to_session(d) for d in _load_all().values()]


# Retrieves a session by name, converting the dictionary to a session object if found
def get_session(name):
    data = _load_all()
    for d in data.values():
        if d["name"].lower() == name.lower():
            return _dict_to_session(d)
    return None


# Saves a session by converting it to a dictionary and adding it to the save file
def save_session(session):
    data = _load_all()
    data[session.id] = _session_to_dict(session)
    _save_all(data)


# Deletes a session by name, removing it from the save file if found
def delete_session(name):
    data = _load_all()
    for key, d in list(data.items()):
        if d["name"].lower() == name.lower():
            del data[key]
            _save_all(data)
            return True
    return False


# Converts a session to a dictionary representation
def _session_to_dict(session):
    return {
        "id": session.id,
        "name": session.name,
        "players": [{"id": p.id, "name": p.name} for p in session.players],
        "transactions": [
            {
                "id": t.id,
                "description": t.description,
                "amount": t.amount,
                "type": t.type.value,
            }
            for t in session.transactions
        ],
        "split_config": {  # ← new
            "mode": session.split_config.mode,
            "overrides": session.split_config.overrides,
        },
    }


# Converts a dictionary representation to a session object
def _dict_to_session(d):
    session = Session(name=d["name"], id=d["id"])
    session.players = [Player(name=p["name"], id=p["id"]) for p in d["players"]]
    session.transactions = [
        Transaction(
            description=t["description"],
            amount=t["amount"],
            type=TransactionType(t["type"]),
            id=t["id"],
        )
        for t in d["transactions"]
    ]
    cfg = d.get("split_config", {})  # ← new
    session.split_config = SplitConfig(
        mode=cfg.get("mode", "equal"), overrides=cfg.get("overrides", {})
    )
    return session
