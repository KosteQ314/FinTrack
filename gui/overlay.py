from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class OverlayWindow(QWidget):
    transaction_submitted = pyqtSignal(str, int, str)
    show_requested = pyqtSignal()  # ← new

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FinTrack")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.show_requested.connect(self.show_at_cursor)  # ← new
        self._build_ui()
        self.hide()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            #container {
                background-color: rgba(15, 20, 30, 220);
                border: 1px solid rgba(100, 160, 255, 80);
                border-radius: 8px;
                padding: 4px;
            }
        """)

        layout = QVBoxLayout(self.container)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        top_row = QHBoxLayout()
        title = QLabel("FinTrack")
        title.setStyleSheet(
            "color: rgba(180, 140, 40, 255); font-size: 13px; font-weight: bold; letter-spacing: 2px;"
        )
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.hide)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255,255,255,120);
                font-size: 12px;
            }
            QPushButton:hover { color: white; }
        """)
        top_row.addWidget(title)
        top_row.addStretch()
        top_row.addWidget(close_btn)
        layout.addLayout(top_row)

        self.session_label = QLabel("No active session")
        self.session_label.setStyleSheet(
            "color: rgba(100, 160, 255, 200); font-size: 11px;"
        )
        layout.addWidget(self.session_label)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description")
        self.desc_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,15);
                border: 1px solid rgba(100,160,255,60);
                border-radius: 4px;
                color: white;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid rgba(100,160,255,180); }
        """)
        layout.addWidget(self.desc_input)

        self.amt_input = QLineEdit()
        self.amt_input.setPlaceholderText("Amount (aUEC)")
        self.amt_input.setStyleSheet(self.desc_input.styleSheet())
        layout.addWidget(self.amt_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.inc_btn = QPushButton("+ Income")
        self.exp_btn = QPushButton("- Expense")

        for btn in (self.inc_btn, self.exp_btn):
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,10);
                    border: 1px solid rgba(100,160,255,60);
                    border-radius: 4px;
                    color: white;
                    padding: 6px 12px;
                    font-size: 12px;
                }
                QPushButton:hover { background: rgba(100,160,255,40); }
                QPushButton:pressed { background: rgba(100,160,255,70); }
            """)

        self.inc_btn.clicked.connect(lambda: self._submit("income"))
        self.exp_btn.clicked.connect(lambda: self._submit("expense"))

        btn_row.addWidget(self.inc_btn)
        btn_row.addWidget(self.exp_btn)
        layout.addLayout(btn_row)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            "color: rgba(255,255,255,140); font-size: 11px;"
        )
        layout.addWidget(self.status_label)

        outer.addWidget(self.container)
        self.setFixedWidth(300)

    def set_session(self, name):
        self.session_label.setText(f"Session: {name}")

    def _submit(self, transaction_type):
        desc = self.desc_input.text().strip()
        amt_text = self.amt_input.text().strip()

        if not desc:
            self.status_label.setText("Enter a description.")
            return
        try:
            amount = int(float(amt_text))
        except ValueError:
            self.status_label.setText("Enter a valid amount.")
            return

        self.transaction_submitted.emit(desc, amount, transaction_type)
        self.desc_input.clear()
        self.amt_input.clear()
        self.status_label.setText("Saved.")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key.Key_Return:
            self._submit("income")

    def show_at_cursor(self):
        from PyQt6.QtGui import QCursor
        from PyQt6.QtWidgets import QApplication

        screen = QApplication.screenAt(QCursor.pos())
        if screen:
            geometry = screen.geometry()
            x = geometry.x() + (geometry.width() - self.width()) // 2
            y = geometry.y() + (geometry.height() - self.height()) // 2
            self.move(x, y)
        self.show()
        self.desc_input.setFocus()
