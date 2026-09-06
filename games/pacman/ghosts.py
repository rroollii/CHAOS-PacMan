"""Four auditor personalities."""

from __future__ import annotations

import math
from enum import Enum

from config import COLOR_ORANGE, COLOR_PINK, COLOR_SKY, MS_RED, TILE_SIZE
from games.pacman import maze
from games.pacman.maze import MAZE_COLS
from games.pacman.player import DIRS, Player

GHOST_SPEED = 6.2 * TILE_SIZE
TUNNEL_FACTOR = 0.6
LEAVE_TIMES = (0.2, 0.8, 2.4, 4.0)
TIE_BREAK = ("UP", "LEFT", "DOWN", "RIGHT")


class GhostState(Enum):
    HOUSE = "HOUSE"
    LEAVE = "LEAVE"
    SCATTER = "SCATTER"
    CHASE = "CHASE"
    FRIGHTENED = "FRIGHTENED"
    EATEN = "EATEN"


class Ghost:
    def __init__(self, name: str, color: tuple[int, int, int], scatter: tuple[int, int], leave_t: float) -> None:
        self.name = name
        self.color = color
        self.scatter = scatter
        self.leave_t = leave_t
        self.state = GhostState.HOUSE
        self.facing = "LEFT"
        self.x = 0.0
        self.y = 0.0
        self.home = (0, 0)
        self.timer = 0.0
        self.reset()

    def reset(self) -> None:
        houses = maze.find_tiles("G")
        self.home = houses[len(houses) // 2] if houses else (10, 10)
        self.x, self.y = maze.pixel_center(*self.home)
        self.state = GhostState.HOUSE
        self.facing = "LEFT"
        self.timer = 0.0

    def tile(self) -> tuple[int, int]:
        return int((self.x - maze.OFFSET_X) // TILE_SIZE), int((self.y - maze.OFFSET_Y) // TILE_SIZE)

    def target(self, player: Player, blinky: Ghost | None, dots_left: int) -> tuple[int, int]:
        pc, pr = player.tile()
        pdx, pdy = DIRS[player.facing]
        if self.state is GhostState.EATEN:
            return self.home
        if self.state is GhostState.SCATTER:
            return self.scatter
        if self.name == "BLINKY":
            if dots_left < 20:
                return pc, pr
            return pc, pr
        if self.name == "PINKY":
            return pc + pdx * 4, pr + pdy * 4
        if self.name == "INKY":
            pivot = (pc + pdx * 2, pr + pdy * 2)
            if blinky is None:
                return pivot
            bc, br = blinky.tile()
            return pivot[0] * 2 - bc, pivot[1] * 2 - br
        # CLYDE
        dist = math.hypot(pc - self.tile()[0], pr - self.tile()[1])
        if dist > 8:
            return pc, pr
        return self.scatter

    def _choose(self, player: Player, blinky: Ghost | None, dots_left: int) -> None:
        col, row = self.tile()
        cx, cy = maze.pixel_center(col, row)
        if abs(self.x - cx) > 2 or abs(self.y - cy) > 2:
            return
        self.x, self.y = cx, cy
        if self.state is GhostState.FRIGHTENED:
            options = [d for d in TIE_BREAK if d != {"LEFT": "RIGHT", "RIGHT": "LEFT", "UP": "DOWN", "DOWN": "UP"}.get(self.facing)]
            valid = []
            for d in options:
                ndx, ndy = DIRS[d]
                if maze.walkable(col + ndx, row + ndy, allow_gate=self.state is GhostState.LEAVE):
                    valid.append(d)
            if valid:
                self.facing = valid[0]
            return
        target = self.target(player, blinky, dots_left)
        reverse = {"LEFT": "RIGHT", "RIGHT": "LEFT", "UP": "DOWN", "DOWN": "UP"}.get(self.facing)
        best = self.facing
        best_d = 1e9
        for d in TIE_BREAK:
            if d == reverse and self.state not in (GhostState.LEAVE, GhostState.EATEN):
                continue
            ndx, ndy = DIRS[d]
            nc, nr = col + ndx, row + ndy
            allow = self.state in (GhostState.LEAVE, GhostState.EATEN)
            if not maze.walkable(nc, nr, allow_gate=allow):
                continue
            dist = math.hypot(nc - target[0], nr - target[1])
            if dist < best_d:
                best_d = dist
                best = d
        self.facing = best

    def update(self, dt: float, player: Player, blinky: Ghost | None, dots_left: int, frightened: bool, elapsed: float) -> None:
        self.timer += dt
        if self.state is GhostState.HOUSE and self.timer >= self.leave_t:
            self.state = GhostState.LEAVE
        if self.state is GhostState.LEAVE:
            gate = maze.find_tiles("-")
            if gate and self.tile()[1] <= gate[0][1]:
                self.state = GhostState.SCATTER
        if self.state is GhostState.EATEN and self.tile() == self.home:
            self.state = GhostState.LEAVE
        if frightened and self.state in (GhostState.CHASE, GhostState.SCATTER, GhostState.LEAVE):
            self.state = GhostState.FRIGHTENED
        if not frightened and self.state is GhostState.FRIGHTENED:
            self.state = GhostState.CHASE
        if self.state in (GhostState.SCATTER, GhostState.CHASE):
            # scatter schedule level-agnostic enough
            cycle = elapsed % 27.0
            self.state = GhostState.SCATTER if cycle < 7 or 27 > cycle > 20 else GhostState.CHASE
        self._choose(player, blinky, dots_left)
        speed = GHOST_SPEED
        if maze.tile_at(*self.tile()) == "T":
            speed *= TUNNEL_FACTOR
        if self.state is GhostState.FRIGHTENED:
            speed *= 0.55
        if self.state is GhostState.EATEN:
            speed *= 1.6
        dx, dy = DIRS[self.facing]
        self.x += dx * speed * dt
        self.y += dy * speed * dt
        col, row = self.tile()
        if maze.tile_at(col, row) == "T":
            if col <= 0:
                self.x, self.y = maze.pixel_center(MAZE_COLS - 2, row)
            elif col >= maze.MAZE_COLS - 1:
                self.x, self.y = maze.pixel_center(1, row)


def make_ghosts() -> list[Ghost]:
    return [
        Ghost("BLINKY", MS_RED, (20, 0), LEAVE_TIMES[0]),
        Ghost("PINKY", COLOR_PINK, (0, 0), LEAVE_TIMES[1]),
        Ghost("INKY", COLOR_SKY, (20, 16), LEAVE_TIMES[2]),
        Ghost("CLYDE", COLOR_ORANGE, (0, 16), LEAVE_TIMES[3]),
    ]
