"""Shell states: select, attract, playing, game over, name entry."""

from __future__ import annotations

import os
import sys
from enum import Enum

import pygame

from assets_loader import LOGOS, load_font
from attract import AttractController
from cabinet import CabinetStore
from config import (
    ATTRACT_IDLE_SECONDS,
    ATTRACT_MAX_SECONDS,
    BURN_IN_IDLE_SECONDS,
    BURN_IN_SHIFT_SECONDS,
    COLOR_AMBER,
    COLOR_BG,
    COLOR_CYAN,
    COLOR_HUD,
    FOOTER_H,
    GAME_BLURBS,
    GAME_ORDER,
    GAME_OVER_HOLD,
    GAME_OVER_IDLE,
    GAME_TITLES,
    HUD_H,
    INACTIVITY_SECONDS,
    INTERNAL_H,
    INTERNAL_W,
    NAME_CHARS,
    NAME_ENTRY_SECONDS,
    NAME_MAX_LEN,
    NAME_MIN_LEN,
    GameId,
)
from game_mode import GameMode, Result
from games import MODE_CLASSES
from highscore import HighscoreStore, draw_highscore_table, name_blocked, sanitize_name
from input_map import Command, InputMap


class StateId(Enum):
    GAME_SELECT = "GAME_SELECT"
    ATTRACT_MODE = "ATTRACT_MODE"
    PLAYING = "PLAYING"
    GAME_OVER = "GAME_OVER"
    NAME_ENTRY = "NAME_ENTRY"


class Game:
    def __init__(self) -> None:
        os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
        pygame.init()
        try:
            pygame.mixer.init()
            self.audio_enabled = True
        except pygame.error:
            self.audio_enabled = False
        pygame.mouse.set_visible(False)
        self.windowed = os.environ.get("CHAOS_WINDOWED") == "1"
        flags = 0 if self.windowed else pygame.FULLSCREEN
        size = (INTERNAL_W, INTERNAL_H) if self.windowed else (0, 0)
        self.window = pygame.display.set_mode(size, flags)
        pygame.display.set_caption("CHAOS ARCADE")
        self.internal = pygame.Surface((INTERNAL_W, INTERNAL_H))
        self.clock = pygame.time.Clock()
        LOGOS.boot()
        self.input = InputMap()
        self.scores = HighscoreStore()
        self.cabinet = CabinetStore()
        self.featured = self.cabinet.load()
        self.registry: dict[GameId, GameMode] = {}
        for gid, cls in MODE_CLASSES.items():
            try:
                self.registry[gid] = cls()
            except Exception as exc:
                print(f"[shell] failed to construct {gid.value}: {exc}")
        if not self.registry:
            print("[shell] no game modes loaded", file=sys.stderr)
            raise SystemExit(1)
        if self.featured not in self.registry:
            self.featured = next(iter(self.registry))
            self.cabinet.save(self.featured)
        self.mode = self.registry[self.featured]
        self.state = StateId.GAME_SELECT
        self.attract = AttractController()
        self.font_l = load_font(42)
        self.font_m = load_font(28)
        self.font_s = load_font(22)
        self.last_input = 0.0
        self.state_t = 0.0
        self.idle_t = 0.0
        self.now = 0.0
        self.pending_score = 0
        self.pending_level = 1
        self.qualify = False
        self.pending_rank = 0
        self.name = ""
        self.alpha_i = 0
        self.flash = 0.0
        self.burn_shift = 0
        self.running = True
        self.watchdog_t = 0.0
        self.crash_wait = 0.0

    def change_state(self, new_id: StateId) -> None:
        self.state = new_id
        self.state_t = 0.0
        if new_id is StateId.GAME_SELECT:
            self.last_input = self.now
        if new_id is StateId.PLAYING:
            self.mode = self.registry[self.featured]
            self.mode.reset()
        if new_id is StateId.NAME_ENTRY:
            self.name = ""
            self.alpha_i = 0
        if new_id is StateId.ATTRACT_MODE:
            self.mode = self.registry[self.featured]
            self.mode.reset()

    def _cycle_featured(self, delta: int) -> None:
        available = [gid for gid in GAME_ORDER if gid in self.registry]
        if not available:
            return
        idx = available.index(self.featured) if self.featured in available else 0
        self.featured = available[(idx + delta) % len(available)]
        self.cabinet.save(self.featured)
        self.mode = self.registry[self.featured]
        print(f"[operator] featured={self.featured.value}")
        self.flash = 0.2

    def _handle_operator(self, cmd: Command) -> bool:
        if self.state in (StateId.PLAYING, StateId.NAME_ENTRY):
            return False
        if self.state is StateId.GAME_OVER and self.qualify:
            return False
        if cmd.operator_switch:
            self._cycle_featured(cmd.operator_switch)
            if self.state is StateId.ATTRACT_MODE:
                self.change_state(StateId.GAME_SELECT)
            return True
        return False

    def _dev_keys(self, events: list[pygame.event.Event]) -> None:
        keys = pygame.key.get_pressed()
        mapping = {
            pygame.K_1: 0,
            pygame.K_2: 1,
            pygame.K_3: 2,
            pygame.K_4: 3,
            pygame.K_5: 4,
            pygame.K_6: 5,
            pygame.K_7: 6,
        }
        allow_switch = self.state in (StateId.GAME_SELECT, StateId.ATTRACT_MODE) or (
            self.state is StateId.GAME_OVER and not self.qualify
        )
        for ev in events:
            if ev.type != pygame.KEYDOWN:
                continue
            if keys[pygame.K_LSHIFT] and ev.key == pygame.K_r:
                self.scores.clear_all()
            if ev.key == pygame.K_F11:
                self.windowed = not self.windowed
                flags = 0 if self.windowed else pygame.FULLSCREEN
                size = (INTERNAL_W, INTERNAL_H) if self.windowed else (0, 0)
                self.window = pygame.display.set_mode(size, flags)
            if allow_switch and ev.key in mapping:
                chosen = GAME_ORDER[mapping[ev.key]]
                if chosen in self.registry:
                    self.featured = chosen
                    self.cabinet.save(self.featured)
                    self.mode = self.registry[self.featured]
                    print(f"[operator] featured={self.featured.value}")
                    self.flash = 0.2
                    if self.state is StateId.ATTRACT_MODE:
                        self.change_state(StateId.GAME_SELECT)

    def on_command(self, cmd: Command) -> None:
        if cmd.quit_combo:
            self.running = False
            return
        if self._handle_operator(cmd):
            return
        if self.state is StateId.GAME_SELECT:
            if cmd.start or cmd.any_action:
                self.change_state(StateId.PLAYING)
        elif self.state is StateId.ATTRACT_MODE:
            self.change_state(StateId.GAME_SELECT)
        elif self.state is StateId.PLAYING:
            try:
                self.mode.on_command(cmd)
            except Exception as exc:
                print(f"[shell] mode command crash: {exc}")
                self.crash_wait = 2.0
                self.change_state(StateId.GAME_SELECT)
        elif self.state is StateId.GAME_OVER:
            if self.qualify and (cmd.start or cmd.any_action or self.state_t >= GAME_OVER_HOLD):
                if cmd.start or cmd.any_action:
                    self.change_state(StateId.NAME_ENTRY)
            elif not self.qualify and (cmd.start or cmd.any_action):
                self.change_state(StateId.GAME_SELECT)
        elif self.state is StateId.NAME_ENTRY:
            if cmd.dx or cmd.dy or cmd.action or cmd.start:
                self.state_t = 0.0
            self._name_command(cmd)

    def _name_command(self, cmd: Command) -> None:
        alphabet = NAME_CHARS + "<="
        if cmd.dx:
            self.alpha_i = (self.alpha_i + cmd.dx) % len(alphabet)
        if cmd.dy:
            self.alpha_i = (self.alpha_i + cmd.dy * 10) % len(alphabet)
        if cmd.action:
            ch = alphabet[self.alpha_i]
            if ch == "<":
                self.name = self.name[:-1]
            elif ch == "=":
                self._submit_name()
            elif len(self.name) < NAME_MAX_LEN:
                self.name += ch
        if cmd.start:
            self._submit_name()

    def _submit_name(self) -> None:
        clean = sanitize_name(self.name)
        if len(clean) < NAME_MIN_LEN or name_blocked(clean):
            self.flash = 1.2
            return
        self.scores.add(self.featured, clean, self.pending_score, self.pending_level)
        self.change_state(StateId.GAME_SELECT)

    def update(self, dt: float) -> None:
        if self.crash_wait > 0:
            self.crash_wait = max(0.0, self.crash_wait - dt)
            return
        self.state_t += dt
        self.now += dt
        self.flash = max(0.0, self.flash - dt)
        if self.now - self.last_input >= BURN_IN_IDLE_SECONDS:
            self.burn_shift = 2 if int((self.now - self.last_input) / BURN_IN_SHIFT_SECONDS) % 2 == 0 else -2
        else:
            self.burn_shift = 0
        if self.state is not StateId.NAME_ENTRY and self.now - self.last_input >= INACTIVITY_SECONDS:
            if self.state in (StateId.PLAYING, StateId.GAME_OVER):
                self.change_state(StateId.GAME_SELECT)
        if self.state is StateId.GAME_SELECT and self.now - self.last_input >= ATTRACT_IDLE_SECONDS:
            self.change_state(StateId.ATTRACT_MODE)
        if self.state is StateId.ATTRACT_MODE:
            if self.state_t >= ATTRACT_MAX_SECONDS:
                self.change_state(StateId.GAME_SELECT)
            else:
                self.attract.tick(self.mode, dt)
        if self.state is StateId.PLAYING:
            try:
                result = self.mode.update(dt)
            except Exception as exc:
                print(f"[shell] mode crash: {exc}")
                self.crash_wait = 2.0
                self.change_state(StateId.GAME_SELECT)
                return
            if result is Result.GAME_OVER:
                self.pending_score = self.mode.score()
                self.pending_level = self.mode.level()
                self.pending_rank = self.scores.prospective_rank(self.featured, self.pending_score)
                self.qualify = self.pending_rank > 0
                self.change_state(StateId.GAME_OVER)
        if self.state is StateId.GAME_OVER:
            if self.qualify and self.state_t >= GAME_OVER_HOLD:
                self.change_state(StateId.NAME_ENTRY)
            elif not self.qualify and self.state_t >= GAME_OVER_IDLE:
                self.change_state(StateId.GAME_SELECT)
        if self.state is StateId.NAME_ENTRY and self.state_t >= NAME_ENTRY_SECONDS:
            self.change_state(StateId.GAME_SELECT)
        self.watchdog_t += dt
        if self.watchdog_t >= 10:
            self.watchdog_t = 0
            if "NOTIFY_SOCKET" in os.environ:
                try:
                    import socket

                    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
                    sock.sendto(b"WATCHDOG=1", os.environ["NOTIFY_SOCKET"])
                    sock.close()
                except OSError:
                    pass

    def _draw_hud(self, surf: pygame.Surface) -> None:
        pygame.draw.rect(surf, COLOR_BG, (0, 0, INTERNAL_W, HUD_H))
        title = GAME_TITLES[self.featured]
        surf.blit(self.font_m.render("CHAOS ARCADE", True, COLOR_CYAN), (24, 12))
        surf.blit(self.font_m.render(title, True, COLOR_HUD), (24, 44))
        if self.state is StateId.PLAYING:
            surf.blit(self.font_m.render(f"SCORE {self.mode.score():06d}", True, COLOR_AMBER), (520, 18))
            surf.blit(self.font_m.render(f"LIVES {self.mode.lives()}", True, COLOR_HUD), (860, 18))
            surf.blit(self.font_m.render(f"LEVEL {self.mode.level()}", True, COLOR_HUD), (1040, 18))
        elif self.state is StateId.ATTRACT_MODE:
            surf.blit(self.font_m.render("DEMO", True, COLOR_AMBER), (1100, 24))

    def _draw_table(self, surf: pygame.Surface, highlight: int | None = None) -> None:
        rect = pygame.Rect(820 + self.burn_shift, 100 + self.burn_shift, 430, 500)
        blink = int(self.now * 3) % 2 == 0
        pending = self.pending_score if self.state is StateId.NAME_ENTRY else None
        draw_highscore_table(
            surf,
            self.featured,
            self.scores,
            rect,
            self.font_s,
            highlight,
            blink,
            pending,
        )

    def draw(self) -> None:
        surf = self.internal
        surf.fill(COLOR_BG)
        if self.state in (StateId.PLAYING, StateId.ATTRACT_MODE):
            try:
                self.mode.draw(surf)
            except Exception as exc:
                print(f"[shell] draw crash: {exc}")
                self.crash_wait = 2.0
                self.change_state(StateId.GAME_SELECT)
        self._draw_hud(surf)
        if self.state is not StateId.PLAYING:
            if self.state is StateId.GAME_SELECT:
                badge = LOGOS.get("logo_hero")
                surf.blit(badge, (40 + self.burn_shift, 96 + self.burn_shift))
                surf.blit(self.font_l.render(GAME_TITLES[self.featured], True, COLOR_HUD), (220, 130))
                surf.blit(self.font_m.render(GAME_BLURBS[self.featured], True, COLOR_CYAN), (220, 190))
                if int(self.now * 2) % 2 == 0:
                    surf.blit(self.font_m.render("START SPIELEN", True, COLOR_AMBER), (220, 460))
            if self.state is StateId.GAME_OVER:
                overlay = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                surf.blit(overlay, (0, 0))
                surf.blit(self.font_l.render("GAME OVER", True, COLOR_HUD), (80, 200))
                surf.blit(self.font_m.render(f"{GAME_TITLES[self.featured]}  {self.pending_score:06d}", True, COLOR_AMBER), (80, 270))
            if self.state is StateId.NAME_ENTRY:
                overlay = pygame.Surface((INTERNAL_W, INTERNAL_H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                surf.blit(overlay, (0, 0))
                surf.blit(self.font_l.render("NAME EINTRAGEN", True, COLOR_HUD), (80, 140))
                surf.blit(self.font_l.render(self.name.ljust(NAME_MAX_LEN, "_"), True, COLOR_CYAN), (80, 210))
                alphabet = NAME_CHARS + "<="
                for i, ch in enumerate(alphabet):
                    col, row = i % 13, i // 13
                    color = COLOR_AMBER if i == self.alpha_i else COLOR_HUD
                    label = "DEL" if ch == "<" else "END" if ch == "=" else ch
                    surf.blit(self.font_s.render(label, True, color), (80 + col * 40, 300 + row * 36))
                if self.flash > 0:
                    msg = "3 ZEICHEN MIN." if len(sanitize_name(self.name)) < NAME_MIN_LEN else "NAME UNGULTIG"
                    surf.blit(self.font_m.render(msg, True, COLOR_AMBER), (80, 520))
            highlight = self.pending_rank if self.state is StateId.NAME_ENTRY and self.qualify else None
            self._draw_table(surf, highlight)
        pygame.draw.rect(surf, COLOR_BG, (0, INTERNAL_H - FOOTER_H + 40, INTERNAL_W, 56))
        surf.blit(self.font_s.render("CHAOS   STICK BEWEGEN   ACTION START", True, COLOR_CYAN), (40, INTERNAL_H - 40))
        if self.flash > 0 and self.state is not StateId.NAME_ENTRY:
            pygame.draw.rect(surf, COLOR_CYAN, surf.get_rect(), 8)
        win = self.window.get_size()
        scaled = pygame.transform.smoothscale(surf, win)
        self.window.blit(scaled, (0, 0))
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT:
                    self.running = False
            cmd = self.input.poll(events)
            if cmd.activity:
                self.last_input = self.now
            self._dev_keys(events)
            self.on_command(cmd)
            self.update(dt)
            self.draw()
        pygame.quit()
