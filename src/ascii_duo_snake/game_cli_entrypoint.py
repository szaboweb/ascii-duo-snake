"""COMPOSITION ROOT — Belépési pont (Phase 1: Statikus szoba kirajzolása).

Ebben az első fázisban még nincs mozgás, nincs billentyűzet és nincs véletlenszám.
A program felépít egyetlen megváltoztathatatlan `WorldState` objektumot (1 kígyóval),
majd az `AsciiBoardRenderer` segítségével kirajzol egyetlen statikus képkockát.
"""

from .domain.game_enums import Direction, PlayerId
from .domain.grid_point_value import GridPoint
from .domain.snake_entity import SnakeEntity
from .domain.world_state import WorldState
from .presentation.ascii_board_renderer import AsciiBoardRenderer


def build_initial_world_state() -> WorldState:
    """Összeállítja a statikus, 1 kígyós kezdő szobát."""
    player_one_snake = SnakeEntity(
        player_id=PlayerId.P1,
        body=(GridPoint(5, 5), GridPoint(4, 5), GridPoint(3, 5)),
        direction=Direction.RIGHT,
    )
    return WorldState(
        room_width=24,
        room_height=12,
        player_one_snake=player_one_snake,
    )


def main() -> int:
    """Felépíti a statikus állapotot és kirajzol egyetlen képkockát."""
    world_state = build_initial_world_state()
    board_renderer = AsciiBoardRenderer()
    board_renderer.render_board_frame(world_state, clear_screen=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
