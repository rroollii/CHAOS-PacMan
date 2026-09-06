"""Offset-row bubble grid."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from config import MS_BLUE, MS_COLORS, MS_GREEN, MS_RED, MS_YELLOW

BUBBLE_COLS = 10
BUBBLE_D = 36
LEVEL_COLORS = {
    1: (MS_RED, MS_GREEN, MS_BLUE, MS_YELLOW),
}


def colors_for(level: int) -> tuple[tuple[int, int, int], ...]:
    if level >= 3:
        return MS_COLORS + ((59, 209, 255),)
    return MS_COLORS


@dataclass
class Cell:
    row: int
    col: int
    color: tuple[int, int, int] | None


def cell_pos(row: int, col: int, ox: int, oy: int) -> tuple[int, int]:
    odd = row % 2
    x = ox + col * BUBBLE_D + (BUBBLE_D // 2 if odd else 0) + BUBBLE_D // 2
    y = oy + row * int(BUBBLE_D * 0.86) + BUBBLE_D // 2
    return x, y


def neighbors(row: int, col: int) -> list[tuple[int, int]]:
    if row % 2 == 0:
        deltas = ((-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0))
    else:
        deltas = ((-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1))
    out = []
    for dr, dc in deltas:
        rr, cc = row + dr, col + dc
        if 0 <= cc < BUBBLE_COLS and rr >= 0:
            out.append((rr, cc))
    return out


def generate(level: int) -> dict[tuple[int, int], tuple[int, int, int]]:
    palette = colors_for(level)
    grid: dict[tuple[int, int], tuple[int, int, int]] = {}
    for _try in range(20):
        grid = {}
        for r in range(5):
            cols = BUBBLE_COLS - (1 if r % 2 else 0)
            for c in range(cols):
                grid[(r, c)] = random.choice(palette)
        if not any(_immediate_triple(grid, key) for key in grid):
            break
    return grid


def _immediate_triple(grid: dict[tuple[int, int], tuple[int, int, int]], start: tuple[int, int]) -> bool:
    color = grid[start]
    seen = {start}
    stack = [start]
    while stack:
        cur = stack.pop()
        for nb in neighbors(*cur):
            if nb in grid and grid[nb] == color and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return len(seen) >= 3


def flood(grid: dict[tuple[int, int], tuple[int, int, int]], start: tuple[int, int]) -> list[tuple[int, int]]:
    if start not in grid:
        return []
    color = grid[start]
    seen = {start}
    stack = [start]
    while stack:
        cur = stack.pop()
        for nb in neighbors(*cur):
            if nb in grid and grid[nb] == color and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return list(seen)


def hanging(grid: dict[tuple[int, int], tuple[int, int, int]]) -> list[tuple[int, int]]:
    connected: set[tuple[int, int]] = set()
    stack = [key for key in grid if key[0] == 0]
    connected.update(stack)
    while stack:
        cur = stack.pop()
        for nb in neighbors(*cur):
            if nb in grid and nb not in connected:
                connected.add(nb)
                stack.append(nb)
    return [key for key in grid if key not in connected]


def nearest_slot(
    grid: dict[tuple[int, int], tuple[int, int, int]],
    x: float,
    y: float,
    ox: int,
    oy: int,
    max_row: int = 12,
) -> tuple[int, int]:
    best = (0, 0)
    best_d = 1e9
    for r in range(max_row):
        cols = BUBBLE_COLS - (1 if r % 2 else 0)
        for c in range(cols):
            if (r, c) in grid:
                continue
            px, py = cell_pos(r, c, ox, oy)
            d = math.hypot(px - x, py - y)
            if d < best_d:
                best_d = d
                best = (r, c)
    return best
