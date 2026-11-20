"""1. DOMAIN RÉTEG — CONTRACT (Interface / Dependency Inversion Principle).

Miért itt, a Domain rétegben vannak ezek a szerződések?
    Ez a **Dependency Inversion (Függőség-megfordítás)** elve: a Domain réteg
    nem függhet fájlrendszertől (`json`, `Path`) vagy a valódi `random` modultól.
    Ehelyett a Domain előír egy *szerződést* (`typing.Protocol`), hogy milyen
    képességekre van szüksége — a külső rétegek (`infrastructure/`) és a tesztek
    (`tests/`) pedig olyan objektumot adnak be, amely teljesíti ezt a szerződést.

Előny a tesztelésben:
    A `RandomNumberProvider` helyére a unit tesztben egy `FakeRandomNumberProvider`
    mock kerülhet, így a véletlenszerű gyümölcs-megjelenés 100%-ban kiszámíthatóvá válik.
"""

from typing import Protocol

from .world_state import WorldState


class RoomManifestLoader(Protocol):
    """Szerződés kezdő pályaállapot betöltéséhez (fájlból, memóriából vagy hálózatról)."""

    def load_initial_world_state(self, manifest_path: str) -> WorldState:
        """Beolvassa és validálja a pályaleírót, majd visszaadja a kezdő `WorldState`-et."""
        ...


class RandomNumberProvider(Protocol):
    """Szerződés determinisztikusan cserélhető véletlenszám-generáláshoz."""

    def next_int(self, upper_exclusive: int) -> int:
        """Visszaad egy egész számot a `[0, upper_exclusive)` intervallumból."""
        ...
