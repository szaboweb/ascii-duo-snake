"""4. PRESENTATION (TUI) RÉTEG — STATELESS RENDERER (Megjelenítő).

Miért hívják ezt "buta" (stateless) megjelenítőnek?
    Az `AsciiBoardRenderer` semmit nem számol ki a játékszabályokból és nem tárol saját
    játékállapotot. Kizárólag a kapott `WorldState` pillanatképet fordítja le
    karakterekre (`#`, `1`, `o`, `2`, `x`, `@`, `*`).

Elkülönítés (`format_board_frame` vs. `render_board_frame`):
    A szöveg összeállítása (`format_board_frame -> str`) el van választva a kiírástól
    (`print`), így még a megjelenítő is könnyen tesztelhető unit tesztből!
"""

from ..domain.fruit_catalog import FRUIT_CATALOG
from ..domain.grid_point_value import GridPoint
from ..domain.world_state import WorldState


class AsciiBoardRenderer:
    """A `WorldState` állapotot ASCII szöveges képkockává alakító megjelenítő."""

    def format_board_frame(self, world_state: WorldState) -> str:
        """Felépíti a teljes terminál-képkockát egyetlen stringként (0 mellékhatás)."""
        # A `set` konverzió O(1) gyorsaságúvá teszi a `cell_position in player_one_cells` ellenőrzést.
        player_one_cells = set(world_state.player_one_snake.body)
        player_two_cells = set(world_state.player_two_snake.body)
        fruit_symbol = FRUIT_CATALOG[world_state.fruit_type].symbol

        frame_lines: list[str] = [
            f"Tick: {world_state.tick:03d} | "
            f"P1 (WASD): {world_state.player_one_snake.fruits_eaten} db "
            f"(hossz: {world_state.player_one_snake.length}) | "
            f"P2 (IJKL): {world_state.player_two_snake.fruits_eaten} db "
            f"(hossz: {world_state.player_two_snake.length})",
        ]

        for row_y in range(world_state.room_height):
            row_characters: list[str] = []
            for column_x in range(world_state.room_width):
                cell_position = GridPoint(column_x, row_y)
                is_wall = (
                    column_x == 0
                    or column_x == world_state.room_width - 1
                    or row_y == 0
                    or row_y == world_state.room_height - 1
                )
                if is_wall:
                    row_characters.append("#")
                elif cell_position in player_one_cells:
                    row_characters.append(
                        "1" if cell_position == world_state.player_one_snake.head else "o"
                    )
                elif cell_position in player_two_cells:
                    row_characters.append(
                        "2" if cell_position == world_state.player_two_snake.head else "x"
                    )
                elif world_state.fruit_position == cell_position:
                    row_characters.append(fruit_symbol)
                else:
                    row_characters.append(" ")
            frame_lines.append("".join(row_characters))

        frame_lines.append(f"Állapot: {world_state.status.value}  |  Kilépés: Q")
        return "\n".join(frame_lines)

    def render_board_frame(self, world_state: WorldState, clear_screen: bool = True) -> None:
        """Kiírja a formázott képkockát a terminálra (opcionális ANSI képernyőtörléssel)."""
        terminal_prefix = "\x1b[2J\x1b[H" if clear_screen else ""
        print(terminal_prefix + self.format_board_frame(world_state), flush=True)
