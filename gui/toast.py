from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QScreen
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QPushButton, QWidget


class ToastNotification(QWidget):
    cancelled = pyqtSignal()

    def __init__(self, timeout=5000):
        super().__init__()
        self.timeout = timeout
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)
        self._confirmed_callback = None
        self._cancelled = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()

    def _build_ui(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            #container {
                background-color: rgba(15, 20, 30, 220);
                border: 1px solid rgba(100, 160, 255, 80);
                border-radius: 8px;
            }
        """)

        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        self.message_label = QLabel("")
        self.message_label.setStyleSheet("color: white; font-size: 13px;")
        layout.addWidget(self.message_label)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedWidth(60)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,10);
                border: 1px solid rgba(255,100,100,60);
                border-radius: 4px;
                color: rgba(255,120,120,255);
                padding: 4px 8px;
                font-size: 12px;
            }
            QPushButton:hover { background: rgba(255,100,100,40); }
        """)
        layout.addWidget(self.cancel_btn)

        self.progress_label = QLabel("5")
        self.progress_label.setStyleSheet(
            "color: rgba(255,255,255,80); font-size: 11px;"
        )
        self.progress_label.setFixedWidth(12)
        layout.addWidget(self.progress_label)

        outer.addWidget(self.container)

        self._countdown_timer = QTimer()
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._tick)
        self._remaining = self.timeout // 1000

    def _tick(self):
        self._remaining -= 1
        self.progress_label.setText(str(self._remaining))

    def _on_timeout(self):
        self._countdown_timer.stop()
        if not self._cancelled and self._confirmed_callback:
            self._confirmed_callback()
        self.hide()

    def _on_cancel(self):
        self._cancelled = True
        self._timer.stop()
        self._countdown_timer.stop()
        self.cancelled.emit()
        self.hide()

    def show_message(self, message, on_confirmed):
        self._cancelled = False
        self._confirmed_callback = on_confirmed
        self._remaining = self.timeout // 1000
        self.message_label.setText(message)
        self.progress_label.setText(str(self._remaining))

        screen = QApplication.primaryScreen().geometry()
        self.adjustSize()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + 40
        self.move(x, y)

        self.show()
        self._timer.start(self.timeout)
        self._countdown_timer.start()
