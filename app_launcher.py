import sys
import threading

import keyboard
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication

from core.config import get as get_config
from gui.app import FinTrackApp


class AppBridge(QObject):
    toggle_requested = pyqtSignal()


app = QApplication(sys.argv)
window = FinTrackApp()
bridge = AppBridge()
bridge.toggle_requested.connect(window.toggle_overlay_mode)


def hotkey_thread():
    keyboard.add_hotkey(
        get_config("app_toggle_hotkey"), lambda: bridge.toggle_requested.emit()
    )
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        pass


threading.Thread(target=hotkey_thread, daemon=True).start()

window.show()
sys.exit(app.exec())
