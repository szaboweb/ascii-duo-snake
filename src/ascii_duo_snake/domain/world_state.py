"""1. DOMAIN RÉTEG — STATE (Single Source of Truth & Composition).

Mi az a Single Source of Truth (SSOT — Egyetlen Igazságforrás)?
    A játék TELJES aktuális állapota ebben az egyetlen `WorldState` objektumban él.
    Nincs szétszórva külön pozíció a képernyőn és külön állapot a motorban —
    így két komponens sosem tud ellentmondani egymásnak.

Mi az a Kompozíció (HAS-A kapcsolat)?
    A `WorldState` nem örököl a `SnakeEntity`-ből, hanem *tartalmaz* egy
    `SnakeEntity` objektumot (`player_one_snake`). Ez rugalmasabb és tisztább,
    mint a mély öröklési hierarchia.
"""

from dataclasses import dataclass

from .game_enums import GameStatus
from .snake_entity import SnakeEntity


@dataclass(frozen=True)
class WorldState:
    """A játékvilág teljes, megváltoztathatatlan pillanatképe egy adott tick-ben.

    Attribútumok:
        room_width, room_height: A szoba külső mérete (a 0-s és room_width-1 / room_height-1 sorok a falak).
        player_one_snake: Az 1-es játékos kígyója.
        status: Fut-e még a játék, vagy eldőlt a meccs.
        tick: Diszkrét időlépések számlálója (0, 1, 2, ...).
    """

    room_width: int
    room_height: int
    player_one_snake: SnakeEntity
    status: GameStatus = GameStatus.RUNNING
    tick: int = 0
