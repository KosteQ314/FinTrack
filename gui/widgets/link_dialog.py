import threading

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QCompleter,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from core.models import TransactionType
from core.prices import get_data


class _Loader(QObject):
    done = pyqtSignal(object)


class LinkDialog(QDialog):
    def __init__(self, parent, transaction):
        super().__init__(parent)
        self.t = transaction
        # income compares against sell prices, expenses against buy prices
        self.side = "sell" if transaction.type == TransactionType.INCOME else "buy"
        self.data = {"prices": {}, "terminals": {}}
        self.setWindowTitle("Link commodity")
        self.setMinimumWidth(420)
        self._build_ui()
        self._load()

    def _build_ui(self):
        self.setStyleSheet("""
            QDialog { background: #0a0e17; }
            QLabel { color: #c8d6e8; }
            QComboBox, QLineEdit {
                background: rgba(255,255,255,8);
                border: 1px solid rgba(100,160,255,50);
                border-radius: 4px;
                color: #c8d6e8;
                padding: 5px 8px;
            }
            QComboBox QAbstractItemView {
                background: #0d1220;
                color: #c8d6e8;
                selection-background-color: rgba(100,160,255,60);
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel(f"{self.t.description}  ·  {int(self.t.amount):,} aUEC")
        title.setStyleSheet("color: #c8a020; font-weight: bold;")
        layout.addWidget(title)

        row = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo.lineEdit().setPlaceholderText("Search commodity...")
        completer = self.combo.completer()
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.combo.currentTextChanged.connect(self._update)

        self.scu_input = QLineEdit()
        self.scu_input.setPlaceholderText("SCU (optional)")
        self.scu_input.setFixedWidth(130)
        if self.t.scu:
            self.scu_input.setText(f"{self.t.scu:g}")
        self.scu_input.textChanged.connect(self._update)

        row.addWidget(self.combo, stretch=1)
        row.addWidget(self.scu_input)
        layout.addLayout(row)

        self.info = QLabel("Loading prices...")
        self.info.setWordWrap(True)
        self.info.setStyleSheet("color: rgba(200,200,200,140); font-size: 12px;")
        layout.addWidget(self.info)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_btn.setEnabled(False)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self):
        # the first fetch can take a few seconds, so keep it off the UI thread
        self._loader = _Loader()
        self._loader.done.connect(self._on_loaded)

        def work():
            data = get_data()
            try:
                self._loader.done.emit(data)
            except RuntimeError:
                pass  # dialog closed before the fetch finished

        threading.Thread(target=work, daemon=True).start()

    def _on_loaded(self, data):
        self.data = data
        names = sorted(data["prices"])
        if not names:
            self.info.setText("Prices unavailable. Check your connection or API key.")
            return
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(names)
        self.combo.blockSignals(False)
        idx = self.combo.findText(self.t.commodity) if self.t.commodity else -1
        self.combo.setCurrentIndex(idx)
        if idx < 0:
            self.combo.setEditText("")
        self._update()

    def _current(self):
        names = {n.lower(): n for n in self.data["prices"]}
        return names.get(self.combo.currentText().strip().lower())

    def _scu(self):
        try:
            return max(float(self.scu_input.text()), 0)
        except ValueError:
            return 0

    def _update(self, *_):
        name = self._current()
        self.ok_btn.setEnabled(bool(name))
        if not self.data["prices"]:
            return
        if not name:
            self.info.setText("Type or pick a commodity.")
            return
        market = self.data["prices"][name][self.side]
        label = "sell" if self.side == "sell" else "buy"
        text = f"Market {label} price: {market:,}/SCU"
        scu = self._scu()
        if scu > 0 and market:
            actual = int(self.t.amount / scu)
            diff = (actual - market) / market * 100
            text += f"\nYour price: {actual:,}/SCU ({diff:+.0f}% vs market)"
        self.info.setText(text)

    def values(self):
        """(commodity, scu, unit_price) for the chosen link."""
        name = self._current()
        return name, self._scu(), self.data["prices"][name][self.side]
