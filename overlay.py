import sys
import threading

import keyboard
from PyQt6.QtCore import QMetaObject, Qt
from PyQt6.QtWidgets import QApplication

from core.models import Transaction, TransactionType
from core.storage import get_session, save_session
from gui.overlay import OverlayWindow

HOTKEY = "f9"
SESSION_NAME = "TestRun"  # change this to your session name

app = QApplication(sys.argv)
window = OverlayWindow()

session = get_session(SESSION_NAME)
if session:
    window.set_session(session.name)
else:
    print(f"No session named '{SESSION_NAME}' found. Create it in the CLI first.")
    sys.exit(1)


def on_transaction(desc, amount, t_type):
    global session
    t = Transaction(
        description=desc,
        amount=amount,
        type=TransactionType.INCOME if t_type == "income" else TransactionType.EXPENSE,
    )
    session.transactions.append(t)
    save_session(session)
    session = get_session(session.name)


window.transaction_submitted.connect(on_transaction)


def hotkey_thread():
    keyboard.add_hotkey(HOTKEY, lambda: window.show_requested.emit())
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        pass


threading.Thread(target=hotkey_thread, daemon=True).start()

print(f"FinTrack overlay running — press {HOTKEY.upper()} in game to open.")

try:
    sys.exit(app.exec())
except KeyboardInterrupt:
    sys.exit(0)
