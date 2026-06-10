import sys
import traceback

try:
    import threading

    import keyboard
    from PyQt6.QtCore import QObject, pyqtSignal
    from PyQt6.QtWidgets import QApplication

    from core.config import get as get_config
    from core.storage import get_session, list_sessions
    from gui.app import FinTrackApp
except Exception as e:
    print("Import error:")
    import traceback

    traceback.print_exc()
    input("Press enter to exit...")
    sys.exit(1)


class AppBridge(QObject):
    toggle_requested = pyqtSignal()
    session_changed = pyqtSignal(str)


try:
    app = QApplication(sys.argv)

    current_session = [None]

    def get_current_session():
        return current_session[0]

    def set_current_session(session):
        current_session[0] = session
        bridge.session_changed.emit(session.name if session else "")

    bridge = AppBridge()

    main_window = FinTrackApp(
        session=get_current_session(),
        on_session_change=set_current_session,
        on_transaction_added=lambda: None,
    )

    def on_session_changed(name):
        s = get_session(name) if name else None
        current_session[0] = s
        main_window.session = s
        main_window._refresh()

    bridge.session_changed.connect(on_session_changed)
    bridge.toggle_requested.connect(main_window.toggle_overlay_mode)

    def hotkey_thread():
        keyboard.add_hotkey(
            get_config("app_toggle_hotkey"), lambda: bridge.toggle_requested.emit()
        )
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            pass

    threading.Thread(target=hotkey_thread, daemon=True).start()

    main_window.show()
    print("FinTrack app running.")
    sys.exit(app.exec())

except Exception as e:
    print("Startup error:")
    traceback.print_exc()
    input("Press enter to exit...")
    sys.exit(1)
