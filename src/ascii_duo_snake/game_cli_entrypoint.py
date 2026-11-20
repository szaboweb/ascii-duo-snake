"""COMPOSITION ROOT (Belépési pont) — Dependency Injection összedrótozása.

Mi az a Composition Root?
    A program egyetlen olyan helye, amely ismeri az összes réteg konkrét osztályait
    (`JsonRoomManifestLoader`, `SystemRandomAdapter`, `InputRecorderService`,
    `GameLoopController`, `AsciiBoardRenderer`, `TerminalKeyboardAdapter`),
    és itt köti össze őket.

    Mivel az összedrótozás egy helyre van koncentrálva, a játék többi része laza
    csatolású (loosely coupled) marad: bármelyik komponens lecserélhető anélkül,
    hogy a `domain/` vagy `application/` réteghez hozzá kellene nyúlni.
"""

import argparse
from pathlib import Path
import time

from .application.game_loop_controller import GameLoopController
from .application.input_recorder_service import InputRecorderService
from .domain.domain_contracts import RandomNumberProvider, RoomManifestLoader
from .domain.game_enums import Direction, GameStatus, PlayerId
from .infrastructure.json_room_manifest_loader import JsonRoomManifestLoader
from .infrastructure.system_random_adapter import SystemRandomAdapter
from .presentation.ascii_board_renderer import AsciiBoardRenderer
from .presentation.terminal_keyboard_adapter import TerminalKeyboardAdapter


def run_demo_session(
    controller: GameLoopController,
    board_renderer: AsciiBoardRenderer,
    step_count: int = 12,
) -> None:
    """Rövid, determinisztikus bemutató kör előre megírt bemenetekkel."""
    scripted_inputs: dict[int, tuple[PlayerId, Direction]] = {
        2: (PlayerId.P1, Direction.UP),
        4: (PlayerId.P2, Direction.DOWN),
        6: (PlayerId.P1, Direction.RIGHT),
    }
    delta_seconds = 1.0 / controller.tick_rate_hz  # GETTER használata

    for _ in range(step_count):
        if controller.current_state.status != GameStatus.RUNNING:
            break
        current_tick = controller.current_state.tick
        if current_tick in scripted_inputs:
            player_id, target_direction = scripted_inputs[current_tick]
            controller.steer_player_snake(player_id, target_direction)
        controller.advance_simulation_tick(delta_seconds)

    board_renderer.render_board_frame(controller.current_state, clear_screen=False)
    recorded_history = controller.input_recorder.history
    print(f"Rögzített bemenetek ({len(recorded_history)} db): {recorded_history}")


def run_interactive_session(
    controller: GameLoopController,
    board_renderer: AsciiBoardRenderer,
) -> None:
    """Valós idejű játékciklus (Game Loop): Input -> Update -> Render -> Sleep."""
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
    print(f"Rögzített irányváltások száma: {len(controller.input_recorder.history)}")


def build_default_manifest_path() -> Path:
    """Visszaadja az alapértelmezett `assets/room_manifest.json` útvonalát."""
    return Path(__file__).resolve().parents[2] / "assets" / "room_manifest.json"


def main() -> None:
    """CLI argumentumok feldolgozása, függőségek bekötése és a játék indítása."""
    argument_parser = argparse.ArgumentParser(
        description="ASCII Duo Snake (Python Clean Architecture)"
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
    argument_parser.add_argument(
        "--manifest",
        type=Path,
        default=build_default_manifest_path(),
        help="Pálya JSON",
    )
    parsed_arguments = argument_parser.parse_args()

    # DEPENDENCY INJECTION: Konkrét megvalósítások hozzárendelése szerződés-típusokhoz
    manifest_loader: RoomManifestLoader = JsonRoomManifestLoader()
    random_provider: RandomNumberProvider = SystemRandomAdapter(
        seed=42 if parsed_arguments.demo else None
    )
    input_recorder = InputRecorderService()
    board_renderer = AsciiBoardRenderer()

    initial_world_state = manifest_loader.load_initial_world_state(str(parsed_arguments.manifest))
    controller = GameLoopController(
        initial_world_state=initial_world_state,
        random_provider=random_provider,
        input_recorder=input_recorder,
    )
    controller.tick_rate_hz = parsed_arguments.speed  # SETTER használata (1.0..60.0 validációval)

    if parsed_arguments.demo:
        run_demo_session(controller, board_renderer)
    else:
        run_interactive_session(controller, board_renderer)
