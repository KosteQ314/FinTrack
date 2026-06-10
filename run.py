import sys
import traceback

try:
    import threading

    import keyboard
    from PyQt6.QtCore import QObject, pyqtSignal
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

    from core.config import get as get_config
    from core.models import Transaction, TransactionType
    from core.storage import get_session, list_sessions, save_session
    from gui.app import FinTrackApp
    from gui.overlay import OverlayWindow
    from gui.toast import ToastNotification
    from gui.voice import VoiceListener
except Exception as e:
    print("Import error:")
    traceback.print_exc()
    input("Press enter to exit...")
    sys.exit(1)


class Bridge(QObject):
    toggle_app_requested = pyqtSignal()
    show_overlay_requested = pyqtSignal()
    voice_command_ready = pyqtSignal(str, int, str)
    session_changed = pyqtSignal(str)  # session name


try:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    bridge = Bridge()

    # shared session state
    current_session = [None]  # list so it's mutable from nested functions

    def get_current_session():
        return current_session[0]

    def set_current_session(session):
        current_session[0] = session
        bridge.session_changed.emit(session.name if session else "")

    # prevent for accidentaly loading sessions
    current_session[0] = None

    # app window
    main_window = FinTrackApp(
        session=get_current_session(),
        on_session_change=set_current_session,
        on_transaction_added=lambda: None,
    )

    # small overlay
    small_overlay = OverlayWindow()
    if get_current_session():
        small_overlay.set_session(get_current_session().name)

    # toast
    toast = ToastNotification(timeout=get_config("voice_cancel_timeout") * 1000)

    # sync session changes to both windows
    def on_session_changed(name):
        print(f"Session changed to: {name}")
        from core.storage import get_session

        s = get_session(name) if name else None
        current_session[0] = s
        main_window.session = s
        main_window._refresh()
        if s:
            small_overlay.set_session(s.name)
        else:
            small_overlay.set_session("No active session")
        tray.setToolTip(f"FinTrack — {name if name else 'No session'}")
        tray.setContextMenu(build_tray_menu())

    bridge.session_changed.connect(on_session_changed)

    # transaction from small overlay
    def on_overlay_transaction(desc, amount, t_type):
        s = get_current_session()
        if not s:
            return
        t = Transaction(
            description=desc,
            amount=amount,
            type=TransactionType.INCOME
            if t_type == "income"
            else TransactionType.EXPENSE,
        )
        s.transactions.append(t)
        save_session(s)
        current_session[0] = get_session(s.name)
        main_window.session = current_session[0]
        main_window._refresh()

    small_overlay.transaction_submitted.connect(on_overlay_transaction)

    # voice
    def on_voice_command(command):
        if not get_current_session():
            return
        bridge.voice_command_ready.emit(
            command["desc"].title(), command["amount"], command["type"]
        )

    def on_voice_command_main(desc, amount, t_type):
        s = get_current_session()
        if not s:
            return
        label = "Income" if t_type == "income" else "Expense"
        message = f"{label}: {desc} — {amount:,} aUEC"

        def save_it():
            s = get_current_session()
            if not s:
                return
            t = Transaction(
                description=desc,
                amount=amount,
                type=TransactionType.INCOME
                if t_type == "income"
                else TransactionType.EXPENSE,
            )
            s.transactions.append(t)
            save_session(s)
            current_session[0] = get_session(s.name)
            main_window.session = current_session[0]
            main_window._refresh()

        toast.show_message(message, on_confirmed=save_it)

    bridge.voice_command_ready.connect(on_voice_command_main)

    voice_mode = get_config("voice_mode")
    voice = VoiceListener(on_command=on_voice_command)
    if voice_mode == "always":
        voice.start()

    # tray
    tray = QSystemTrayIcon(QIcon("assets/icon.png"), parent=app)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("System tray not available.")
        input("Press enter to exit...")
        sys.exit(1)
    if tray.icon().isNull():
        print("Icon failed to load.")
        input("Press enter to exit...")
        sys.exit(1)

    def build_tray_menu():
        current_voice_mode = get_config("voice_mode")
        tray_menu = QMenu()
        all_sessions = list_sessions()
        if all_sessions:
            sessions_menu = tray_menu.addMenu("Switch Session")
            for s in all_sessions:
                action = sessions_menu.addAction(s.name)
                action.triggered.connect(
                    lambda checked, name=s.name: set_current_session(get_session(name))
                )
        else:
            no_sessions = tray_menu.addAction("No sessions found")
            no_sessions.setEnabled(False)
        tray_menu.addSeparator()
        show_app = tray_menu.addAction("Show App")
        show_app.triggered.connect(
            lambda: (main_window.show(), main_window.activateWindow())
        )
        show_overlay = tray_menu.addAction("Show Overlay")
        show_overlay.triggered.connect(small_overlay.show_at_cursor)
        tray_menu.addSeparator()
        voice_action = tray_menu.addAction(
            "Disable Voice" if current_voice_mode == "always" else "Enable Voice"
        )
        voice_action.triggered.connect(toggle_voice)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(app.quit)
        return tray_menu

    def toggle_voice():
        current = get_config("voice_mode")
        from core.config import set as set_config

        if current == "always":
            voice.stop()
            set_config("voice_mode", "hotkey")
        else:
            voice.start()
            set_config("voice_mode", "always")
        tray.setContextMenu(build_tray_menu())

    def switch_session_tray(name):
        s = get_session(name)
        set_current_session(s)

    tray.setToolTip(
        f"FinTrack — {get_current_session().name if get_current_session() else 'No session'}"
    )
    tray.setContextMenu(build_tray_menu())
    tray.show()

    # hotkeys
    def hotkey_thread():
        voice_hotkey = get_config("voice_hotkey")
        app_toggle_hotkey = get_config("app_toggle_hotkey")

        keyboard.add_hotkey(
            get_config("hotkey"), lambda: bridge.show_overlay_requested.emit()
        )
        keyboard.add_hotkey(
            app_toggle_hotkey, lambda: bridge.toggle_app_requested.emit()
        )
        keyboard.on_press_key(
            voice_hotkey,
            lambda _: voice.start() if get_config("voice_mode") == "hotkey" else None,
        )
        keyboard.on_release_key(
            voice_hotkey,
            lambda _: voice.stop() if get_config("voice_mode") == "hotkey" else None,
        )

        try:
            keyboard.wait()
        except KeyboardInterrupt:
            pass

    bridge.show_overlay_requested.connect(small_overlay.show_at_cursor)
    bridge.toggle_app_requested.connect(main_window.toggle_overlay_mode)

    threading.Thread(target=hotkey_thread, daemon=True).start()

    main_window.show()
    print("FinTrack running — right-click tray icon to quit.")
    sys.exit(app.exec())

except Exception as e:
    print("Startup error:")
    traceback.print_exc()
    input("Press enter to exit...")
    sys.exit(1)
