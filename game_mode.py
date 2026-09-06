"""GameMode protocol shared by every title."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from config import GameId
from input_map import Command


class Result(Enum):
    CONTINUE = "CONTINUE"
    GAME_OVER = "GAME_OVER"


class GameMode(ABC):
    id: GameId

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def on_command(self, cmd: Command) -> None: ...

    @abstractmethod
    def update(self, dt: float) -> Result: ...

    @abstractmethod
    def draw(self, surf: object) -> None: ...

    @abstractmethod
    def score(self) -> int: ...

    @abstractmethod
    def level(self) -> int: ...

    @abstractmethod
    def lives(self) -> int: ...

    @abstractmethod
    def attract_tick(self, dt: float) -> None: ...
