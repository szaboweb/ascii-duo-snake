"""4. PRESENTATION RÉTEG — STATELESS ASCII BOARD RENDERER.

Miért választjuk szét a `format_board_frame()` és a `render_board_frame()` metódust?
    A `format_board_frame()` tiszta függvény: `WorldState -> str`. Nem hív `print()`-et,
    ezért a kirajzolás is 100%-ban tesztelhető unit tesztből, valódi terminál nélkül.
    A `render_board_frame()` csak a képernyő-törlést és a kiírást végzi.
"""

import sys

from ..domain.world_state import WorldState


class AsciiBoardRenderer:
    """Állapotmentes ASCII megjelenítő: a `WorldState`-et 2D szöveges képpé alakítja."""

    def format_board_frame(self, world_state: WorldState) -> str:
        """Tiszta formázás: a teljes szobát és az 1-es kígyót egyetlen szöveggé alakítja."""
        grid = [
            [" " for _ in range(world_state.room_width)]
            for _ in range(world_state.room_height)
        ]

        # 1. Szoba külső falai (`#`)
        for column_x in range(world_state.room_width):
            grid[0][column_x] = "#"
            grid[world_state.room_height - 1][column_x] = "#"
        for row_y in range(world_state.room_height):
            grid[row_y][0] = "#"
            grid[row_y][world_state.room_width - 1] = "#"

        # 2. 1-es játékos kígyója (fej: `1`, test: `o`)
        for segment_index, cell_position in enumerate(world_state.player_one_snake.body):
            grid[cell_position.y][cell_position.x] = "1" if segment_index == 0 else "o"

        board_lines = ["".join(row_cells) for row_cells in grid]
        header_line = (
            f"ASCII Duo Snake (Phase 1) | Tick: {world_state.tick} | "
            f"P1 Hossz: {world_state.player_one_snake.length} | "
            f"Allapot: {world_state.status.value}"
        )
        legend_line = "Jelmagyarazat: # fal | 1/o P1 kigyo"
        return "\n".join([header_line, *board_lines, legend_line])

    def render_board_frame(self, world_state: WorldState, clear_screen: bool = True) -> None:
        """Kiírja a megformázott képkockát a standard kimenetre."""
        frame_text = self.format_board_frame(world_state)
        if clear_screen:
            sys.stdout.write("\033[H\033[J")
        sys.stdout.write(frame_text + "\n")
        sys.stdout.flush()
