from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.models import Transaction, TransactionType
from core.storage import save_session


class MainPanelWidget(QWidget):
    def __init__(
        self, session=None, on_transaction_added=None, on_transaction_removed=None
    ):
        super().__init__()
        self.session = session
        self.on_transaction_added = on_transaction_added
        self.on_transaction_removed = on_transaction_removed
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # header row
        self.session_header = QLabel("No active session")
        self.session_header.setStyleSheet(
            "color: #c8a020; font-size: 15px; font-weight: bold; padding-bottom: 4px;"
        )
        self.session_header.hide()
        layout.addWidget(self.session_header)

        # summary row
        self.summary_row = QHBoxLayout()
        self.income_card = self._metric_card("Income", "0 aUEC", "#2ecc71")
        self.expenses_card = self._metric_card("Expenses", "0 aUEC", "#e74c3c")
        self.net_card = self._metric_card("Net profit", "0 aUEC", "#c8a020")
        self.summary_row.addWidget(self.income_card[0])
        self.summary_row.addWidget(self.expenses_card[0])
        self.summary_row.addWidget(self.net_card[0])
        layout.addLayout(self.summary_row)

        # divider
        layout.addWidget(self._divider())

        # transactions label
        tx_header = QHBoxLayout()
        tx_label = QLabel("TRANSACTIONS")
        tx_label.setObjectName("section_title")
        tx_header.addWidget(tx_label)
        tx_header.addStretch()
        layout.addLayout(tx_header)

        # transactions scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.tx_container = QWidget()
        self.tx_container.setStyleSheet("background: transparent;")
        self.tx_layout = QVBoxLayout(self.tx_container)
        self.tx_layout.setContentsMargins(0, 0, 0, 0)
        self.tx_layout.setSpacing(4)
        self.tx_layout.addStretch()

        scroll.setWidget(self.tx_container)
        layout.addWidget(scroll, stretch=1)

        # divider
        layout.addWidget(self._divider())

        # input row
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description")
        self.desc_input.setStyleSheet(self._input_style())

        self.amt_input = QLineEdit()
        self.amt_input.setPlaceholderText("Amount")
        self.amt_input.setFixedWidth(120)
        self.amt_input.setStyleSheet(self._input_style())

        inc_btn = QPushButton("+ Income")
        inc_btn.setStyleSheet(self._btn_style("#2ecc71"))
        inc_btn.clicked.connect(lambda: self._add_transaction("income"))

        exp_btn = QPushButton("− Expense")
        exp_btn.setStyleSheet(self._btn_style("#e74c3c"))
        exp_btn.clicked.connect(lambda: self._add_transaction("expense"))

        input_row.addWidget(self.desc_input, stretch=1)
        input_row.addWidget(self.amt_input)
        input_row.addWidget(inc_btn)
        input_row.addWidget(exp_btn)
        layout.addLayout(input_row)

        self._refresh_transactions()
        self._refresh_summary()

    def _metric_card(self, label, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: #0d1220;
                border: 1px solid rgba(100,160,255,30);
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            "color: rgba(200,200,200,100); font-size: 11px; letter-spacing: 1px;"
        )
        val = QLabel(value)
        val.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")

        card_layout.addWidget(lbl)
        card_layout.addWidget(val)
        return card, val

    def show_session_header(self, visible):
        if visible and self.session:
            self.session_header.setText(self.session.name)
        self.session_header.setVisible(visible)

    def _divider(self):
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background: rgba(100,160,255,30);")
        return line

    def _input_style(self):
        return """
            QLineEdit {
                background: rgba(255,255,255,5);
                border: 1px solid rgba(100,160,255,40);
                border-radius: 4px;
                color: #c8d6e8;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(100,160,255,150);
            }
        """

    def _btn_style(self, color):
        return f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {color}60;
                border-radius: 4px;
                color: {color};
                padding: 6px 14px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {color}20;
            }}
            QPushButton:pressed {{
                background: {color}40;
            }}
        """

    def _refresh_summary(self):
        if not self.session:
            self.income_card[1].setText("0 aUEC")
            self.expenses_card[1].setText("0 aUEC")
            self.net_card[1].setText("0 aUEC")
            return
        self.income_card[1].setText(f"{int(self.session.total_income):,} aUEC")
        self.expenses_card[1].setText(f"{int(self.session.total_expenses):,} aUEC")
        self.net_card[1].setText(f"{int(self.session.net_profit):,} aUEC")

    def _refresh_transactions(self):
        for i in reversed(range(self.tx_layout.count())):
            item = self.tx_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        if not self.session or not self.session.transactions:
            empty = QLabel("No transactions yet")
            empty.setStyleSheet("color: rgba(200,200,200,60); font-size: 12px;")
            self.tx_layout.addWidget(empty)
            self.tx_layout.addStretch()
            return

        for t in self.session.transactions:  # ← removed reversed()
            self.tx_layout.addWidget(self._transaction_row(t))
        self.tx_layout.addStretch()

    def _transaction_row(self, transaction):
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,3);
                border: 1px solid rgba(100,160,255,20);
                border-radius: 4px;
            }
            QFrame:hover {
                background: rgba(255,255,255,6);
                border: 1px solid rgba(100,160,255,40);
            }
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255,100,100,180);
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: rgba(255,100,100,255);
            }
        """)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(10, 6, 10, 6)

        is_income = transaction.type == TransactionType.INCOME
        symbol = "+" if is_income else "−"
        color = "#2ecc71" if is_income else "#e74c3c"

        symbol_label = QLabel(symbol)
        symbol_label.setStyleSheet(
            f"color: {color}; font-size: 14px; font-weight: bold;"
        )
        symbol_label.setFixedWidth(16)

        desc_label = QLabel(transaction.description)
        desc_label.setStyleSheet("color: #c8d6e8; font-size: 13px;")

        amt_label = QLabel(f"{int(transaction.amount):,} aUEC")
        amt_label.setStyleSheet(f"color: {color}; font-size: 13px;")
        amt_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(22, 22)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255, 80, 80, 200);
                font-size: 15px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                color: rgba(255, 80, 80, 255);
            }
        """)
        remove_btn.clicked.connect(lambda _, t=transaction: self._remove_transaction(t))

        row_layout.addWidget(symbol_label)
        row_layout.addWidget(desc_label, stretch=1)
        row_layout.addWidget(amt_label)
        row_layout.addWidget(remove_btn)
        return row

    def _add_transaction(self, t_type):
        if not self.session:
            return
        desc = self.desc_input.text().strip()
        amt_text = self.amt_input.text().strip()
        if not desc:
            self.desc_input.setFocus()
            return
        try:
            amount = int(float(amt_text))
        except ValueError:
            self.amt_input.setFocus()
            return

        t = Transaction(
            description=desc,
            amount=amount,
            type=TransactionType.INCOME
            if t_type == "income"
            else TransactionType.EXPENSE,
        )
        self.session.transactions.append(t)
        save_session(self.session)
        self.desc_input.clear()
        self.amt_input.clear()
        self.desc_input.setFocus()

        if self.on_transaction_added:
            self.on_transaction_added()

    def _remove_transaction(self, transaction):
        if not self.session:
            return
        self.session.transactions = [
            t for t in self.session.transactions if t.id != transaction.id
        ]
        save_session(self.session)
        if self.on_transaction_removed:
            self.on_transaction_removed()

    def update_session(self, session):
        self.session = session
        if self.session_header.isVisible() and session:
            self.session_header.setText(session.name)
        self._refresh_transactions()
        self._refresh_summary()
