"""1. DOMAIN RÉTEG — ENUM (Felsorolási típusok).

Miért használunk Enum-ot sima szövegek (pl. "up", "P1") helyett?
    Ha nyers stringeket írnánk mindenhova, egy apró elgépelés ("Up" vagy "p1")
    csak futásidőben, némán okozna hibát. Az Enum zárt, véges értékkészletet ad,
    amit a szerkesztő (IDE) és a típusellenőrző is ismer.

Összefüggés a többi fájllal:
    - `snake_entity.py` a `Direction`-t és `PlayerId`-t használja a kígyó leírásához.
    - `world_state.py` a `GameStatus`-szal jelzi, hogy fut-e még a meccs.
"""

from enum import Enum


class PlayerId(Enum):
    """A játékosok egyedi, elgépelésbiztos azonosítója."""

    P1 = "P1"
    P2 = "P2"


class Direction(Enum):
    """A 4 lehetséges haladási irány a 2D rácson."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class GameStatus(Enum):
    """A játék életciklusának lehetséges állapotai (állapotgép)."""

    RUNNING = "running"
    PLAYER1_WON = "player1_won"
    PLAYER2_WON = "player2_won"
    DRAW = "draw"
