"""Breakout brick wall."""

from __future__ import annotations

from dataclasses import dataclass

from config import MS_COLORS


@dataclass
class Brick:
    x: int
    y: int
    w: int
    h: int
    hp: int
    color: tuple[int, int, int]
    points: int
    lockin: bool = False


def build_wall(level: int, ox: int, oy: int) -> list[Brick]:
    rows = min(8, 6 + max(0, level - 1))
    cols = 10
    w, h, gap = 72, 22, 4
    bricks: list[Brick] = []
    pts = [30, 25, 20, 15, 10, 10, 10, 10]
    lock_spots = {(1, 2), (1, 7), (3, 1), (3, 8)} if level >= 2 else set()
    for r in range(rows):
        for c in range(cols):
            lockin = (r, c) in lock_spots
            bricks.append(
                Brick(
                    x=ox + c * (w + gap),
                    y=oy + 24 + r * (h + gap),
                    w=w,
                    h=h,
                    hp=2 if lockin else 1,
                    color=(70, 70, 70) if lockin else MS_COLORS[r % 4],
                    points=pts[min(r, 7)],
                    lockin=lockin,
                )
            )
    return bricks
