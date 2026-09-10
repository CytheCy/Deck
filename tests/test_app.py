import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from deck_app.app import DeckWindow
from deck_app.storage import StateStore


class ExternalOpenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(["deck-tests"])

    def test_external_deck_does_not_replace_saved_folder_or_selection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            saved_folder = root / "saved"
            saved_folder.mkdir()
            (saved_folder / "saved.deck").write_text("saved card\n", encoding="utf-8")
            external = root / "external.deck"
            external.write_text("external card\n", encoding="utf-8")

            with patch.dict(os.environ, {"XDG_DATA_HOME": str(root / "data")}):
                StateStore().set_selection(saved_folder, "saved.deck")
                window = DeckWindow(external)
                reloaded = StateStore()

                self.assertEqual(window.current_path, external.resolve())
                self.assertEqual(reloaded.folder, saved_folder.resolve())
                self.assertEqual(reloaded.active_file, "saved.deck")
                window.close()

                normal_window = DeckWindow()
                self.assertEqual(
                    normal_window.current_path,
                    (saved_folder / "saved.deck").resolve(),
                )
                normal_window.close()

    def test_right_arrow_draws_the_next_card(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            deck = root / "cards.deck"
            deck.write_text("first\nsecond\n", encoding="utf-8")

            with patch.dict(os.environ, {"XDG_DATA_HOME": str(root / "data")}):
                window = DeckWindow(deck)
                window.show()
                window.activateWindow()
                self.app.processEvents()

                QTest.keyClick(window, Qt.Key_Right)
                self.app.processEvents()

                self.assertEqual(window.store.progress(deck, 2), (2, 2))
                window.close()


if __name__ == "__main__":
    unittest.main()
