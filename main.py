#!/usr/bin/env python3
"""CHAOS Arcade entry point."""

from __future__ import annotations

import os

os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

from states import Game  # noqa: E402


def main() -> None:
    Game().run()


if __name__ == "__main__":
    main()
