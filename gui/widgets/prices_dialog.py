import html
import threading

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QCompleter,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from core.prices import get_data


class _Loader(QObject):
    done = pyqtSignal(object)


class PricesDialog(QDialog):
    def __init__(self, parent=None, initial=""):
        super().__init__(parent)
        self.setWindowTitle("Commodity prices")
        self.setMinimumSize(520, 460)
        self.data = {"prices": {}, "terminals": {}}
        self._initial = initial
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
        self.scu_input.textChanged.connect(self._update)

        row.addWidget(self.combo, stretch=1)
        row.addWidget(self.scu_input)
        layout.addLayout(row)

        self.status = QLabel("Loading prices...")
        self.status.setStyleSheet("color: rgba(200,200,200,100); font-size: 11px;")
        layout.addWidget(self.status)

        self.result = QLabel("")
        self.result.setTextFormat(Qt.TextFormat.RichText)
        self.result.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.result.setWordWrap(True)
        layout.addWidget(self.result, stretch=1)

    def _load(self):
        # network fetch can take a few seconds, so keep it off the UI thread
        self._loader = _Loader()
        self._loader.done.connect(self._on_loaded)

        def work():
            data = get_data()
            try:
                self._loader.done.emit(data)
            except RuntimeError:
                pass  # dialog was closed before the fetch finished

        threading.Thread(target=work, daemon=True).start()

    def _on_loaded(self, data):
        self.data = data
        names = sorted(data["prices"])
        if not names:
            self.status.setText("Prices unavailable. Check your connection or API key.")
            return
        self.status.setText(f"{len(names)} commodities · averages from UEX")
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(names)
        self.combo.blockSignals(False)
        idx = self.combo.findText(self._initial) if self._initial else -1
        self.combo.setCurrentIndex(idx)
        self._update()

    def _update(self, *_):
        prices = self.data["prices"]
        if not prices:
            return
        names = {n.lower(): n for n in prices}
        name = names.get(self.combo.currentText().strip().lower())
        if not name:
            self.result.setText("Type or pick a commodity.")
            return
        try:
            scu = float(self.scu_input.text())
        except ValueError:
            scu = 0

        p = prices[name]
        parts = [
            f"<h3 style='color:#c8a020'>{html.escape(name)}</h3>",
            f"<p>Avg sell <b style='color:#2ecc71'>{p['sell']:,}</b>/SCU"
            f" &nbsp;·&nbsp; Avg buy <b style='color:#e74c3c'>{p['buy']:,}</b>/SCU</p>",
        ]
        if scu > 0 and p["sell"]:
            parts.append(
                f"<p>{scu:g} SCU sells for ~<b>{int(scu * p['sell']):,}</b> aUEC on average</p>"
            )

        for title, side in (("Best places to sell", "sell"), ("Cheapest places to buy", "buy")):
            rows = [r for r in self.data["terminals"].get(name, []) if r[side] > 0]
            rows.sort(key=lambda r: r[side], reverse=(side == "sell"))
            parts.append(f"<p style='color:#6ea0ff'><b>{title}</b></p>")
            if not rows:
                parts.append("<p>no data</p>")
                continue
            table = ["<table cellspacing='4'>"]
            for r in rows[:5]:
                total = f"<td align='right'>{int(scu * r[side]):,}</td>" if scu > 0 else ""
                table.append(
                    f"<tr><td>{html.escape(r['terminal'])}</td>"
                    f"<td align='right'>{r[side]:,}/SCU</td>{total}</tr>"
                )
            table.append("</table>")
            parts.append("".join(table))
        self.result.setText("".join(parts))
