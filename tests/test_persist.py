"""Persistence and name-filter tests (no display required)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cabinet import CabinetStore
from config import GameId, NAME_BLOCKLIST
from highscore import HighscoreStore, name_blocked, sanitize_name


class NameFilterTests(unittest.TestCase):
    def test_sanitize_uppercases_and_strips(self) -> None:
        self.assertEqual(sanitize_name("  rol-1 "), "ROL-1")

    def test_sanitize_drops_spaces_and_symbols(self) -> None:
        self.assertEqual(sanitize_name("A B!C"), "ABC")

    def test_blocklist_is_substring(self) -> None:
        self.assertTrue(NAME_BLOCKLIST)
        self.assertTrue(name_blocked("XXXY"))
        self.assertFalse(name_blocked("ROL"))


class HighscoreStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "highscores.json"
        self.store = HighscoreStore(self.path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_zero_score_never_written(self) -> None:
        self.assertEqual(self.store.add(GameId.PACMAN, "ROL", 0, 1), 0)
        self.assertEqual(self.store.table(GameId.PACMAN), [])

    def test_short_or_blocked_name_rejected(self) -> None:
        self.assertEqual(self.store.add(GameId.PACMAN, "AB", 100, 1), 0)
        self.assertEqual(self.store.add(GameId.PACMAN, "XXX", 100, 1), 0)
        self.assertEqual(self.store.table(GameId.PACMAN), [])

    def test_named_score_persists_per_game(self) -> None:
        rank = self.store.add(GameId.SNAKE, "MIA", 900, 2)
        self.assertEqual(rank, 1)
        reloaded = HighscoreStore(self.path)
        rows = reloaded.table(GameId.SNAKE)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], "MIA")
        self.assertEqual(rows[0]["score"], 900)
        self.assertEqual(reloaded.table(GameId.PACMAN), [])

    def test_top_ten_and_qualify(self) -> None:
        for i in range(10):
            self.store.add(GameId.BREAKOUT, f"P{i:02d}X", 100 + i, 1)
        self.assertFalse(self.store.qualifies(GameId.BREAKOUT, 50))
        self.assertTrue(self.store.qualifies(GameId.BREAKOUT, 109))
        self.assertEqual(self.store.prospective_rank(GameId.BREAKOUT, 200), 1)

    def test_legacy_entries_migrate_to_pacman(self) -> None:
        self.path.write_text(
            json.dumps({"entries": [{"score": 12, "level": 1, "ts": "2020-01-01T00:00:00+00:00"}]}),
            encoding="utf-8",
        )
        store = HighscoreStore(self.path)
        rows = store.table(GameId.PACMAN)
        self.assertEqual(rows[0]["name"], "---")
        self.assertEqual(rows[0]["score"], 12)
        self.assertEqual(store.table(GameId.SNAKE), [])

    def test_clear_all_keeps_file_shape(self) -> None:
        self.store.add(GameId.PACMAN, "ROL", 10, 1)
        self.store.clear_all()
        self.assertEqual(self.store.table(GameId.PACMAN), [])
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertIn("games", data)
        self.assertEqual(data["games"]["PACMAN"], [])


class CabinetStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "cabinet.json"
        self.store = CabinetStore(self.path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_default_is_pacman(self) -> None:
        self.assertEqual(self.store.load(), GameId.PACMAN)

    def test_save_and_reload(self) -> None:
        self.store.save(GameId.FROGGER)
        self.assertEqual(CabinetStore(self.path).load(), GameId.FROGGER)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["featured_game"], "FROGGER")

    def test_corrupt_file_falls_back(self) -> None:
        self.path.write_text("{not json", encoding="utf-8")
        self.assertEqual(self.store.load(), GameId.PACMAN)


if __name__ == "__main__":
    unittest.main()
