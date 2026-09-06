"""PacmanMode — shelfware maze."""

from __future__ import annotations

import math

import pygame

from assets_loader import LOGOS, draw_ms_mark
from config import COLOR_BG, COLOR_CYAN, COLOR_HUD, COLOR_MAZE_FILL, GameId, TILE_SIZE
from game_mode import GameMode, Result
from games.pacman import maze
from games.pacman.ghosts import Ghost, GhostState, make_ghosts
from games.pacman.player import DIRS, Player
from input_map import Command


class PacmanMode(GameMode):
    id = GameId.PACMAN

    def __init__(self) -> None:
        self.player = Player()
        self.ghosts: list[Ghost] = []
        self.dots: set[tuple[int, int]] = set()
        self.powers: set[tuple[int, int]] = set()
        self._score = 0
        self._level = 1
        self._lives = 3
        self.frightened = 0.0
        self.eat_combo = 0
        self.elapsed = 0.0
        self._attract_dir = 1
        self.reset()

    def reset(self) -> None:
        self.player.reset()
        self.ghosts = make_ghosts()
        self.dots = set(maze.find_tiles("."))
        self.powers = set(maze.find_tiles("O"))
        self._score = 0
        self._level = 1
        self._lives = 3
        self.frightened = 0.0
        self.eat_combo = 0
        self.elapsed = 0.0

    def _reload_maze(self) -> None:
        self.player.reset()
        self.ghosts = make_ghosts()
        self.dots = set(maze.find_tiles("."))
        self.powers = set(maze.find_tiles("O"))
        self.frightened = 0.0
        self.eat_combo = 0

    def score(self) -> int:
        return self._score

    def level(self) -> int:
        return self._level

    def lives(self) -> int:
        return self._lives

    def on_command(self, cmd: Command) -> None:
        if cmd.dx < 0:
            self.player.queue("LEFT")
        elif cmd.dx > 0:
            self.player.queue("RIGHT")
        elif cmd.dy < 0:
            self.player.queue("UP")
        elif cmd.dy > 0:
            self.player.queue("DOWN")

    def _fright_time(self) -> float:
        return max(2.0, 6.0 - 0.5 * (self._level - 1))

    def update(self, dt: float) -> Result:
        self.elapsed += dt
        if self.frightened > 0:
            self.frightened = max(0.0, self.frightened - dt)
        self.player.update(dt)
        col, row = self.player.tile()
        if (col, row) in self.dots:
            self.dots.remove((col, row))
            self._score += 10
        if (col, row) in self.powers:
            self.powers.remove((col, row))
            self._score += 50
            self.frightened = self._fright_time()
            self.eat_combo = 0
        blinky = self.ghosts[0]
        dots_left = len(self.dots) + len(self.powers)
        for ghost in self.ghosts:
            ghost.update(dt, self.player, blinky, dots_left, self.frightened > 0, self.elapsed)
            if math.hypot(ghost.x - self.player.x, ghost.y - self.player.y) < TILE_SIZE * 0.7:
                if ghost.state is GhostState.FRIGHTENED:
                    ghost.state = GhostState.EATEN
                    self.eat_combo = min(3, self.eat_combo + 1)
                    self._score += (200, 400, 800, 1600)[self.eat_combo]
                elif ghost.state not in (GhostState.EATEN, GhostState.HOUSE) and self.player.invuln <= 0:
                    self._lives -= 1
                    if self._lives <= 0:
                        return Result.GAME_OVER
                    self.player.reset()
                    self.player.invuln = 2.0
                    for g in self.ghosts:
                        g.reset()
                    break
        if not self.dots and not self.powers:
            self._score += 500
            self._level += 1
            self._reload_maze()
        return Result.CONTINUE

    def attract_tick(self, dt: float) -> None:
        self.player.queue("RIGHT" if self._attract_dir > 0 else "LEFT")
        result = self.update(dt)
        col, _ = self.player.tile()
        if col <= 1:
            self._attract_dir = 1
        if col >= maze.MAZE_COLS - 2:
            self._attract_dir = -1
        if result is Result.GAME_OVER:
            self.reset()

    def draw(self, surf: pygame.Surface) -> None:
        pygame.draw.rect(surf, COLOR_BG, surf.get_rect())
        for r, line in enumerate(maze.LAYOUT):
            for c, ch in enumerate(line):
                x = maze.OFFSET_X + c * TILE_SIZE
                y = maze.OFFSET_Y + r * TILE_SIZE
                if ch == "#":
                    pygame.draw.rect(surf, COLOR_CYAN, (x, y, TILE_SIZE, TILE_SIZE), 2)
                    pygame.draw.rect(surf, COLOR_MAZE_FILL, (x + 3, y + 3, TILE_SIZE - 6, TILE_SIZE - 6))
                elif ch == "-":
                    pygame.draw.line(surf, COLOR_HUD, (x, y + TILE_SIZE // 2), (x + TILE_SIZE, y + TILE_SIZE // 2), 2)
        for c, r in self.dots:
            cx, cy = maze.pixel_center(c, r)
            pygame.draw.circle(surf, COLOR_HUD, (int(cx), int(cy)), 3)
        for c, r in self.powers:
            cx, cy = maze.pixel_center(c, r)
            draw_ms_mark(surf, pygame.Rect(int(cx) - 8, int(cy) - 8, 16, 16))
        house = maze.find_tiles("G")
        if house:
            hx = maze.OFFSET_X + min(h[0] for h in house) * TILE_SIZE
            hy = maze.OFFSET_Y + min(h[1] for h in house) * TILE_SIZE - 28
            hw = (max(h[0] for h in house) - min(h[0] for h in house) + 1) * TILE_SIZE
            draw_ms_mark(surf, pygame.Rect(hx, hy, max(72, hw), 26), label=True)
        facing = self.player.facing
        logo = LOGOS.get_facing("logo_tile", facing)
        if self.player.invuln <= 0 or int(self.player.invuln * 8) % 2 == 0:
            surf.blit(logo, (int(self.player.x - logo.get_width() / 2), int(self.player.y - logo.get_height() / 2)))
        names = {"BLINKY": "AUDITOR", "PINKY": "TRUEUP", "INKY": "SKUWIRR", "CLYDE": "SHELFWARE"}
        for ghost in self.ghosts:
            color = (45, 226, 230) if ghost.state is GhostState.FRIGHTENED else ghost.color
            if ghost.state is GhostState.EATEN:
                color = COLOR_HUD
            pygame.draw.rect(surf, color, (int(ghost.x) - 12, int(ghost.y) - 14, 20, 26), border_radius=3)
            pygame.draw.circle(surf, COLOR_HUD, (int(ghost.x) - 6, int(ghost.y) - 10), 3)
            pygame.draw.circle(surf, COLOR_HUD, (int(ghost.x) + 4, int(ghost.y) - 10), 3)
            draw_ms_mark(surf, pygame.Rect(int(ghost.x) - 3, int(ghost.y) - 2, 6, 6))
            _ = names
