"""COMPOSITION ROOT (Belépési pont) — 3. előadás: 2 kígyó, gyümölcsök és DI.

Ebben a fázisban a két kígyó és a szoba mérete még kódból készül el
(`build_default_world_state`), a véletlengenerálás viszont már szerződés
(`RandomNumberProvider`) mögött, `SystemRandomAdapter` befecskendezésével működik.
A külső JSON manifest betöltő a 4. előadásban érkezik.
"""

import argparse
import time

from .application.game_loop_controller import GameLoopController
from .domain.domain_contracts import RandomNumberProvider
from .domain.game_enums import Direction, GameStatus, PlayerId
from .domain.grid_point_value import GridPoint
from .domain.snake_entity import SnakeEntity
from .domain.world_state import WorldState
from .infrastructure.system_random_adapter import SystemRandomAdapter
from .presentation.ascii_board_renderer import AsciiBoardRenderer
from .presentation.terminal_keyboard_adapter import TerminalKeyboardAdapter


def build_default_world_state() -> WorldState:
    """Összeállítja az alapértelmezett 24x16-os, kétkígyós kezdő világállapotot."""
    player_one_snake = SnakeEntity(
        player_id=PlayerId.P1,
        body=(GridPoint(5, 8),),
        direction=Direction.RIGHT,
    )
    player_two_snake = SnakeEntity(
        player_id=PlayerId.P2,
        body=(GridPoint(18, 8),),
        direction=Direction.LEFT,
    )
    return WorldState(
        room_width=24,
        room_height=16,
        player_one_snake=player_one_snake,
        player_two_snake=player_two_snake,
        fruit_spawn_interval_seconds=3.0,
    )


def run_demo_session(
    controller: GameLoopController,
    board_renderer: AsciiBoardRenderer,
    step_count: int = 12,
) -> None:
    """Rövid, determinisztikus bemutató kör két kígyóval és gyümölcs-spawninggal."""
    scripted_inputs: dict[int, tuple[PlayerId, Direction]] = {
        2: (PlayerId.P1, Direction.UP),
        4: (PlayerId.P2, Direction.DOWN),
        6: (PlayerId.P1, Direction.RIGHT),
    }
    delta_seconds = 1.0 / controller.tick_rate_hz

    for _ in range(step_count):
        if controller.current_state.status != GameStatus.RUNNING:
            break
        current_tick = controller.current_state.tick
        if current_tick in scripted_inputs:
            player_id, target_direction = scripted_inputs[current_tick]
            controller.steer_player_snake(player_id, target_direction)
        controller.advance_simulation_tick(delta_seconds)

    board_renderer.render_board_frame(controller.current_state, clear_screen=False)


def run_interactive_session(
    controller: GameLoopController,
    board_renderer: AsciiBoardRenderer,
) -> None:
    """Valós idejű 2 fős játékciklus (P1: WASD, P2: IJKL, Kilépés: Q)."""
    delta_seconds = 1.0 / controller.tick_rate_hz

    with TerminalKeyboardAdapter() as keyboard_adapter:
        while controller.current_state.status == GameStatus.RUNNING:
            polled_commands, quit_requested = keyboard_adapter.poll_keyboard_commands()
            if quit_requested:
                break
            for player_id, target_direction in polled_commands:
                controller.steer_player_snake(player_id, target_direction)

            controller.advance_simulation_tick(delta_seconds)
            board_renderer.render_board_frame(controller.current_state, clear_screen=True)
            time.sleep(delta_seconds)

    print(f"\nJáték vége! Eredmény: {controller.current_state.status.value}")


def main() -> None:
    """CLI argumentumok feldolgozása, DI összedrótozás és a játék indítása."""
    argument_parser = argparse.ArgumentParser(
        description="ASCII Duo Snake — 3. előadás (2 kígyó, gyümölcsök, DI)"
    )
    argument_parser.add_argument(
        "--demo",
        action="store_true",
        help="Nem-interaktív demó futtatása",
    )
    argument_parser.add_argument(
        "--speed",
        type=float,
        default=6.0,
        help="Sebesség (tick/mp, 1..60)",
    )
    parsed_arguments = argument_parser.parse_args()

    random_provider: RandomNumberProvider = SystemRandomAdapter(
        seed=42 if parsed_arguments.demo else None
    )
    board_renderer = AsciiBoardRenderer()
    controller = GameLoopController(
        initial_world_state=build_default_world_state(),
        random_provider=random_provider,
    )
    controller.tick_rate_hz = parsed_arguments.speed

    if parsed_arguments.demo:
        run_demo_session(controller, board_renderer)
    else:
        run_interactive_session(controller, board_renderer)
