"""1. DOMAIN RÉTEG — ENTITY (Class, Object, Stat, Getter & Method).

2. Előadás bővítése:
    A kígyó megkapja a `change_direction()` metódust és a deklaratív
    `OPPOSITE_DIRECTIONS` lookup táblát, amely tiltja a 180 fokos visszafordulást.
"""

from dataclasses import dataclass, replace

from .game_enums import Direction, PlayerId
from .grid_point_value import GridPoint

OPPOSITE_DIRECTIONS: dict[Direction, Direction] = {
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT,
}


@dataclass(frozen=True)
class SnakeEntity:
    """Egy játékos kígyójának megváltoztathatatlan pillanatképe."""

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

    def is_opposite_direction(self, target_direction: Direction) -> bool:
        """Tiszta predikátum: igaz, ha a kért irány pontosan 180°-kal ellentétes."""
        return OPPOSITE_DIRECTIONS[self.direction] == target_direction

    def change_direction(self, target_direction: Direction) -> "SnakeEntity":
        """Új haladási irányt állít be, de tiltja a 180 fokos visszafordulást."""
        if self.is_opposite_direction(target_direction):
            return self
        return replace(self, direction=target_direction)
