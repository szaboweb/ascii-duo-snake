"""1. DOMAIN RÉTEG — ENTITY (Class, Object, Read-Only Getter & Immutability).

Mi a különbség az Entity és a Value Object között?
    Míg a `GridPoint` (Value Object) csak egy koordináta, addig a `SnakeEntity`
    egyedi azonosítóval (`player_id: PlayerId`) rendelkező szereplő.

Miért `tuple` a `body`, és nem `list`?
    Mert a `SnakeEntity` megváltoztathatatlan (`frozen=True`). Ha `list` lenne benne,
    kívülről mégis bele lehetne írni (`snake.body.append(...)`), megtörve az
    immutabilitást. A `tuple` garantálja a biztonságos, tiszta állapotkezelést.
"""

from dataclasses import dataclass

from .game_enums import Direction, PlayerId
from .grid_point_value import GridPoint


@dataclass(frozen=True)
class SnakeEntity:
    """Egy játékos kígyójának megváltoztathatatlan pillanatképe.

    Attribútumok:
        player_id: A játékos azonosítója (`PlayerId.P1`).
        body: A kígyó testrészei a fejtől (`body[0]`) a farokig (`body[-1]`).
        direction: Az aktuális haladási irány.
    """

    player_id: PlayerId
    body: tuple[GridPoint, ...]
    direction: Direction

    @property
    def head(self) -> GridPoint:
        """GETTER (csak olvasható): visszaadja a kígyó fejének koordinátáját."""
        return self.body[0]

    @property
    def length(self) -> int:
        """GETTER (csak olvasható): visszaadja a kígyó aktuális hosszát."""
        return len(self.body)
