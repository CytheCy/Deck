import random
import tempfile
import unittest
from pathlib import Path

from deck_app.storage import StateStore, append_card, replace_card


class StateStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.deck = self.root / "deck.deck"
        self.deck.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
        self.store = StateStore(self.root / "data")

    def tearDown(self):
        self.temp.cleanup()

    def test_each_card_is_drawn_once_before_new_cycle(self):
        cards = self.store.read_cards(self.deck)
        draws = [self.store.draw(self.deck, cards, random.Random(7)) for _ in cards]
        self.assertEqual({draw.index for draw in draws}, {0, 1, 2})
        next_draw = self.store.draw(self.deck, cards, random.Random(7))
        self.assertTrue(next_draw.cycle_started)
        self.assertEqual(self.store.progress(self.deck, 3), (1, 3))

    def test_history_survives_reload(self):
        cards = self.store.read_cards(self.deck)
        first = self.store.draw(self.deck, cards, random.Random(2))
        reloaded = StateStore(self.root / "data")
        second = reloaded.draw(self.deck, cards, random.Random(2))
        self.assertNotEqual(first.index, second.index)

    def test_appending_keeps_prior_history(self):
        cards = self.store.read_cards(self.deck)
        first = self.store.draw(self.deck, cards, random.Random(3))
        append_card(self.deck, "delta")
        new_cards = self.store.read_cards(self.deck)
        self.store.draw(self.deck, new_cards, random.Random(3))
        seen, total = self.store.progress(self.deck, 4)
        self.assertEqual((seen, total), (2, 4))
        self.assertEqual(new_cards[-1], "delta")
        self.assertIn(first.index, self.store.data["decks"][str(self.deck.resolve())]["seen"])

    def test_editing_existing_cards_resets_history(self):
        cards = self.store.read_cards(self.deck)
        self.store.draw(self.deck, cards, random.Random(1))
        edited = ["changed", "beta", "gamma"]
        self.store.draw(self.deck, edited, random.Random(1))
        self.assertEqual(self.store.progress(self.deck, 3), (1, 3))

    def test_replacing_card_preserves_layout_and_seen_history(self):
        self.deck.write_text("alpha\r\n\r\nbeta\r\n", encoding="utf-8")
        cards = self.store.read_cards(self.deck)
        first = self.store.draw(self.deck, cards, random.Random(1))
        replacement = replace_card(self.deck, first.index, " updated card ", expected=first.text)
        edited_cards = self.store.read_cards(self.deck)
        self.store.record_edit(self.deck, edited_cards, first.index)

        self.assertEqual(replacement, "updated card")
        self.assertEqual(self.deck.read_bytes().count(b"\r\n"), 3)
        self.assertIn(b"\r\n\r\n", self.deck.read_bytes())
        self.assertEqual(self.store.progress(self.deck, 2), (1, 2))
        self.assertEqual(edited_cards[first.index], "updated card")

    def test_utf8_bom_and_blank_lines(self):
        self.deck.write_text("\ufeffone\n\n two \n", encoding="utf-8")
        self.assertEqual(self.store.read_cards(self.deck), ["one", " two "])

    def test_only_deck_files_are_discovered(self):
        (self.root / "notes.txt").write_text("not a deck\n", encoding="utf-8")
        (self.root / "SECOND.DECK").write_text("a card\n", encoding="utf-8")
        self.assertEqual(
            [path.name for path in self.store.list_decks(self.root)],
            ["deck.deck", "SECOND.DECK"],
        )

    def test_theme_preference_survives_reload(self):
        self.store.set_preferences(self.root, "dark")
        reloaded = StateStore(self.root / "data")
        self.assertEqual(reloaded.theme, "dark")
        self.assertEqual(reloaded.folder, self.root)

    def test_invalid_saved_theme_falls_back_to_light(self):
        self.store.data["theme"] = "sepia"
        self.assertEqual(self.store.theme, "light")


if __name__ == "__main__":
    unittest.main()
