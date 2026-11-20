"""COMPOSITION ROOT (Belépési pont) — Dependency Injection összedrótozása.

Mi az a Composition Root?
    A program egyetlen olyan helye, amely ismeri az összes réteg konkrét osztályait
    (`JsonRoomManifestLoader`, `SystemRandomAdapter`, `InputRecorderService`,
    `GameLoopController`, `AsciiBoardRenderer`, `TerminalKeyboardAdapter`,
    `SessionStateMachine`, `GameEventBus`, `MatchTelemetryCollector`,
    `RetroArcadeSoundAdapter`, `DeterministicReplayService`),
    és itt köti össze őket.

    Mivel az összedrótozás egy helyre van koncentrálva, a játék többi része laza
    csatolású (loosely coupled) marad: bármelyik komponens lecserélhető anélkül,
    hogy a `domain/` vagy `application/` réteghez hozzá kellene nyúlni.
"""

import argparse
from pathlib import Path
import random
import sys
import time

from .application.deterministic_replay_service import DeterministicReplayService, MatchReplaySnapshot
from .application.game_event_bus import GameEventBus, MatchTelemetryCollector
from .application.game_loop_controller import GameLoopController
from .application.input_recorder_service import InputRecorderService
from .domain.bot_steering_strategy import (
    BOT_STRATEGY_CATALOG,
    BotSteeringStrategy,
    select_bot_strategy,
)
from .domain.domain_contracts import RandomNumberProvider, RoomManifestLoader
from .domain.game_enums import Direction, GameStatus, PlayerId
from .domain.session_state_machine import SessionPhase, SessionStateMachine
from .domain.world_state import WorldState
from .infrastructure.json_room_manifest_loader import JsonRoomManifestLoader
from .infrastructure.system_random_adapter import SystemRandomAdapter
from .presentation.ascii_board_renderer import AsciiBoardRenderer
from .presentation.board_theme_catalog import BOARD_THEME_CATALOG, select_board_theme
from .presentation.retro_arcade_sound_adapter import RetroArcadeSoundAdapter
from .presentation.terminal_keyboard_adapter import TerminalKeyboardAdapter


def _configure_utf8_stdout() -> None:
    """UTF-8 kimenet beállítása Windows konzolon is, ha a szabványos kimenet támogatja."""
    reconfigure_stdout = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure_stdout):
        reconfigure_stdout(encoding="utf-8", errors="replace")


def _apply_player_two_bot_steering(
    controller: GameLoopController,
    player_two_bot_strategy: BotSteeringStrategy | None,
) -> None:
    """Ha a P2 bot aktív, meghatározza és végrehajtja a következő irányválasztását."""
    if player_two_bot_strategy is None:
        return
    chosen_direction = player_two_bot_strategy.choose_next_direction(
        controller.current_state, PlayerId.P2
    )
    controller.steer_player_snake(PlayerId.P2, chosen_direction)


def run_demo_session(
    controller: GameLoopController,
    board_renderer: AsciiBoardRenderer,
    step_count: int = 12,
    player_two_bot_strategy: BotSteeringStrategy | None = None,
) -> None:
    """Rövid, determinisztikus bemutató kör előre megírt vagy bot-vezérelt bemenetekkel."""
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
            if player_two_bot_strategy is None or player_id != PlayerId.P2:
                controller.steer_player_snake(player_id, target_direction)
        _apply_player_two_bot_steering(controller, player_two_bot_strategy)
        controller.advance_simulation_tick(delta_seconds)

    board_renderer.render_board_frame(controller.current_state, clear_screen=False)
    recorded_history = controller.input_recorder.history
    print(f"Rögzített bemenetek ({len(recorded_history)} db): {recorded_history}")


def run_interactive_session(
    controller: GameLoopController,
    board_renderer: AsciiBoardRenderer,
    player_two_bot_strategy: BotSteeringStrategy | None = None,
) -> None:
    """Valós idejű játékciklus (Game Loop): Input -> Update -> Render -> Sleep."""
    delta_seconds = 1.0 / controller.tick_rate_hz

    with TerminalKeyboardAdapter() as keyboard_adapter:
        while controller.current_state.status == GameStatus.RUNNING:
            polled_commands, quit_requested = keyboard_adapter.poll_keyboard_commands()
            if quit_requested:
                break
            for player_id, target_direction in polled_commands:
                if player_two_bot_strategy is None or player_id != PlayerId.P2:
                    controller.steer_player_snake(player_id, target_direction)
            _apply_player_two_bot_steering(controller, player_two_bot_strategy)

            controller.advance_simulation_tick(delta_seconds)
            board_renderer.render_board_frame(controller.current_state, clear_screen=True)
            time.sleep(delta_seconds)

    print(f"\nJáték vége! Eredmény: {controller.current_state.status.value}")
    print(f"Rögzített irányváltások száma: {len(controller.input_recorder.history)}")


def build_default_manifest_path() -> Path:
    """Visszaadja az alapértelmezett `assets/room_manifest.json` útvonalát."""
    return Path(__file__).resolve().parents[2] / "assets" / "room_manifest.json"


def _build_argument_parser() -> argparse.ArgumentParser:
    """Felépíti a parancssori argumentum-feldolgozót az összes játék- és bővítménykapcsolóval."""
    argument_parser = argparse.ArgumentParser(description="ASCII Duo Snake (Python Clean Architecture)")
    argument_parser.add_argument("--demo", action="store_true", help="Nem-interaktív demó futtatása")
    argument_parser.add_argument("--speed", type=float, default=6.0, help="Sebesség (tick/mp, 1..60)")
    argument_parser.add_argument("--manifest", type=Path, default=build_default_manifest_path(), help="Pálya JSON")
    argument_parser.add_argument(
        "--theme", choices=tuple(BOARD_THEME_CATALOG.keys()), default="classic_ascii", help="Vizuális játéktábla-téma"
    )
    argument_parser.add_argument(
        "--p2-bot", choices=tuple(BOT_STRATEGY_CATALOG.keys()), default=None, help="Második játékos (P2) bot stratégiája"
    )
    argument_parser.add_argument("--sound", action="store_true", default=False, help="Retro 8-bites hanghatások bekapcsolása")
    argument_parser.add_argument("--seed", type=int, default=None, help="Véletlenszám-kezdőmag (demóban alapértelmezetten 42)")
    argument_parser.add_argument("--record", type=Path, default=None, help="Bemenetek mentése visszajátszási JSON fájlba")
    argument_parser.add_argument("--replay", type=Path, default=None, help="Mentett JSON visszajátszás determinisztikus futtatása")
    return argument_parser


def _resolve_effective_seed(parsed_arguments: argparse.Namespace) -> int:
    """Kiszámítja az effektív random kezdőmagot (demó módban alapértelmezetten 42)."""
    if parsed_arguments.seed is not None:
        return parsed_arguments.seed
    if parsed_arguments.demo:
        return 42
    return random.SystemRandom().randrange(1, 1_000_000)


def _run_replay_session(
    replay_path: Path,
    initial_world_state: WorldState,
    board_renderer: AsciiBoardRenderer,
    state_machine: SessionStateMachine,
) -> None:
    """Betölti és determinisztikusan újrajátssza a mentett mérkőzést."""
    state_machine.transition_to(SessionPhase.REPLAY)
    snapshot = DeterministicReplayService.deserialize_replay_from_json(
        replay_path.read_text(encoding="utf-8")
    )
    replayed_state = DeterministicReplayService.replay_match_deterministically(
        initial_world_state, snapshot, lambda seed: SystemRandomAdapter(seed=seed)
    )
    state_machine.transition_to(SessionPhase.GAME_OVER)
    board_renderer.render_board_frame(replayed_state, clear_screen=False)
    print(
        f"[REPLAY OK] Visszajátszott állapot: {replayed_state.status.value} "
        f"(tick={replayed_state.tick}, seed={snapshot.random_seed})"
    )


def _save_replay_snapshot(
    record_path: Path, effective_seed: int, controller: GameLoopController
) -> None:
    """Elmenti a lejátszott mérkőzés determinisztikus visszajátszási pillanatképét."""
    snapshot = MatchReplaySnapshot(
        random_seed=effective_seed,
        tick_rate_hz=controller.tick_rate_hz,
        total_ticks=controller.current_state.tick,
        recorded_inputs=controller.input_recorder.history,
        expected_final_status=controller.current_state.status,
    )
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(
        DeterministicReplayService.serialize_replay_to_json(snapshot), encoding="utf-8"
    )
    print(f"[RECORD OK] Visszajátszás mentve: {record_path} (tick={snapshot.total_ticks}, seed={effective_seed})")


def _print_session_summary(
    telemetry_collector: MatchTelemetryCollector, state_machine: SessionStateMachine
) -> None:
    """Kiírja a feloldott jelvényeket (ha vannak) és az FSM állapotátmenet-történetét."""
    if telemetry_collector.unlocked_badges:
        print(f"Feloldott jelvények: {', '.join(telemetry_collector.unlocked_badges)}")
    transition_history_text = " -> ".join(phase.value.upper() for phase in state_machine.transition_history)
    print(f"Munkamenet állapotút (FSM): {transition_history_text}")


def main(argv: list[str] | None = None) -> None:
    """CLI argumentumok feldolgozása, függőségek bekötése és a játék indítása."""
    _configure_utf8_stdout()
    parsed_arguments = _build_argument_parser().parse_args(argv)

    state_machine = SessionStateMachine()
    board_renderer = AsciiBoardRenderer(theme=select_board_theme(parsed_arguments.theme))
    manifest_loader: RoomManifestLoader = JsonRoomManifestLoader()
    initial_world_state = manifest_loader.load_initial_world_state(str(parsed_arguments.manifest))
    telemetry_collector = MatchTelemetryCollector()

    if parsed_arguments.replay is not None:
        _run_replay_session(parsed_arguments.replay, initial_world_state, board_renderer, state_machine)
        _print_session_summary(telemetry_collector, state_machine)
        return

    # DEPENDENCY INJECTION: Konkrét megvalósítások hozzárendelése szerződés-típusokhoz
    effective_seed = _resolve_effective_seed(parsed_arguments)
    random_provider: RandomNumberProvider = SystemRandomAdapter(seed=effective_seed)
    input_recorder = InputRecorderService()
    event_bus = GameEventBus()
    sound_adapter = RetroArcadeSoundAdapter(enabled=parsed_arguments.sound)
    event_bus.subscribe_listener(telemetry_collector.on_domain_event)
    event_bus.subscribe_listener(sound_adapter.on_domain_event)

    controller = GameLoopController(
        initial_world_state=initial_world_state,
        random_provider=random_provider,
        input_recorder=input_recorder,
        event_bus=event_bus,
    )
    controller.tick_rate_hz = parsed_arguments.speed  # SETTER használata (1.0..60.0 validációval)
    player_two_bot_strategy: BotSteeringStrategy | None = (
        select_bot_strategy(parsed_arguments.p2_bot) if parsed_arguments.p2_bot else None
    )

    state_machine.transition_to(SessionPhase.PLAYING)
    if parsed_arguments.demo:
        run_demo_session(controller, board_renderer, player_two_bot_strategy=player_two_bot_strategy)
    else:
        run_interactive_session(controller, board_renderer, player_two_bot_strategy=player_two_bot_strategy)
    state_machine.transition_to(SessionPhase.GAME_OVER)

    if parsed_arguments.record is not None:
        _save_replay_snapshot(parsed_arguments.record, effective_seed, controller)
    _print_session_summary(telemetry_collector, state_machine)
