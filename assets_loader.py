"""SVG logo pipeline, fallback geometry, stick hero, Microsoft mark."""

from __future__ import annotations

from enum import Enum
from io import BytesIO
from pathlib import Path

import pygame

from config import (
    ASSETS_DIR,
    COLOR_CHAOS_GREEN,
    COLOR_CYAN,
    COLOR_HUD,
    FONT_CANDIDATES,
    MS_BLUE,
    MS_GREEN,
    MS_RED,
    MS_YELLOW,
    TILE_SIZE,
)


class LogoKind(Enum):
    FACE = "FACE"
    MARK = "MARK"
    BADGE = "BADGE"


LOGO_FILES = {
    LogoKind.FACE: ASSETS_DIR / "logo_face.svg",
    LogoKind.MARK: ASSETS_DIR / "logo_mark.svg",
    LogoKind.BADGE: ASSETS_DIR / "logo_badge.svg",
}

CACHE_SIZES = {
    "logo_hero": (LogoKind.BADGE, 160),
    "logo_tile": (LogoKind.FACE, TILE_SIZE - 4),
    "logo_dk": (LogoKind.MARK, 36),
    "logo_cannon": (LogoKind.MARK, 48),
    "logo_bubble": (LogoKind.FACE, 28),
    "logo_snake_body": (LogoKind.FACE, 24),
    "logo_ship": (LogoKind.MARK, 36),
    "logo_paddle": (LogoKind.MARK, 40),
    "logo_nest": (LogoKind.FACE, 20),
}


def _hexagon(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(6):
        ang = pygame.math.Vector2(1, 0).rotate(60 * i - 30)
        pts.append((cx + ang.x * r, cy + ang.y * r))
    return pts


def _draw_face(surf: pygame.Surface, cx: int, cy: int, size: int, eye: tuple[int, int, int], mouth: tuple[int, int, int]) -> None:
    eye_w = max(3, int(size * 0.16))
    gap = size * 0.14
    ey = cy - int(size * 0.12)
    for sign in (-1, 1):
        ex = int(cx + sign * gap)
        pygame.draw.polygon(
            surf,
            eye,
            [(ex, ey - eye_w // 2), (ex + eye_w // 2, ey), (ex, ey + eye_w // 2), (ex - eye_w // 2, ey)],
        )
    mw = int(size * 0.42)
    mh = max(2, int(size * 0.07))
    rect = pygame.Rect(0, 0, mw, mh * 2)
    rect.center = (cx, cy + int(size * 0.16))
    pygame.draw.arc(surf, mouth, rect, 3.6, 5.9, mh)


def render_fallback_logo(kind: LogoKind, size: int) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = size // 2
    if kind is LogoKind.FACE:
        _draw_face(surf, cx, cy, size, COLOR_CHAOS_GREEN, COLOR_HUD)
    elif kind is LogoKind.MARK:
        r = size * 0.42
        pygame.draw.polygon(surf, COLOR_CHAOS_GREEN, _hexagon(cx, cy, r), max(2, int(size * 0.10)))
        # opening on the right: cover a wedge
        pygame.draw.rect(surf, (0, 0, 0, 0), pygame.Rect(cx + int(size * 0.08), cy - int(size * 0.12), size, int(size * 0.24)))
        _draw_face(surf, cx + int(size * 0.04), cy, int(size * 0.72), COLOR_CHAOS_GREEN, COLOR_HUD)
    else:
        pygame.draw.polygon(surf, COLOR_HUD, _hexagon(cx, cy, size * 0.48))
        pygame.draw.polygon(surf, (11, 13, 16), _hexagon(cx, cy, size * 0.36), max(2, int(size * 0.10)))
        pygame.draw.rect(surf, COLOR_HUD, pygame.Rect(cx + int(size * 0.04), cy - int(size * 0.10), int(size * 0.28), int(size * 0.20)))
        _draw_face(surf, cx, cy, int(size * 0.62), COLOR_CHAOS_GREEN, (11, 13, 16))
    return surf


def _fit_square(src: pygame.Surface, size: int) -> pygame.Surface:
    w, h = src.get_size()
    scale = size / max(w, h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    scaled = pygame.transform.smoothscale(src, (nw, nh))
    dest = pygame.Surface((size, size), pygame.SRCALPHA)
    dest.blit(scaled, ((size - nw) // 2, (size - nh) // 2))
    return dest


class LogoAsset:
    def __init__(self) -> None:
        self.cache: dict[tuple[LogoKind, int], pygame.Surface] = {}
        self.facing: dict[tuple[LogoKind, int], dict[str, pygame.Surface]] = {}
        self.named: dict[str, pygame.Surface] = {}
        self.tinted: dict[tuple[int, tuple[int, int, int]], pygame.Surface] = {}
        self.angle_cache: dict[int, pygame.Surface] = {}

    @staticmethod
    def load(kind: LogoKind, path: Path, size: int) -> pygame.Surface:
        if path.exists():
            try:
                import cairosvg  # type: ignore

                png = cairosvg.svg2png(
                    url=str(path),
                    output_width=size * 2,
                    output_height=size * 2,
                )
                raw = pygame.image.load(BytesIO(png)).convert_alpha()
                print(f"[assets] {kind.value} loaded via cairosvg: {path}")
                return _fit_square(raw, size)
            except Exception as exc:
                print(f"[assets] {kind.value} cairosvg failed ({exc}), trying pygame")
                try:
                    raw = pygame.image.load(str(path)).convert_alpha()
                    print(f"[assets] {kind.value} loaded via pygame: {path}")
                    return _fit_square(raw, size)
                except Exception as exc2:
                    print(f"[assets] {kind.value} load failed ({exc2}), using fallback geometry")
            try:
                raw = pygame.image.load(str(path)).convert_alpha()
                print(f"[assets] {kind.value} loaded via pygame: {path}")
                return _fit_square(raw, size)
            except Exception as exc:
                print(f"[assets] {kind.value} load failed ({exc}), using fallback geometry")
        else:
            print(f"[assets] {kind.value} load failed (missing {path}), using fallback geometry")
        return render_fallback_logo(kind, size)

    def boot(self) -> None:
        for key, (kind, size) in CACHE_SIZES.items():
            surf = self.load(kind, LOGO_FILES[kind], size)
            self.cache[(kind, size)] = surf
            self.named[key] = surf
            self.facing[(kind, size)] = self._facing_set(surf)
        cannon = self.named["logo_cannon"]
        for deg in range(-80, 82, 2):
            rot = pygame.transform.rotate(cannon, -deg)
            self.angle_cache[deg] = _fit_square(rot, 56)

    def _facing_set(self, base: pygame.Surface) -> dict[str, pygame.Surface]:
        size = base.get_width()
        return {
            "RIGHT": base,
            "LEFT": pygame.transform.flip(base, True, False),
            "UP": _fit_square(pygame.transform.rotate(base, 90), size),
            "DOWN": _fit_square(pygame.transform.rotate(base, -90), size),
        }

    def get(self, key: str) -> pygame.Surface:
        return self.named[key]

    def get_facing(self, key: str, facing: str) -> pygame.Surface:
        kind, size = CACHE_SIZES[key]
        return self.facing[(kind, size)][facing]

    def tint(self, src: pygame.Surface, color: tuple[int, int, int]) -> pygame.Surface:
        ident = (id(src), color)
        if ident in self.tinted:
            return self.tinted[ident]
        tinted = src.copy()
        overlay = pygame.Surface(src.get_size(), pygame.SRCALPHA)
        overlay.fill((*color, 160))
        tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.tinted[ident] = tinted
        return tinted

    def cannon_at(self, degrees: int) -> pygame.Surface:
        snapped = int(round(degrees / 2.0) * 2)
        snapped = max(-80, min(80, snapped))
        return self.angle_cache.get(snapped, self.named["logo_cannon"])


LOGOS = LogoAsset()


def load_font(size: int) -> pygame.font.Font:
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


def tint_surface(surf: pygame.Surface, color: tuple[int, int, int]) -> pygame.Surface:
    return LOGOS.tint(surf, color)


def draw_ms_mark(surf: pygame.Surface, dest: pygame.Rect, *, label: bool = False) -> None:
    gap = max(1, int(min(dest.w, dest.h) * 0.12))
    if label and dest.h >= 22:
        mark_h = dest.h - max(8, dest.h // 3)
    else:
        mark_h = dest.h
    cell = max(1, (min(dest.w, mark_h) - gap) // 2)
    total = cell * 2 + gap
    ox = dest.x + (dest.w - total) // 2
    oy = dest.y
    colors = (MS_RED, MS_GREEN, MS_BLUE, MS_YELLOW)
    idx = 0
    for row in range(2):
        for col in range(2):
            r = pygame.Rect(ox + col * (cell + gap), oy + row * (cell + gap), cell, cell)
            pygame.draw.rect(surf, colors[idx], r)
            idx += 1
    if label and dest.h >= 22:
        font = load_font(max(8, min(14, dest.h // 3)))
        text = font.render("MICROSOFT", True, COLOR_HUD)
        tx = dest.x + (dest.w - text.get_width()) // 2
        ty = oy + total + 1
        surf.blit(text, (tx, ty))


def draw_stick_hero(
    surf: pygame.Surface,
    logo_surf: pygame.Surface,
    anchor: tuple[int, int],
    facing: str,
    pose: str,
) -> None:
    lw, lh = logo_surf.get_size()
    x, y = anchor
    surf.blit(logo_surf, (x - lw // 2, y - lh // 2))
    color = COLOR_CYAN
    width = 3 if lh >= 28 else 2
    leg = lh * 0.55
    arm = lh * 0.45
    hip = (x, y + lh // 2)
    shoulder_l = (x - lw // 2, y)
    shoulder_r = (x + lw // 2, y)
    fx = 1 if facing == "RIGHT" else -1 if facing == "LEFT" else 0

    def limb(origin: tuple[int, int], angle_deg: float, length: float) -> None:
        vec = pygame.math.Vector2(0, length).rotate(angle_deg)
        end = (int(origin[0] + vec.x), int(origin[1] + vec.y))
        pygame.draw.line(surf, color, origin, end, width)

    if pose == "WALK_A":
        limb(hip, -28, leg)
        limb(hip, 28, leg)
        limb(shoulder_l, 20 * fx - 90, arm)
        limb(shoulder_r, -20 * fx - 90, arm)
    elif pose == "WALK_B":
        limb(hip, 28, leg)
        limb(hip, -28, leg)
        limb(shoulder_l, -20 * fx - 90, arm)
        limb(shoulder_r, 20 * fx - 90, arm)
    elif pose == "JUMP":
        limb(hip, 25, leg)
        limb(hip, 35, leg)
        limb(shoulder_l, -30, arm)
        limb(shoulder_r, 30, arm)
    elif pose == "CLIMB":
        limb(hip, -18, leg)
        limb(hip, 18, leg)
        limb(shoulder_l, -70, arm)
        limb(shoulder_r, -110, arm)
    elif pose == "HOP":
        limb(hip, 40, leg)
        limb(hip, 50, leg)
        limb(shoulder_l, -20, arm)
        limb(shoulder_r, 20, arm)
    else:
        limb(hip, -8, leg)
        limb(hip, 8, leg)
        limb(shoulder_l, 15, arm * 0.6)
        limb(shoulder_r, -15, arm * 0.6)
