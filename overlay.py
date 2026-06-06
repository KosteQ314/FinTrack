import sys
import traceback

try:
    import threading

    import keyboard
    from PyQt6.QtCore import QObject, Qt, pyqtSignal
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

    from core.config import get as get_config
    from core.models import Transaction, TransactionType
    from core.storage import get_session, list_sessions, save_session
    from gui.overlay import OverlayWindow
    from gui.toast import ToastNotification
    from gui.voice import VoiceListener
except Exception as e:
    print("Import error:")
    traceback.print_exc()
    input("Press enter to exit...")
    sys.exit(1)

HOTKEY = get_config("hotkey")
WAKE_WORD = get_config("wake_word")


class VoiceBridge(QObject):
    command_ready = pyqtSignal(str, int, str)


try:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = OverlayWindow()
    toast = ToastNotification(timeout=get_config("voice_cancel_timeout") * 1000)
    voice_bridge = VoiceBridge()

    session = None
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

    def on_voice_command(command):
        if not session:
            return
        desc = command["desc"].title()
        amount = command["amount"]
        t_type = command["type"]
        voice_bridge.command_ready.emit(desc, amount, t_type)

    def on_voice_command_main(desc, amount, t_type):
        global session
        if not session:
            return
        label = "Income" if t_type == "income" else "Expense"
        message = f"{label}: {desc} — {amount:,} aUEC"

        def save_it():
            global session
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

        toast.show_message(message, on_confirmed=save_it)

    voice_bridge.command_ready.connect(on_voice_command_main)

    voice_mode = get_config("voice_mode")
    voice = VoiceListener(on_command=on_voice_command)

    if voice_mode == "always":
        voice.start()

    tray = QSystemTrayIcon(QIcon("assets/icon.png"), parent=app)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("System tray not available on this system.")
        input("Press enter to exit...")
        sys.exit(1)
    if tray.icon().isNull():
        print("Icon failed to load — check assets/icon.png exists.")
        input("Press enter to exit...")
        sys.exit(1)

    def toggle_voice():
        current = get_config("voice_mode")
        from core.config import set as set_config

        if current == "always":
            voice.stop()
            set_config("voice_mode", "hotkey")
        else:
            set_config("voice_mode", "always")
            voice.start()
        tray.setContextMenu(build_tray_menu())

    def build_tray_menu():
        current_voice_mode = get_config("voice_mode")
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
        voice_action = tray_menu.addAction(
            "Disable Voice" if current_voice_mode == "always" else "Enable Voice"
        )
        voice_action.triggered.connect(toggle_voice)
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
        toast.show_message(f"Switched to '{session.name}'", on_confirmed=lambda: None)

    tray.setToolTip(f"FinTrack — {session.name if session else 'No session'}")
    tray.setContextMenu(build_tray_menu())
    tray.show()

    def hotkey_thread():
        voice_hotkey = get_config("voice_hotkey")
        print(f"Voice hotkey registered: {voice_hotkey}")
        print(f"Voice mode: {get_config('voice_mode')}")

        keyboard.add_hotkey(HOTKEY, lambda: window.show_requested.emit())
        keyboard.on_press_key(
            voice_hotkey,
            lambda _: (
                print("PTT pressed")
                or (voice.start() if get_config("voice_mode") == "hotkey" else None)
            ),
        )
        keyboard.on_release_key(
            voice_hotkey,
            lambda _: (
                print("PTT released")
                or (voice.stop() if get_config("voice_mode") == "hotkey" else None)
            ),
        )

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
