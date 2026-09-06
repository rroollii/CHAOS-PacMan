"""Keyboard + 8BitDo HID mapping."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from config import AXIS_DEADZONE, HAT_Y_INVERT, OPERATOR_BUTTONS, START_BUTTONS


@dataclass(frozen=True)
class Command:
    dx: int
    dy: int
    start: bool
    action: bool
    action_held: bool
    operator_held: bool
    operator_switch: int
    any_action: bool
    activity: bool
    quit_combo: bool


class InputMap:
    def __init__(self) -> None:
        self._joysticks: dict[int, pygame.joystick.Joystick] = {}
        self._prev_action = False
        self._prev_start = False
        self._prev_dx = 0
        self._hotplug()

    def _hotplug(self) -> None:
        try:
            count = pygame.joystick.get_count()
        except pygame.error:
            return
        for idx in range(count):
            if idx not in self._joysticks:
                try:
                    joy = pygame.joystick.Joystick(idx)
                    joy.init()
                    self._joysticks[idx] = joy
                except pygame.error:
                    continue
        dead = [i for i in self._joysticks if i >= count]
        for i in dead:
            try:
                self._joysticks[i].quit()
            except pygame.error:
                pass
            del self._joysticks[i]

    def _pad_axes(self) -> tuple[int, int, bool, bool, bool]:
        dx = dy = 0
        action_held = False
        start_held = False
        operator_held = False
        for joy in self._joysticks.values():
            try:
                hats = joy.get_numhats()
                if hats:
                    hx, hy = joy.get_hat(0)
                    if HAT_Y_INVERT:
                        hy = -hy
                    if hx:
                        dx = 1 if hx > 0 else -1
                    if hy:
                        dy = -1 if hy > 0 else 1
                if joy.get_numaxes() >= 2:
                    ax = joy.get_axis(0)
                    ay = joy.get_axis(1)
                    if abs(ax) >= AXIS_DEADZONE or abs(ay) >= AXIS_DEADZONE:
                        if abs(ax) >= abs(ay):
                            dx = 1 if ax > 0 else -1
                            dy = 0
                        else:
                            dy = 1 if ay > 0 else -1
                            dx = 0
                buttons = joy.get_numbuttons()
                for b in range(buttons):
                    if not joy.get_button(b):
                        continue
                    if b in (0, 1):
                        action_held = True
                    if b in START_BUTTONS:
                        start_held = True
                    if b in OPERATOR_BUTTONS:
                        operator_held = True
            except pygame.error:
                continue
        return dx, dy, action_held, start_held, operator_held

    def poll(self, events: list[pygame.event.Event]) -> Command:
        self._hotplug()
        keys = pygame.key.get_pressed()
        k_dx = k_dy = 0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            k_dx = 1
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            k_dx = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            k_dy = 1
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            k_dy = -1

        p_dx, p_dy, p_action, p_start, p_op = self._pad_axes()
        dx = p_dx or k_dx
        dy = p_dy or k_dy
        if dx and dy:
            if abs(p_dx) >= abs(p_dy) and p_dx:
                dy = 0
            elif p_dy:
                dx = 0
            else:
                dy = 0

        action_held = bool(p_action or keys[pygame.K_SPACE] or keys[pygame.K_LCTRL])
        start_held = bool(p_start or keys[pygame.K_RETURN])
        operator_held = bool(p_op or keys[pygame.K_LSHIFT])

        action = action_held and not self._prev_action
        start_edge = start_held and not self._prev_start
        start = start_edge and not operator_held
        if operator_held and start_held:
            start = False

        switch = 0
        if operator_held and dx and dx != self._prev_dx:
            switch = dx
            dx = 0
            start = False

        quit_combo = bool(keys[pygame.K_LSHIFT] and keys[pygame.K_q])
        any_action = action or start
        activity = bool(dx or dy or action or start or switch or operator_held)

        self._prev_action = action_held
        self._prev_start = start_held
        self._prev_dx = dx if operator_held else 0

        for ev in events:
            if ev.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                self._hotplug()

        return Command(
            dx=dx,
            dy=dy,
            start=start,
            action=action,
            action_held=action_held,
            operator_held=operator_held,
            operator_switch=switch,
            any_action=any_action,
            activity=activity,
            quit_combo=quit_combo,
        )
