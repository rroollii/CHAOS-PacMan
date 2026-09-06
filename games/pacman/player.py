"""Pac-Man player movement."""

from __future__ import annotations

from config import TILE_SIZE
from games.pacman import maze
from games.pacman.maze import MAZE_COLS

DIRS = {
    "LEFT": (-1, 0),
    "RIGHT": (1, 0),
    "UP": (0, -1),
    "DOWN": (0, 1),
}
TURN_EPSILON = 3
PLAYER_SPEED = 7.0 * TILE_SIZE


class Player:
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.facing = "RIGHT"
        self.queued = "RIGHT"
        self.moving = True
        self.invuln = 0.0
        self.reset()

    def reset(self) -> None:
        col, row = maze.find_tiles("P")[0]
        self.x, self.y = maze.pixel_center(col, row)
        self.facing = "RIGHT"
        self.queued = "RIGHT"
        self.moving = True
        self.invuln = 0.0

    def tile(self) -> tuple[int, int]:
        col = int((self.x - maze.OFFSET_X) // TILE_SIZE)
        row = int((self.y - maze.OFFSET_Y) // TILE_SIZE)
        return col, row

    def _center(self) -> tuple[float, float]:
        col, row = self.tile()
        return maze.pixel_center(col, row)

    def queue(self, facing: str) -> None:
        if facing in DIRS:
            self.queued = facing

    def update(self, dt: float) -> None:
        if self.invuln > 0:
            self.invuln = max(0.0, self.invuln - dt)
        cx, cy = self._center()
        if abs(self.x - cx) <= TURN_EPSILON and abs(self.y - cy) <= TURN_EPSILON:
            self.x, self.y = cx, cy
            nxt = self.queued
            ndx, ndy = DIRS[nxt]
            ncol, nrow = self.tile()[0] + ndx, self.tile()[1] + ndy
            if maze.walkable(ncol, nrow):
                self.facing = nxt
            else:
                fdx, fdy = DIRS[self.facing]
                fcol, frow = self.tile()[0] + fdx, self.tile()[1] + fdy
                if not maze.walkable(fcol, frow):
                    self.moving = False
                    return
            self.moving = True
        reverse = {"LEFT": "RIGHT", "RIGHT": "LEFT", "UP": "DOWN", "DOWN": "UP"}
        if self.queued == reverse.get(self.facing):
            self.facing = self.queued
        if not self.moving:
            return
        dx, dy = DIRS[self.facing]
        self.x += dx * PLAYER_SPEED * dt
        self.y += dy * PLAYER_SPEED * dt
        col, row = self.tile()
        if maze.tile_at(col, row) == "T":
            if col <= 0:
                self.x, self.y = maze.pixel_center(MAZE_COLS - 2, row)
            elif col >= maze.MAZE_COLS - 1:
                self.x, self.y = maze.pixel_center(1, row)

    def radius(self) -> float:
        return TILE_SIZE * 0.35
