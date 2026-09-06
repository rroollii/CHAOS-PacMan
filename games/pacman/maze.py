"""21x17 neon maze."""

from __future__ import annotations

from config import INTERNAL_W, TILE_SIZE

MAZE_COLS = 21
MAZE_ROWS = 17
MAZE_W = MAZE_COLS * TILE_SIZE
MAZE_H = MAZE_ROWS * TILE_SIZE
OFFSET_X = (INTERNAL_W - MAZE_W) // 2
OFFSET_Y = 80

LAYOUT = [
    "#####################",
    "#.........#.........#",
    "#O##.###.#.###.##O#.#",
    "#...................#",
    "###.#.#####.#.#######",
    "#...#...#...#.......#",
    "#.#.###.#.###.#.#.#.#",
    "#.#...............#.#",
    "#.###.##---##.###.#.#",
    "#.....#.GGG.#.......#",
    "#####.#GGGGG#.#######",
    "T     #.....#       T",
    "#####.#######.#######",
    "#........P..........#",
    "#O##.###.#.###.##O#.#",
    "#...................#",
    "#####################",
]

assert len(LAYOUT) == MAZE_ROWS
assert all(len(line) == MAZE_COLS for line in LAYOUT)


def tile_at(col: int, row: int) -> str:
    if row < 0 or row >= MAZE_ROWS:
        return "#"
    if col < 0 or col >= MAZE_COLS:
        return "T" if "T" in LAYOUT[max(0, min(MAZE_ROWS - 1, row))] else "#"
    return LAYOUT[row][col]


def is_wall(col: int, row: int) -> bool:
    return tile_at(col, row) == "#"


def is_gate(col: int, row: int) -> bool:
    return tile_at(col, row) == "-"


def walkable(col: int, row: int, allow_gate: bool = False) -> bool:
    ch = tile_at(col, row)
    if ch == "#":
        return False
    if ch == "-" and not allow_gate:
        return False
    return True


def pixel_center(col: int, row: int) -> tuple[float, float]:
    return OFFSET_X + col * TILE_SIZE + TILE_SIZE / 2, OFFSET_Y + row * TILE_SIZE + TILE_SIZE / 2


def find_tiles(ch: str) -> list[tuple[int, int]]:
    found: list[tuple[int, int]] = []
    for r, line in enumerate(LAYOUT):
        for c, token in enumerate(line):
            if token == ch:
                found.append((c, r))
    return found
