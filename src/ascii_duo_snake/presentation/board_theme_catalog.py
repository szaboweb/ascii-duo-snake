"""Adatvezérelt vizuális témakatalógus (Data-Driven Visual Theming Catalog).

Ez a modul a Presentation (megjelenítési) rétegben definiálja a játéktábla
karakterkészleteit (témáit) a Felelősségek Szétválasztása (Separation of Concerns)
és a Nyílt/Zárt Elv (Open/Closed Principle — OCP) szerint.

Architekturális előnyök:
1. **Rétegszigetelés:** A Domain réteg (`WorldState`, `SnakeEntity`) teljesen
   független attól, hogy a falakat `#`, `█` vagy `+` karakterrel rajzoljuk ki.
2. **Immutabilitás (`frozen=True` + `MappingProxyType`):** A témák futásidőben
   nem írhatók felül véletlenül, így a renderelő mindig konzisztens szimbólumokat olvas.
3. **Bővíthetőség kódmódosítás nélkül:** Új vizuális téma felvételéhez elegendő egy
   új `BoardThemeSpec` bejegyzést regisztrálni a `BOARD_THEME_CATALOG` szótárban.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class BoardThemeSpec:
    """Egyetlen ASCII/Unicode játéktábla-téma nem-módosítható karakterkészlete."""

    theme_id: str
    display_name: str
    wall_glyph: str
    empty_glyph: str
    p1_head_glyph: str
    p1_body_glyph: str
    p2_head_glyph: str
    p2_body_glyph: str


DEFAULT_BOARD_THEME = BoardThemeSpec(
    theme_id="classic_ascii",
    display_name="Klasszikus ASCII",
    wall_glyph="#",
    empty_glyph=" ",
    p1_head_glyph="1",
    p1_body_glyph="o",
    p2_head_glyph="2",
    p2_body_glyph="x",
)

BOARD_THEME_CATALOG: Mapping[str, BoardThemeSpec] = MappingProxyType(
    {
        "classic_ascii": DEFAULT_BOARD_THEME,
        "neon_arcade": BoardThemeSpec(
            theme_id="neon_arcade",
            display_name="Neon Játékterem",
            wall_glyph="█",
            empty_glyph="·",
            p1_head_glyph="@",
            p1_body_glyph="●",
            p2_head_glyph="&",
            p2_body_glyph="◆",
        ),
        "retro_matrix": BoardThemeSpec(
            theme_id="retro_matrix",
            display_name="Retro Mátrix",
            wall_glyph="+",
            empty_glyph=".",
            p1_head_glyph="A",
            p1_body_glyph="a",
            p2_head_glyph="B",
            p2_body_glyph="b",
        ),
    }
)


def select_board_theme(theme_id: str) -> BoardThemeSpec:
    """Kikeresei a megadott azonosítójú táblatémát a katalógusból."""
    selected_theme = BOARD_THEME_CATALOG.get(theme_id)
    if selected_theme is None:
        valid_ids = ", ".join(sorted(BOARD_THEME_CATALOG.keys()))
        raise ValueError(
            f"Ismeretlen táblatéma-azonosító: '{theme_id}'. "
            f"Érvényes témák: [{valid_ids}]"
        )
    return selected_theme
