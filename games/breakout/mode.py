"""BreakoutMode — smash the lock-in."""

from __future__ import annotations

import math

import pygame

from assets_loader import LOGOS, draw_ms_mark
from config import COLOR_BG, COLOR_CYAN, GameId, INTERNAL_W
from game_mode import GameMode, Result
from games.breakout.bricks import Brick, build_wall
from input_map import Command

PLAY_W, PLAY_H = 800, 560


class BreakoutMode(GameMode):
    id = GameId.BREAKOUT

    def __init__(self) -> None:
        self.ox = (INTERNAL_W - PLAY_W) // 2
        self.oy = 88
        self.paddle_x = PLAY_W / 2
        self.ball = pygame.Vector2(PLAY_W / 2, PLAY_H - 50)
        self.vel = pygame.Vector2(0, 0)
        self.stuck = True
        self.bricks: list[Brick] = []
        self._score = 0
        self._level = 1
        self._lives = 3
        self.speed = 360.0
        self._held = 0
        self.reset()

    def reset(self) -> None:
        self.paddle_x = PLAY_W / 2
        self.stuck = True
        self.vel = pygame.Vector2(0, 0)
        self._score = 0
        self._level = 1
        self._lives = 3
        self.speed = 360.0
        self._held = 0
        self.bricks = build_wall(1, self.ox, self.oy)
        self._stick_ball()

    def _stick_ball(self) -> None:
        self.ball.update(self.paddle_x, PLAY_H - 42)
        self.stuck = True
        self.vel.update(0, 0)

    def score(self) -> int:
        return self._score

    def level(self) -> int:
        return self._level

    def lives(self) -> int:
        return self._lives

    def on_command(self, cmd: Command) -> None:
        self._held = cmd.dx
        if cmd.action and self.stuck:
            offset = (self.ball.x - self.paddle_x) / 48
            ang = max(-55, min(55, offset * 55))
            self.vel = pygame.Vector2(0, -1).rotate(ang) * self.speed
            self.stuck = False

    def update(self, dt: float) -> Result:
        self.paddle_x = max(48, min(PLAY_W - 48, self.paddle_x + self._held * 420 * dt))
        if self.stuck:
            self.ball.update(self.paddle_x, PLAY_H - 42)
            return Result.CONTINUE
        self.ball += self.vel * dt
        if self.ball.x < 20:
            self.ball.x = 20
            self.vel.x *= -1
        if self.ball.x > PLAY_W - 20:
            self.ball.x = PLAY_W - 20
            self.vel.x *= -1
        if self.ball.y < 16:
            self.ball.y = 16
            self.vel.y *= -1
        paddle = pygame.Rect(self.paddle_x - 48, PLAY_H - 28, 96, 18)
        if self.vel.y > 0 and paddle.collidepoint(self.ball.x + self.ox - self.ox, self.ball.y):
            if paddle.top - 10 <= self.ball.y <= paddle.bottom:
                offset = (self.ball.x - self.paddle_x) / 48
                ang = max(-55, min(55, offset * 55))
                self.vel = pygame.Vector2(0, -1).rotate(ang) * self.vel.length()
                self.ball.y = paddle.top - 8
        for brick in list(self.bricks):
            rect = pygame.Rect(brick.x - self.ox, brick.y - self.oy, brick.w, brick.h)
            if rect.inflate(8, 8).collidepoint(self.ball.x, self.ball.y):
                brick.hp -= 1
                if abs((self.ball.x) - rect.centerx) > rect.w * 0.4:
                    self.vel.x *= -1
                else:
                    self.vel.y *= -1
                if brick.hp <= 0:
                    self._score += brick.points
                    self.bricks.remove(brick)
                    self.speed = min(620, self.speed * 1.04)
                    self.vel.scale_to_length(self.speed)
                break
        if self.ball.y > PLAY_H:
            self._lives -= 1
            if self._lives <= 0:
                return Result.GAME_OVER
            self._stick_ball()
        if not self.bricks:
            self._score += 500
            self._level += 1
            self.speed = 360 * (1.06 ** (self._level - 1))
            self.bricks = build_wall(self._level, self.ox, self.oy)
            self._stick_ball()
        return Result.CONTINUE

    def attract_tick(self, dt: float) -> None:
        self._held = 1 if self.ball.x > self.paddle_x else -1
        if self.stuck:
            self.on_command(Command(0, 0, False, True, False, False, 0, True, True, False))
        if self.update(dt) is Result.GAME_OVER:
            self.reset()

    def draw(self, surf: pygame.Surface) -> None:
        surf.fill(COLOR_BG)
        pygame.draw.rect(surf, COLOR_CYAN, (self.ox, self.oy, PLAY_W, PLAY_H), 12)
        for brick in self.bricks:
            pygame.draw.rect(surf, brick.color, (brick.x, brick.y, brick.w, brick.h))
            pygame.draw.rect(surf, (244, 241, 234), (brick.x, brick.y, brick.w, brick.h), 2)
            if brick.lockin:
                draw_ms_mark(surf, pygame.Rect(brick.x + 16, brick.y + 2, brick.w - 32, brick.h - 4))
        paddle = LOGOS.get("logo_paddle")
        px = self.ox + int(self.paddle_x)
        py = self.oy + PLAY_H - 20
        pygame.draw.rect(surf, COLOR_CYAN, (px - 48, py - 8, 96, 18), border_radius=4)
        surf.blit(paddle, paddle.get_rect(center=(px, py)))
        ball = LOGOS.get("logo_bubble")
        surf.blit(ball, ball.get_rect(center=(self.ox + int(self.ball.x), self.oy + int(self.ball.y))))
