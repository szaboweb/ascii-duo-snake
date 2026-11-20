"""BELÉPÉSI PONT (2. előadás) — 1 kígyó játékciklusa (`--demo` és interaktív mód)."""

import argparse
import time

from .application.game_loop_controller import GameLoopController
from .domain.game_enums import Direction, GameStatus, PlayerId
from .domain.grid_point_value import GridPoint
from .domain.snake_entity import SnakeEntity
from .domain.world_state import WorldState
from .presentation.ascii_board_renderer import AsciiBoardRenderer
from .presentation.terminal_keyboard_adapter import TerminalKeyboardAdapter


def build_initial_world_state() -> WorldState:
    """Létrehozza a 2. előadás 1 kígyós kezdőpályáját."""
    return WorldState(
        room_width=24,
        room_height=12,
        player_one_snake=SnakeEntity(
            player_id=PlayerId.P1,
            body=(GridPoint(6, 6), GridPoint(5, 6), GridPoint(4, 6)),
            direction=Direction.RIGHT,
        ),
    )


def run_demo_session(
    controller: GameLoopController,
    board_renderer: AsciiBoardRenderer,
    total_steps: int = 8,
) -> None:
    """Rövid, determinisztikus bemutató kör 1 kígyóval."""
    demo_script: dict[int, tuple[PlayerId, Direction]] = {
        2: (PlayerId.P1, Direction.UP),
        5: (PlayerId.P1, Direction.LEFT),
    }
    for _ in range(total_steps):
        if controller.current_state.status != GameStatus.RUNNING:
            break
        current_tick = controller.current_state.tick
        if current_tick in demo_script:
            player_id, target_direction = demo_script[current_tick]
            controller.steer_player_snake(player_id, target_direction)
        controller.advance_simulation_tick()

    board_renderer.render_board_frame(controller.current_state, clear_screen=False)


def run_interactive_session(
    controller: GameLoopController,
    board_renderer: AsciiBoardRenderer,
) -> None:
    """Valós idejű játékciklus: Input -> Update -> Render -> Sleep."""
    delta_seconds = 1.0 / controller.tick_rate_hz

    with TerminalKeyboardAdapter() as keyboard_adapter:
        while controller.current_state.status == GameStatus.RUNNING:
            commands, quit_requested = keyboard_adapter.poll_keyboard_commands()
            if quit_requested:
                break
            for player_id, target_direction in commands:
                controller.steer_player_snake(player_id, target_direction)

            controller.advance_simulation_tick()
            board_renderer.render_board_frame(controller.current_state, clear_screen=True)
            time.sleep(delta_seconds)

    print(f"\nJáték vége! Állapot: {controller.current_state.status.value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ASCII Duo Snake — 2. előadás (1 kígyó)")
    parser.add_argument("--demo", action="store_true", help="Nem-interaktív demó futtatása")
    parser.add_argument("--speed", type=float, default=6.0, help="Sebesség (tick/mp, 1..60)")
    cli_args = parser.parse_args()

    controller = GameLoopController(build_initial_world_state())
    controller.tick_rate_hz = cli_args.speed  # Validált SETTER használata
    board_renderer = AsciiBoardRenderer()

    if cli_args.demo:
        run_demo_session(controller, board_renderer)
    else:
        run_interactive_session(controller, board_renderer)
