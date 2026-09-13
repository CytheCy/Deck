from __future__ import annotations

import json
import os
import random
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


@dataclass(frozen=True)
class Draw:
    index: int
    text: str
    cycle_started: bool = False


def default_data_dir() -> Path:
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "deck"


class StateStore:
    """JSON-backed preferences and per-file draw history.

    Histories are keyed by the canonical file path. Each entry also stores a copy
    of the lines from the last draw, which lets us keep history after appending
    cards while safely resetting it after existing cards are edited or reordered.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else default_data_dir()
        self.path = self.data_dir / "state.json"
        self.data: dict[str, Any] = {
            "version": 1,
            "folder": "",
            "active_file": "",
            "theme": "light",
            "decks": {},
        }
        self._load()

    def _load(self) -> None:
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.data.update(loaded)
        except (OSError, json.JSONDecodeError):
            pass
        if not isinstance(self.data.get("decks"), dict):
            self.data["decks"] = {}

    def save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix="state-", suffix=".json", dir=self.data_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        except Exception:
            try:
                os.unlink(temporary)
            except OSError:
                pass
            raise

    @property
    def folder(self) -> Path | None:
        value = self.data.get("folder", "")
        return Path(value) if value else None

    @property
    def active_file(self) -> str:
        return str(self.data.get("active_file", ""))

    @property
    def theme(self) -> str:
        value = self.data.get("theme", "light")
        return value if value in ("light", "dark") else "light"

    def set_selection(self, folder: Path, active_file: str = "") -> None:
        self.data["folder"] = str(folder.resolve())
        self.data["active_file"] = active_file
        self.save()

    def set_preferences(self, folder: Path | None, theme: str) -> None:
        if theme not in ("light", "dark"):
            raise ValueError(f"Unsupported theme: {theme}")
        self.data["folder"] = str(folder.resolve()) if folder else ""
        self.data["theme"] = theme
        self.save()

    @staticmethod
    def read_cards(path: Path) -> list[str]:
        # A blank line is not a useful card; whitespace around real cards is kept.
        with path.open("r", encoding="utf-8-sig") as handle:
            return [line.rstrip("\r\n") for line in handle if line.strip()]

    @staticmethod
    def list_decks(folder: Path | None) -> list[Path]:
        if not folder or not folder.is_dir():
            return []
        return sorted(
            (path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".deck"),
            key=lambda path: path.name.casefold(),
        )

    def draw(self, path: Path, cards: Sequence[str], rng: random.Random | None = None) -> Draw:
        if not cards:
            raise ValueError("Cannot draw from an empty deck")

        key = str(path.resolve())
        record = self.data["decks"].get(key, {})
        old_cards = record.get("cards", [])
        seen = record.get("seen", [])
        if not isinstance(old_cards, list) or not isinstance(seen, list):
            old_cards, seen = [], []

        # Appending leaves all old indices valid. Any other content change starts
        # a fresh cycle because line numbers no longer identify the same cards.
        is_append = len(cards) >= len(old_cards) and list(cards[: len(old_cards)]) == old_cards
        if old_cards and not is_append:
            seen = []
        seen_set = {index for index in seen if isinstance(index, int) and 0 <= index < len(cards)}

        cycle_started = len(seen_set) >= len(cards)
        if cycle_started:
            seen_set.clear()

        remaining = [index for index in range(len(cards)) if index not in seen_set]
        index = (rng or random.SystemRandom()).choice(remaining)
        seen_set.add(index)
        self.data["decks"][key] = {"cards": list(cards), "seen": sorted(seen_set)}
        self.save()
        return Draw(index=index, text=cards[index], cycle_started=cycle_started)

    def progress(self, path: Path, total: int) -> tuple[int, int]:
        record = self.data["decks"].get(str(path.resolve()), {})
        seen = record.get("seen", [])
        valid = {index for index in seen if isinstance(index, int) and 0 <= index < total}
        return len(valid), total

    def record_edit(self, path: Path, cards: Sequence[str], edited_index: int) -> None:
        """Update a deck snapshot while retaining valid draw history."""
        key = str(path.resolve())
        record = self.data["decks"].get(key, {})
        old_cards = record.get("cards", [])
        seen = record.get("seen", [])
        only_selected_card_changed = (
            isinstance(old_cards, list)
            and len(old_cards) == len(cards)
            and all(
                old == new
                for index, (old, new) in enumerate(zip(old_cards, cards))
                if index != edited_index
            )
        )
        if only_selected_card_changed and isinstance(seen, list):
            seen_set = {
                index
                for index in seen
                if isinstance(index, int) and 0 <= index < len(cards)
            }
        else:
            seen_set = set()
        seen_set.add(edited_index)
        self.data["decks"][key] = {"cards": list(cards), "seen": sorted(seen_set)}
        self.save()

    def record_removal(self, path: Path, cards: Sequence[str], removed_index: int) -> None:
        """Update a deck snapshot and shift seen indices past a removed card."""
        key = str(path.resolve())
        record = self.data["decks"].get(key, {})
        old_cards = record.get("cards", [])
        seen = record.get("seen", [])
        expected_cards = (
            old_cards[:removed_index] + old_cards[removed_index + 1:]
            if isinstance(old_cards, list) and 0 <= removed_index < len(old_cards)
            else None
        )
        if expected_cards == list(cards) and isinstance(seen, list):
            seen_set = {
                index if index < removed_index else index - 1
                for index in seen
                if isinstance(index, int) and 0 <= index < len(old_cards) and index != removed_index
            }
        else:
            seen_set = set()
        self.data["decks"][key] = {"cards": list(cards), "seen": sorted(seen_set)}
        self.save()


def append_card(path: Path, text: str) -> None:
    clean = " ".join(part.strip() for part in text.splitlines() if part.strip())
    if not clean:
        raise ValueError("Card text cannot be empty")
    needs_newline = path.exists() and path.stat().st_size > 0
    if needs_newline:
        with path.open("rb") as check:
            check.seek(-1, os.SEEK_END)
            needs_newline = check.read(1) not in (b"\n", b"\r")
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        if needs_newline:
            handle.write("\n")
        handle.write(clean + "\n")


def replace_card(path: Path, index: int, text: str, expected: str | None = None) -> str:
    """Replace one nonblank card line while preserving the file's other lines."""
    clean = " ".join(part.strip() for part in text.splitlines() if part.strip())
    if not clean:
        raise ValueError("Card text cannot be empty")

    has_bom = path.read_bytes().startswith(b"\xef\xbb\xbf")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        raw = handle.read()
    lines = raw.splitlines(keepends=True)
    card_lines = [
        line_index
        for line_index, line in enumerate(lines)
        if line.rstrip("\r\n").strip()
    ]
    if not 0 <= index < len(card_lines):
        raise IndexError("Card is no longer present in the deck")

    line_index = card_lines[index]
    old_text = lines[line_index].rstrip("\r\n")
    if expected is not None and old_text != expected:
        raise ValueError("The deck changed since this card was drawn")
    ending = lines[line_index][len(old_text):]
    lines[line_index] = clean + ending
    with path.open("w", encoding="utf-8-sig" if has_bom else "utf-8", newline="") as handle:
        handle.write("".join(lines))
    return clean


def remove_card(path: Path, index: int, expected: str | None = None) -> str:
    """Remove one nonblank card line while preserving all other file content."""
    has_bom = path.read_bytes().startswith(b"\xef\xbb\xbf")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        raw = handle.read()
    lines = raw.splitlines(keepends=True)
    card_lines = [
        line_index
        for line_index, line in enumerate(lines)
        if line.rstrip("\r\n").strip()
    ]
    if not 0 <= index < len(card_lines):
        raise IndexError("Card is no longer present in the deck")

    line_index = card_lines[index]
    old_text = lines[line_index].rstrip("\r\n")
    if expected is not None and old_text != expected:
        raise ValueError("The deck changed since this card was drawn")
    del lines[line_index]
    with path.open("w", encoding="utf-8-sig" if has_bom else "utf-8", newline="") as handle:
        handle.write("".join(lines))
    return old_text
