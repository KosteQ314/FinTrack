from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.models import Player, SplitConfig
from core.storage import list_sessions, save_session


class SidebarWidget(QWidget):
    def __init__(
        self,
        session=None,
        on_session_change=None,
        on_player_added=None,
        on_player_removed=None,
    ):
        super().__init__()
        self.session = session
        self.on_session_change = on_session_change
        self.on_player_added = on_player_added
        self.on_player_removed = on_player_removed
        self._current_split_mode = "equal"
        self._override_inputs = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        session_label = QLabel("SESSION")
        session_label.setObjectName("section_title")
        layout.addWidget(session_label)

        self.session_name_label = QLabel("No active session")
        self.session_name_label.setStyleSheet(
            "color: #c8a020; font-size: 15px; font-weight: bold;"
        )
        self.session_name_label.setWordWrap(True)
        layout.addWidget(self.session_name_label)

        self.switch_btn = QPushButton("Switch session")
        self.switch_btn.clicked.connect(self._show_session_picker)
        layout.addWidget(self.switch_btn)

        layout.addWidget(self._divider())

        players_label_row = QHBoxLayout()
        players_label = QLabel("PLAYERS")
        players_label.setObjectName("section_title")
        players_label_row.addStretch()
        layout.addLayout(players_label_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        self.players_container = QWidget()
        self.players_container.setStyleSheet("background: transparent;")
        self.players_layout = QVBoxLayout(self.players_container)
        self.players_layout.setContentsMargins(0, 0, 0, 0)
        self.players_layout.setSpacing(4)
        self.players_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.players_container)
        layout.addWidget(scroll, stretch=1)

        layout.addWidget(self._divider())

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+")
        add_btn.setFixedWidth(40)
        add_btn.setToolTip("Add player")
        add_btn.clicked.connect(self._add_player)

        remove_btn = QPushButton("−")
        remove_btn.setFixedWidth(40)
        remove_btn.setToolTip("Remove player")
        remove_btn.clicked.connect(self._remove_player)

        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._refresh_players()

    def _divider(self):
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background: rgba(100,160,255,30);")
        return line

    def _refresh_players(self):
        for i in reversed(range(self.players_layout.count())):
            item = self.players_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self._override_inputs = {}

        if not self.session or not self.session.players:
            empty = QLabel("No players yet")
            empty.setStyleSheet("color: rgba(200,200,200,60); font-size: 12px;")
            self.players_layout.addWidget(empty)
            return

        split = self.session.calculate_split()
        total = sum(split.values()) if split else 0

        for p in self.session.players:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            row.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            row.customContextMenuRequested.connect(
                lambda pos, player=p: self._player_context_menu(player)
            )
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(6)

            name_label = QLabel(p.name)
            name_label.setStyleSheet("color: #c8d6e8; font-size: 13px;")

            pct = split.get(p.name, 0)
            pct_val = (pct / total * 100) if total else 0
            share_val = int(pct)

            right = QLabel(f"{pct_val:.0f}%  {share_val:,} aUEC")
            right.setStyleSheet("color: rgba(100,160,255,160); font-size: 11px;")
            right.setAlignment(Qt.AlignmentFlag.AlignRight)

            row_layout.addWidget(name_label)
            row_layout.addStretch()
            row_layout.addWidget(right)
            self.players_layout.addWidget(row)

    def _player_context_menu(self, player):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #0d1220;
                border: 1px solid rgba(100,160,255,60);
                border-radius: 4px;
                color: #c8d6e8;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background: rgba(100,160,255,30);
            }
        """)

        set_pct = menu.addAction("Set percentage")
        set_fixed = menu.addAction("Set fixed amount")
        menu.addSeparator()
        reset_one = menu.addAction("Reset to equal")
        menu.addSeparator()
        reset_all = menu.addAction("Reset all to equal")

        action = menu.exec(self.cursor().pos())
        if not action:
            return

        if action == set_pct:
            val, ok = QInputDialog.getDouble(
                self, f"Set % for {player.name}", "Percentage:", 0, 0, 100, 1
            )
            if ok:
                overrides = dict(self.session.split_config.overrides)
                overrides[player.name.lower()] = val
                self.session.split_config = SplitConfig(
                    mode="percentage", overrides=overrides
                )
                self._current_split_mode = "percentage"
                save_session(self.session)
                if self.on_player_added:
                    self.on_player_added()

        elif action == set_fixed:
            val, ok = QInputDialog.getInt(
                self, f"Set fixed for {player.name}", "Amount (aUEC):", 0, 0, 999999999
            )
            if ok:
                overrides = dict(self.session.split_config.overrides)
                overrides[player.name.lower()] = val
                self.session.split_config = SplitConfig(
                    mode="fixed", overrides=overrides
                )
                self._current_split_mode = "fixed"
                save_session(self.session)
                if self.on_player_added:
                    self.on_player_added()

        elif action == reset_one:
            overrides = dict(self.session.split_config.overrides)
            overrides.pop(player.name.lower(), None)
            self.session.split_config = SplitConfig(
                mode=self.session.split_config.mode, overrides=overrides
            )
            save_session(self.session)
            if self.on_player_added:
                self.on_player_added()

        elif action == reset_all:
            self.session.split_config = SplitConfig(mode="equal", overrides={})
            self._current_split_mode = "equal"
            save_session(self.session)
            if self.on_player_added:
                self.on_player_added()

    def _show_session_picker(self):
        sessions = list_sessions()
        if not sessions:
            QMessageBox.information(
                self, "No sessions", "No sessions found. Create one in the CLI first."
            )
            return
        names = [s.name for s in sessions]
        name, ok = QInputDialog.getItem(
            self, "Switch session", "Select session:", names, 0, False
        )
        if ok and name:
            session = next((s for s in sessions if s.name == name), None)
            if session and self.on_session_change:
                self.on_session_change(session)

    def _add_player(self):
        if not self.session:
            QMessageBox.warning(self, "No session", "Select a session first.")
            return
        name, ok = QInputDialog.getText(self, "Add player", "Player name:")
        if ok and name.strip():
            self.session.players.append(Player(name=name.strip()))
            save_session(self.session)
            if self.on_player_added:
                self.on_player_added()

    def _remove_player(self):
        if not self.session or not self.session.players:
            return
        names = [p.name for p in self.session.players]
        name, ok = QInputDialog.getItem(
            self, "Remove player", "Select player:", names, 0, False
        )
        if ok and name:
            self.session.players = [p for p in self.session.players if p.name != name]
            save_session(self.session)
            if self.on_player_removed:
                self.on_player_removed()

    def update_session(self, session):
        self.session = session
        if session:
            self.session_name_label.setText(session.name)
            self._current_split_mode = session.split_config.mode
        else:
            self.session_name_label.setText("No active session")
            self._current_split_mode = "equal"
        self._refresh_players()
