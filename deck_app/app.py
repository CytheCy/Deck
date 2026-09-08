from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .storage import StateStore, append_card


ROOT = Path(__file__).resolve().parent.parent
ICON_DIR = next(
    (candidate for candidate in (
        ROOT / "assets" / "icons",
        ROOT / "share" / "deck" / "assets" / "icons",
        Path(sys.prefix) / "share" / "deck" / "assets" / "icons",
    ) if candidate.is_dir()),
    ROOT / "assets" / "icons",
)


class AddCardDialog(QDialog):
    def __init__(self, deck_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add a card")
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        title = QLabel(f"Add to {deck_name}")
        title.setObjectName("dialogTitle")
        hint = QLabel("Write one card. Line breaks will be saved as spaces.")
        hint.setObjectName("muted")
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Type the card text…")
        self.editor.setMinimumHeight(140)
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Save)
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addSpacing(8)
        layout.addWidget(self.editor)
        layout.addWidget(buttons)

    def _accept_if_valid(self) -> None:
        if self.editor.toPlainText().strip():
            self.accept()


class DeckWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.store = StateStore()
        self.current_path: Path | None = None
        self.cards: list[str] = []
        self.setWindowTitle("Deck")
        self.setMinimumSize(620, 500)
        self.resize(820, 650)
        self._build_ui()
        self._build_shortcuts()
        self._apply_style()
        self.refresh_decks(initial=True)

    def _icon(self, name: str) -> QIcon:
        return QIcon(str(ICON_DIR / f"{name}.svg"))

    def _tool_button(self, icon: str, label: str, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setIcon(self._icon(icon))
        button.setIconSize(QSize(22, 22))
        button.setText(label)
        button.setToolTip(tooltip)
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        button.setCursor(Qt.PointingHandCursor)
        return button

    def _build_ui(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(28, 28, 28, 22)
        outer.setSpacing(20)

        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(56, 48, 56, 42)
        self.deck_label = QLabel("DECK")
        self.deck_label.setObjectName("eyebrow")
        self.deck_label.setAlignment(Qt.AlignCenter)
        self.card_text = QLabel("Choose a folder to begin")
        self.card_text.setObjectName("cardText")
        self.card_text.setWordWrap(True)
        self.card_text.setAlignment(Qt.AlignCenter)
        self.card_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("progress")
        self.progress_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.deck_label)
        card_layout.addStretch(1)
        card_layout.addWidget(self.card_text)
        card_layout.addStretch(1)
        card_layout.addWidget(self.progress_label)
        outer.addWidget(self.card, 1)

        footer = QFrame()
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(12, 10, 12, 10)
        footer_layout.setSpacing(8)
        self.settings_button = self._tool_button("bx-cog", "Settings", "Choose the deck folder (Ctrl+,)")
        self.settings_button.clicked.connect(self.choose_folder)
        self.deck_combo = QComboBox()
        self.deck_combo.setToolTip("Choose a .deck file")
        self.deck_combo.setMinimumWidth(180)
        self.deck_combo.currentIndexChanged.connect(self._deck_changed)
        self.add_button = self._tool_button("bx-plus", "Add card", "Add a card to this deck (Ctrl+N)")
        self.add_button.clicked.connect(self.add_card)
        self.next_button = self._tool_button("bx-shuffle", "New card", "Draw a random unseen card (Space)")
        self.next_button.setObjectName("primaryTool")
        self.next_button.clicked.connect(self.draw_card)
        footer_layout.addWidget(self.settings_button)
        footer_layout.addWidget(self.deck_combo, 1)
        footer_layout.addWidget(self.add_button)
        footer_layout.addWidget(self.next_button)
        outer.addWidget(footer)
        self.setCentralWidget(central)

    def _build_shortcuts(self) -> None:
        for shortcut, callback in ((QKeySequence("Space"), self.draw_card), (QKeySequence("Ctrl+N"), self.add_card), (QKeySequence("Ctrl+,"), self.choose_folder)):
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            self.addAction(action)

    def _apply_style(self) -> None:
        QApplication.instance().setFont(QFont("Noto Sans", 10))
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #eef1f7; color: #17213a; }
            QLabel { background: transparent; }
            QFrame#card { background: #ffffff; border: 1px solid #dfe4ee; border-radius: 22px; }
            QLabel#eyebrow { color: #7c3aed; font-size: 11px; font-weight: 700; letter-spacing: 2px; }
            QLabel#cardText { color: #17213a; font-size: 27px; font-weight: 600; }
            QLabel#progress, QLabel#muted { color: #7c879f; font-size: 12px; }
            QLabel#dialogTitle { font-size: 19px; font-weight: 700; }
            QFrame#footer { background: #ffffff; border: 1px solid #dfe4ee; border-radius: 15px; }
            QToolButton { background: transparent; border: none; border-radius: 9px; padding: 9px 11px; font-weight: 600; }
            QToolButton:hover { background: #f0ecff; color: #6d28d9; }
            QToolButton:disabled { color: #aab1bf; }
            QToolButton#primaryTool { background: #7c3aed; color: white; padding: 10px 14px; }
            QToolButton#primaryTool:hover { background: #6d28d9; }
            QComboBox { background: #f6f7fb; border: 1px solid #dfe4ee; border-radius: 9px; padding: 9px 12px; }
            QComboBox:hover, QComboBox:focus { border-color: #8b5cf6; }
            QComboBox QAbstractItemView { background: white; selection-background-color: #ede9fe; selection-color: #4c1d95; }
            QPlainTextEdit { background: white; border: 1px solid #d5dae5; border-radius: 9px; padding: 10px; font-size: 14px; }
            QPlainTextEdit:focus { border-color: #8b5cf6; }
            QPushButton { padding: 8px 16px; border-radius: 7px; }
        """)

    def choose_folder(self) -> None:
        start = str(self.store.folder or Path.home())
        selected = QFileDialog.getExistingDirectory(self, "Choose the folder containing your decks", start)
        if selected:
            self.store.set_selection(Path(selected))
            self.refresh_decks(initial=False)

    def refresh_decks(self, initial: bool = False, preferred: str = "") -> None:
        decks = self.store.list_decks(self.store.folder)
        selected_name = preferred or (self.store.active_file if initial else "")
        self.deck_combo.blockSignals(True)
        self.deck_combo.clear()
        for path in decks:
            self.deck_combo.addItem(path.stem, str(path))
        index = next((i for i, path in enumerate(decks) if path.name == selected_name), 0)
        if decks:
            self.deck_combo.setCurrentIndex(index)
        self.deck_combo.blockSignals(False)
        if decks:
            self._load_deck(decks[index], draw=True)
        else:
            self.current_path = None
            self.cards = []
            self.deck_combo.setPlaceholderText("No .deck files found")
            self.card_text.setText("Choose a folder with a .deck file to begin")
            self.deck_label.setText("NO DECK SELECTED")
            self.progress_label.clear()
            self._update_controls()

    def _deck_changed(self, index: int) -> None:
        if index >= 0:
            self._load_deck(Path(self.deck_combo.itemData(index)), draw=True)

    def _load_deck(self, path: Path, draw: bool) -> None:
        try:
            cards = self.store.read_cards(path)
        except (OSError, UnicodeError) as error:
            QMessageBox.critical(self, "Could not open deck", f"{path.name} could not be read.\n\n{error}")
            return
        self.current_path, self.cards = path, cards
        self.store.set_selection(path.parent, path.name)
        self.deck_label.setText(path.stem.upper())
        self._update_controls()
        if not cards:
            self.card_text.setText("This deck is empty. Add its first card below.")
            self.progress_label.setText("0 cards")
        elif draw:
            self.draw_card()

    def _update_controls(self) -> None:
        self.add_button.setEnabled(self.current_path is not None)
        self.next_button.setEnabled(bool(self.cards))
        self.deck_combo.setEnabled(self.deck_combo.count() > 0)

    def draw_card(self) -> None:
        if not self.current_path or not self.cards:
            return
        draw = self.store.draw(self.current_path, self.cards)
        self.card_text.setText(draw.text)
        seen, total = self.store.progress(self.current_path, len(self.cards))
        prefix = "New round · " if draw.cycle_started else ""
        self.progress_label.setText(f"{prefix}{seen} of {total} seen")
        self._animate_card()

    def _animate_card(self) -> None:
        effect = self.card.graphicsEffect()
        if effect is None:
            from PySide6.QtWidgets import QGraphicsOpacityEffect
            effect = QGraphicsOpacityEffect(self.card)
            self.card.setGraphicsEffect(effect)
        self.animation = QPropertyAnimation(effect, b"opacity", self)
        self.animation.setDuration(180)
        self.animation.setStartValue(0.35)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()

    def add_card(self) -> None:
        if not self.current_path:
            return
        dialog = AddCardDialog(self.current_path.name, self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            append_card(self.current_path, dialog.editor.toPlainText())
            self.cards = self.store.read_cards(self.current_path)
            self._update_controls()
            self.card_text.setText("Card added to the deck")
            seen, total = self.store.progress(self.current_path, len(self.cards))
            self.progress_label.setText(f"{seen} of {total} seen")
        except OSError as error:
            QMessageBox.critical(self, "Could not add card", f"The card could not be saved.\n\n{error}")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Deck")
    app.setOrganizationName("Deck")
    app.setDesktopFileName("io.github.deck.Deck")
    window = DeckWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
