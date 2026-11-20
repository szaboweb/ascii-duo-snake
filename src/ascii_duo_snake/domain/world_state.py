"""1. DOMAIN RÉTEG — STATE (Single Source of Truth & Composition).

Mi az a Single Source of Truth (SSOT — Egyetlen Igazságforrás)?
    A játék TELJES aktuális állapota ebben az egyetlen `WorldState` objektumban él.
    Nincs szétszórva külön pontszám a képernyőn, külön pozíció a motorban és külön
    időzítő máshol — így két komponens sosem tud ellentmondani egymásnak.

Mi az a Kompozíció (HAS-A kapcsolat)?
    A `WorldState` nem örököl a `SnakeEntity`-ből, hanem *tartalmaz* két `SnakeEntity`
    objektumot (`player_one_snake` és `player_two_snake`). Ez rugalmasabb és tisztább,
    mint a mély öröklési hierarchia.
"""

from dataclasses import dataclass

from .game_enums import FruitType, GameStatus
from .grid_point_value import GridPoint
from .snake_entity import SnakeEntity


@dataclass(frozen=True)
class WorldState:
    """A játékvilág teljes, megváltoztathatatlan pillanatképe egy adott tick-ben.

    Attribútumok:
        room_width, room_height: A szoba külső mérete (a 0-s és room_width-1 / room_height-1 sorok a falak).
        player_one_snake, player_two_snake: Az 1-es és 2-es játékos kígyói.
        fruit_spawn_interval_seconds: Hány másodpercenként jelenjen meg új gyümölcs (manifestből).
        fruit_position: Az aktív gyümölcs helye, vagy `None`, ha épp nincs a pályán.
        fruit_type: Az aktív gyümölcs típusa (`FRUIT_CATALOG` kulcs).
        time_since_last_fruit_seconds: Eltelt idő (mp) az utolsó gyümölcs megjelenése óta.
        status: Fut-e még a játék, vagy eldőlt a meccs.
        tick: Diszkrét időlépések számlálója (0, 1, 2, ...).
    """

    room_width: int
    room_height: int
    player_one_snake: SnakeEntity
    player_two_snake: SnakeEntity
    fruit_spawn_interval_seconds: float = 3.0
    fruit_position: GridPoint | None = None
    fruit_type: FruitType = FruitType.APPLE
    time_since_last_fruit_seconds: float = 0.0
    status: GameStatus = GameStatus.RUNNING
    tick: int = 0
