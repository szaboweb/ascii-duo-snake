"""1. DOMAIN RÉTEG — VALUE OBJECT, IMMUTABILITY & OPERATOR OVERLOADING.

Mi az a Value Object (Értékobjektum)?
    Olyan apró objektum, amelynek nincs saját "személyazonossága" (ID-ja):
    két `GridPoint(5, 7)` pontosan ugyanazt jelenti, és létrehozás után
    soha nem változik meg (`frozen=True`).

Miért hasznos az operátor-túlterhelés (`__add__`)?
    Ahelyett, hogy mindenhol kézzel írnánk: `GridPoint(point.x + delta_x, point.y + delta_y)`,
    elég annyi: `head_position + direction_delta`. A kód közelebb kerül a matematikai gondolkodáshoz.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GridPoint:
    """Megváltoztathatatlan (x, y) rács-koordináta a 2D szobában.

    A `@dataclass(frozen=True)` automatikusan generálja:
        - az `__init__` konstruktort,
        - az érték-alapú `__eq__` összehasonlítást (`GridPoint(1, 2) == GridPoint(1, 2)`),
        - a `__hash__` metódust (így betehető `set`-be és `dict`-be, pl. ütközéskereséshez),
        - és megakadályozza a mezők utólagos átírását (Immutability).
    """

    x: int
    y: int

    def __add__(self, offset: "GridPoint") -> "GridPoint":
        """Összead két koordinátát/vektort, és egy ÚJ `GridPoint`-ot ad vissza.

        Példa:
            `GridPoint(5, 7) + GridPoint(1, 0) == GridPoint(6, 7)`
        """
        return GridPoint(self.x + offset.x, self.y + offset.y)
