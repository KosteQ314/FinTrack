import sys
import traceback

try:
    import threading

    import keyboard
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

    from core.config import get as get_config
    from core.models import Transaction, TransactionType
    from core.storage import get_session, list_sessions, save_session
    from gui.overlay import OverlayWindow
except Exception as e:
    print("Import error:")
    traceback.print_exc()
    input("Press enter to exit...")
    sys.exit(1)

HOTKEY = get_config("hotkey")
WAKE_WORD = get_config("wake_word")

try:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = OverlayWindow()

    sessions = list_sessions()
    session = sessions[0] if sessions else None
    if session:
        window.set_session(session.name)
    else:
        window.set_session("No active session")

    def on_transaction(desc, amount, t_type):
        global session
        if not session:
            return
        t = Transaction(
            description=desc,
            amount=amount,
            type=TransactionType.INCOME
            if t_type == "income"
            else TransactionType.EXPENSE,
        )
        session.transactions.append(t)
        save_session(session)
        session = get_session(session.name)

    window.transaction_submitted.connect(on_transaction)

    tray = QSystemTrayIcon(QIcon("assets/icon.png"), parent=app)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("System tray not available on this system.")
        input("Press enter to exit...")
        sys.exit(1)
    if tray.icon().isNull():
        print("Icon failed to load — check assets/icon.png exists.")
        input("Press enter to exit...")
        sys.exit(1)

    def build_tray_menu():
        tray_menu = QMenu()
        all_sessions = list_sessions()
        if all_sessions:
            sessions_menu = tray_menu.addMenu("Switch Session")
            for s in all_sessions:
                action = sessions_menu.addAction(s.name)
                action.triggered.connect(
                    lambda checked, name=s.name: switch_session(name)
                )
        else:
            no_sessions = tray_menu.addAction("No sessions found")
            no_sessions.setEnabled(False)
        tray_menu.addSeparator()
        show_action = tray_menu.addAction("Show Overlay")
        show_action.triggered.connect(window.show_at_cursor)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(app.quit)
        return tray_menu

    def switch_session(name):
        global session
        session = get_session(name)
        window.set_session(session.name)
        tray.setToolTip(f"FinTrack — {session.name}")
        tray.setContextMenu(build_tray_menu())
        tray.showMessage(
            "FinTrack",
            f"Switched to '{session.name}'",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    tray.setToolTip(f"FinTrack — {session.name if session else 'No session'}")
    tray.setContextMenu(build_tray_menu())
    tray.show()

    def hotkey_thread():
        keyboard.add_hotkey(HOTKEY, lambda: window.show_requested.emit())
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            pass

    threading.Thread(target=hotkey_thread, daemon=True).start()

    print("FinTrack overlay running — right-click tray icon to quit.")
    sys.exit(app.exec())

except Exception as e:
    print("Startup error:")
    traceback.print_exc()
    input("Press enter to exit...")
    sys.exit(1)
