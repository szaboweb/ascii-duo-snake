"""1. DOMAIN RÉTEG — CONTRACT (Interface / Dependency Inversion Principle).

Miért itt, a Domain rétegben van ez a szerződés?
    Ez a **Dependency Inversion (Függőség-megfordítás)** elve: a Domain réteg
    nem függhet a valódi `random` modultól. Ehelyett a Domain előír egy
    *szerződést* (`typing.Protocol`), hogy milyen véletlenszám-képességre van
    szüksége — a külső réteg (`infrastructure/system_random_adapter.py`) és a
    tesztek (`tests/`) pedig olyan objektumot adnak be, amely teljesíti ezt.

Előny a tesztelésben:
    A `RandomNumberProvider` helyére a unit tesztben egy `FakeRandomNumberProvider`
    mock kerülhet, így a véletlenszerű gyümölcs-megjelenés 100%-ban kiszámíthatóvá válik.
"""

from typing import Protocol


class RandomNumberProvider(Protocol):
    """Szerződés determinisztikusan cserélhető véletlenszám-generáláshoz."""

    def next_int(self, upper_exclusive: int) -> int:
        """Visszaad egy egész számot a `[0, upper_exclusive)` intervallumból."""
        ...
