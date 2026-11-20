"""1. DOMAIN RÉTEG — CATALOG (Adatvezérelt nyilvántartás / Data-Driven SSOT).

Miért tesszük külön katalógusba a gyümölcsök tulajdonságait?
    Ha a gyümölcsök növesztési értéke és ASCII karaktere egy központi szótárban él
    (Single Source of Truth), akkor egy új gyümölcs (pl. szuperbogyó) felvételéhez
    elég a `game_enums.py`-t és ezt a fájlt bővíteni — a `game_rules_engine.py` és az
    `ascii_board_renderer.py` automatikusan kezelni fogja!

Miért `MappingProxyType`?
    A sima Python `dict` futásidőben véletlenül átírható lenne. A `MappingProxyType`
    csak olvasható nézetet ad rá, így a katalógus valóban állandó marad.
"""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .game_enums import FruitType


@dataclass(frozen=True)
class FruitSpec:
    """Egy gyümölcstípus statikus leírása (megjelenítés + játékhatás)."""

    symbol: str
    growth_amount: int


FRUIT_CATALOG: Mapping[FruitType, FruitSpec] = MappingProxyType(
    {
        FruitType.APPLE: FruitSpec(symbol="@", growth_amount=1),
        FruitType.GOLDEN_MELON: FruitSpec(symbol="*", growth_amount=3),
    }
)
