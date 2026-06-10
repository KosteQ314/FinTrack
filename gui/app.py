from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FinTrackApp(QMainWindow):
    def __init__(self, session=None, on_session_change=None, on_transaction_added=None):
        super().__init__()
        self.session = session
        self.on_session_change = on_session_change
        self.on_transaction_added = on_transaction_added
        self.is_overlay_mode = False

        self.setWindowTitle("FinTrack")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0e17;
            }
            QWidget {
                background-color: #0a0e17;
                color: #c8d6e8;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13pt;
            }
            QFrame#sidebar {
                background-color: #0d1220;
                border-right: 1px solid rgba(100, 160, 255, 40);
            }
            QFrame#main_panel {
                background-color: #0a0e17;
            }
            QPushButton {
                background: rgba(255,255,255,5);
                border: 1px solid rgba(100,160,255,50);
                border-radius: 4px;
                color: #c8d6e8;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background: rgba(100,160,255,20);
                border: 1px solid rgba(100,160,255,120);
            }
            QPushButton:pressed {
                background: rgba(100,160,255,40);
            }
            QLabel#gold {
                color: #c8a020;
                font-size: 18pt;
                font-weight: bold;
                letter-spacing: 2px;
            }
            QLabel#section_title {
                color: rgba(100,160,255,200);
                font-size: 11pt;
                letter-spacing: 1px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 4px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: rgba(100,160,255,60);
                border-radius: 2px;
            }
        """)

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(16, 16, 16, 16)
        self.sidebar_layout.setSpacing(8)

        # main panel
        self.main_panel = QFrame()
        self.main_panel.setObjectName("main_panel")
        self.main_panel_layout = QVBoxLayout(self.main_panel)
        self.main_panel_layout.setContentsMargins(24, 16, 24, 16)
        self.main_panel_layout.setSpacing(12)

        root.addWidget(self.sidebar)
        root.addWidget(self.main_panel, stretch=1)

        self._build_sidebar()
        self._build_main_panel()
        self._build_bottom_bar()

    def _build_sidebar(self):
        from gui.widgets.sidebar import SidebarWidget

        self.sidebar_widget = SidebarWidget(
            session=self.session,
            on_session_change=self._on_session_change,
            on_player_added=self._refresh,
            on_player_removed=self._refresh,
        )
        self.sidebar_layout.addWidget(self.sidebar_widget)

    def _build_main_panel(self):
        from gui.widgets.main_panel import MainPanelWidget

        self.main_panel_widget = MainPanelWidget(
            session=self.session,
            on_transaction_added=self._on_transaction_added,
            on_transaction_removed=self._refresh,
        )
        self.main_panel_layout.addWidget(self.main_panel_widget)

    def _build_bottom_bar(self):
        bar = QWidget()
        bar.setStyleSheet(
            "background: #0d1220; border-top: 1px solid rgba(100,160,255,30);"
        )
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(16, 8, 16, 8)

        self.statusLabel = QLabel("Ready")
        self.statusLabel.setStyleSheet("color: rgba(200,200,200,100); font-size: 11px;")
        bar_layout.addWidget(self.statusLabel)
        bar_layout.addStretch()

        self.toggle_btn = QPushButton("⧉  Overlay mode")
        self.toggle_btn.setFixedWidth(160)
        self.toggle_btn.clicked.connect(self.toggle_overlay_mode)
        bar_layout.addWidget(self.toggle_btn)

        self.main_panel_layout.addWidget(bar)

    def _on_session_change(self, session):
        self.session = session
        if self.on_session_change:
            self.on_session_change(session)
        self._refresh()

    def _on_transaction_added(self):
        self._refresh()
        if self.on_transaction_added:
            self.on_transaction_added()

    def _refresh(self):
        from core.storage import get_session

        if self.session:
            self.session = get_session(self.session.name)
        self.sidebar_widget.update_session(self.session)
        self.main_panel_widget.update_session(self.session)

    def toggle_overlay_mode(self):
        self.is_overlay_mode = not self.is_overlay_mode
        if self.is_overlay_mode:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Window
            )
            self.setFixedSize(520, 600)
            self.toggle_btn.setText("⧉  App mode")
            self.sidebar.hide()
            self.main_panel_widget.show_session_header(True)
            self.setWindowOpacity(0.88)
        else:
            self.setWindowFlags(
                Qt.WindowType.Window  # ← plain window, no always-on-top
            )
            self.setMinimumSize(900, 600)
            self.setMaximumSize(16777215, 16777215)
            self.toggle_btn.setText("⧉  Overlay mode")
            self.sidebar.show()
            self.main_panel_widget.show_session_header(False)
            self.setWindowOpacity(1.0)
        self.show()
        self.activateWindow()  # ← brings focus back to the app when switching to app mode

    def set_status(self, message):
        self.statusLabel.setText(message)
