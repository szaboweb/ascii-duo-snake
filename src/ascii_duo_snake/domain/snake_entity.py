"""1. DOMAIN RÉTEG — ENTITY (Class, Object, Stat, Read-Only Getter & Method).

Mi a különbség az Entity és a Value Object között?
    Míg a `GridPoint` (Value Object) csak egy koordináta, addig a `SnakeEntity`
    egyedi azonosítóval (`player_id: PlayerId`) és saját viselkedéssel
    (`change_direction`) rendelkező szereplő.

Miért `tuple` a `body`, és nem `list`?
    Mert a `SnakeEntity` megváltoztathatatlan (`frozen=True`). Ha `list` lenne benne,
    kívülről mégis bele lehetne írni (`snake.body.append(...)`), megtörve az
    immutabilitást. A `tuple` garantálja, hogy minden módosítás új `SnakeEntity`-t hoz létre.
"""

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Mapping

from .game_enums import Direction, PlayerId
from .grid_point_value import GridPoint

# Deklaratív lookup tábla: megmutatja minden irány pontos ellentétét.
# Rövidebb és átláthatóbb, mint egy 4 ágú if/elif lánc.
OPPOSITE_DIRECTIONS: Mapping[Direction, Direction] = MappingProxyType(
    {
        Direction.UP: Direction.DOWN,
        Direction.DOWN: Direction.UP,
        Direction.LEFT: Direction.RIGHT,
        Direction.RIGHT: Direction.LEFT,
    }
)


def is_opposite_direction(current_direction: Direction, target_direction: Direction) -> bool:
    """Tiszta predikátum: igazat ad vissza, ha a két irány 180 fokban ellentétes."""
    return OPPOSITE_DIRECTIONS[current_direction] == target_direction


@dataclass(frozen=True)
class SnakeEntity:
    """Egy játékos kígyójának megváltoztathatatlan pillanatképe.

    Attribútumok:
        player_id: A játékos azonosítója (`PlayerId.P1` vagy `PlayerId.P2`).
        body: A kígyó testrészei a fejtől (`body[0]`) a farokig (`body[-1]`).
        direction: Az aktuális haladási irány.
        fruits_eaten: Statisztika (STAT) az eddig megevett gyümölcsök számáról.
        pending_growth: Hátralévő növekedési lépések (pl. aranydinnye = +3 tickig nő).
    """

    player_id: PlayerId
    body: tuple[GridPoint, ...]
    direction: Direction
    fruits_eaten: int = 0
    pending_growth: int = 0

    @property
    def head(self) -> GridPoint:
        """GETTER (csak olvasható): visszaadja a kígyó fejének koordinátáját."""
        return self.body[0]

    @property
    def length(self) -> int:
        """GETTER (csak olvasható): visszaadja a kígyó aktuális hosszát."""
        return len(self.body)

    def change_direction(self, target_direction: Direction) -> "SnakeEntity":
        """Új haladási irányt állít be, de tiltja a 180 fokos visszafordulást.

        Logika:
            Ha a kért irány pontosan ellentétes a jelenlegivel (pl. jobbra menet balra),
            a kígyó nem fordulhat önmagába, ezért változatlanul (`self`) tér vissza.
            Egyébként a `dataclasses.replace` egy új `SnakeEntity` példányt készít az új iránnyal.
        """
        if is_opposite_direction(self.direction, target_direction):
            return self
        return replace(self, direction=target_direction)
