"""PROMO STORYBOARD — 100% adatvezérelt (Data-Driven), élő játékmotort futtató bemutató.

Ez a modul szigorúan elkülönül a `src/ascii_duo_snake/` rétegektől: kizárólag
fogyasztója a valódi domain, application, infrastructure és presentation osztályoknak.
Minden szöveg, időzítés, kezdőállapot és szkriptelt lépés a `PromoStoryboardConfig`
(JSON) objektumból érkezik — nulla beégetett promóciós szöveg vagy tick-szkript.
"""

from pathlib import Path
import tempfile
import time

from ascii_duo_snake.application.game_loop_controller import GameLoopController
from ascii_duo_snake.application.input_recorder_service import InputRecorderService
from ascii_duo_snake.domain.domain_exceptions import InvalidRoomManifestException
from ascii_duo_snake.domain.game_enums import Direction, FruitType, GameStatus, PlayerId
from ascii_duo_snake.domain.grid_point_value import GridPoint
from ascii_duo_snake.domain.snake_entity import SnakeEntity
from ascii_duo_snake.domain.world_state import WorldState
from ascii_duo_snake.infrastructure.json_room_manifest_loader import JsonRoomManifestLoader
from ascii_duo_snake.presentation.ascii_board_renderer import AsciiBoardRenderer
from promo_config_loader import (
    PromoSceneConfig,
    PromoStoryboardConfig,
    PromoTimingsConfig,
    ScriptedInputConfig,
)

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_CYAN = "\033[36m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"

DIRECTION_TO_WASD = {
    Direction.UP: "W",
    Direction.LEFT: "A",
    Direction.DOWN: "S",
    Direction.RIGHT: "D",
}


class PromoRandomProvider:
    """Determinisztikus `RandomNumberProvider` a kiszámítható promóciós jelenetekhez."""

    def __init__(self, values: list[int]) -> None:
        self._values = values
        self._index = 0

    def next_int(self, upper_exclusive: int) -> int:
        """Visszaadja a következő előre beállított egész számot `[0, upper_exclusive)` között."""
        value = self._values[self._index % len(self._values)]
        self._index += 1
        return value % upper_exclusive


def colorize(text: str, ansi_code: str) -> str:
    """ANSI színkóddal burkolja a szöveget."""
    return f"{ansi_code}{text}{ANSI_RESET}"


def pause_seconds(seconds: float) -> None:
    """Csak pozitív késleltetésnél alszik, így `--fast` módban 0 ms."""
    if seconds > 0.0:
        time.sleep(seconds)


def resolve_effective_timings(timings: PromoTimingsConfig, fast_mode: bool) -> PromoTimingsConfig:
    """`--fast` módban lenullázza az összes időzítést."""
    if fast_mode:
        return PromoTimingsConfig(0.0, 0.0, 0.0)
    return timings


def clear_terminal_if_enabled(clear_screen: bool) -> None:
    """Törli a terminált, ha a megjelenítés engedélyezi."""
    if clear_screen:
        print("\033[H\033[J", end="")


def print_scene_banner(scene: PromoSceneConfig, typewriter_delay: float) -> None:
    """Kiírja a jelenet fejlécét a konfiguráció alapján, opcionális írógép-effekttel."""
    header = f"{scene.phase_badge}: {scene.title}"
    border = colorize("=" * 68, ANSI_CYAN)
    print(f"\n{border}")
    if typewriter_delay > 0.0:
        for char in header:
            print(colorize(char, ANSI_BOLD + ANSI_CYAN), end="", flush=True)
            time.sleep(typewriter_delay)
        print()
    else:
        print(colorize(header, ANSI_BOLD + ANSI_CYAN))
    print(colorize(scene.subtitle, ANSI_DIM))
    print(border)


def print_highlights(highlights: tuple[str, ...]) -> None:
    """Kiírja a jelenethez tartozó oktatási kiemeléseket."""
    for line in highlights:
        print(colorize(f"  * {line}", ANSI_YELLOW))


def format_wasd_badge(active_key: str | None) -> str:
    """Kiemeli az adott tick-ben aktív WASD billentyűt."""
    parts = [
        colorize(f"[{key}]", ANSI_BOLD + ANSI_GREEN) if key == active_key else colorize(f" {key} ", ANSI_DIM)
        for key in ("W", "A", "S", "D")
    ]
    return "WASD: " + " ".join(parts)


def build_initial_world_state(scene: PromoSceneConfig) -> WorldState:
    """A JSON jelenet-konfigurációból felépíti a valódi `WorldState` kezdőállapotot."""
    snakes_by_id = {
        item.player_id: SnakeEntity(item.player_id, (GridPoint(item.x, item.y),), item.direction)
        for item in scene.initial_snakes
    }
    fruit = scene.optional_fruit
    return WorldState(
        room_width=scene.room_width,
        room_height=scene.room_height,
        player_one_snake=snakes_by_id[PlayerId.P1],
        player_two_snake=snakes_by_id[PlayerId.P2],
        fruit_position=GridPoint(fruit.x, fruit.y) if fruit is not None else None,
        fruit_type=fruit.fruit_type if fruit is not None else FruitType.APPLE,
        fruit_spawn_interval_seconds=99.0,
    )


def _index_inputs_by_tick(inputs: tuple[ScriptedInputConfig, ...]) -> dict[int, list[ScriptedInputConfig]]:
    """Tick-sorszám szerint csoportosítja a szkriptelt bemeneteket."""
    grouped: dict[int, list[ScriptedInputConfig]] = {}
    for cmd in inputs:
        grouped.setdefault(cmd.tick, []).append(cmd)
    return grouped


def _run_validation_and_closing_scene(
    scene: PromoSceneConfig,
    timings: PromoTimingsConfig,
    clear_screen: bool,
) -> None:
    """Lefuttatja a manifest-validációs eseteket, a bemenet-naplózót és a zárókártyát."""
    clear_terminal_if_enabled(clear_screen)
    print_scene_banner(scene, timings.typewriter_char_delay_seconds)
    loader = JsonRoomManifestLoader()
    real_manifest = Path(__file__).resolve().parents[1] / "assets" / "room_manifest.json"
    loaded_world = loader.load_initial_world_state(str(real_manifest))
    print(colorize(f"  [OK] {real_manifest.name} -> {loaded_world.room_width}x{loaded_world.room_height}", ANSI_GREEN))

    for case in scene.validation_cases:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            tmp.write(case.payload)
            tmp_path = tmp.name
        try:
            loader.load_initial_world_state(tmp_path)
        except InvalidRoomManifestException as exc:
            print(colorize(f"  [OK] {case.label} -> {exc}", ANSI_YELLOW))
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    recorder = InputRecorderService()
    controller = GameLoopController(loaded_world, PromoRandomProvider([1]), recorder)
    controller.tick_rate_hz = scene.tick_rate_hz
    inputs_by_tick = _index_inputs_by_tick(scene.scripted_inputs)
    for tick in range(scene.steps + 1):
        for cmd in inputs_by_tick.get(tick, []):
            controller.steer_player_snake(cmd.player_id, cmd.direction)
        if tick < scene.steps:
            controller.advance_simulation_tick(1.0 / controller.tick_rate_hz)
    print(colorize(f"  [RECORDER] ({len(recorder.history)} db): {recorder.history}", ANSI_CYAN))
    print_highlights(scene.highlights)

    if scene.closing_layers:
        width = max(len(line) for line in scene.closing_layers) + 4
        border = f"  +{'-' * width}+"
        print(colorize(f"\n{border}", ANSI_BOLD + ANSI_CYAN))
        for idx, line in enumerate(scene.closing_layers):
            style = ANSI_BOLD + ANSI_CYAN if idx == 0 else ANSI_GREEN
            print(colorize(f"  |  {line.ljust(width - 2)}|", style))
        print(colorize(border, ANSI_BOLD + ANSI_CYAN))
    pause_seconds(timings.scene_pause_seconds)


def _run_simulation_scene(
    scene: PromoSceneConfig,
    timings: PromoTimingsConfig,
    clear_screen: bool,
) -> None:
    """Statikus vagy többlépéses élő szimulációs jelenetet futtat konfiguráció alapján."""
    renderer = AsciiBoardRenderer()
    world_state = build_initial_world_state(scene)
    if scene.steps == 0:
        clear_terminal_if_enabled(clear_screen)
        print_scene_banner(scene, timings.typewriter_char_delay_seconds)
        print(renderer.format_board_frame(world_state))
        print_highlights(scene.highlights)
        pause_seconds(timings.scene_pause_seconds)
        return

    controller = GameLoopController(world_state, PromoRandomProvider([0, 0]), InputRecorderService())
    controller.tick_rate_hz = scene.tick_rate_hz
    inputs_by_tick = _index_inputs_by_tick(scene.scripted_inputs)
    has_p1_script = any(cmd.player_id == PlayerId.P1 for cmd in scene.scripted_inputs)

    for step_index in range(scene.steps):
        active_key: str | None = None
        for cmd in inputs_by_tick.get(step_index, []):
            controller.steer_player_snake(cmd.player_id, cmd.direction)
            if cmd.player_id == PlayerId.P1:
                active_key = DIRECTION_TO_WASD[cmd.direction]

        clear_terminal_if_enabled(clear_screen)
        delay = timings.typewriter_char_delay_seconds if step_index == 0 else 0.0
        print_scene_banner(scene, delay)
        if has_p1_script:
            print(f"  {format_wasd_badge(active_key)}   |   tick_rate_hz={controller.tick_rate_hz:.1f} Hz")
        if scene.optional_fruit is not None:
            p1 = controller.current_state.player_one_snake
            print(colorize(f"  Tick #{step_index}: P1 hossz={p1.length}, pending_growth={p1.pending_growth}", ANSI_YELLOW))
        print(renderer.format_board_frame(controller.current_state))
        controller.advance_simulation_tick(1.0 / controller.tick_rate_hz)
        pause_seconds(timings.frame_delay_seconds)

    if controller.current_state.status != GameStatus.RUNNING:
        print(colorize(f"  -> {controller.current_state.status.value}", ANSI_RED))
    print_highlights(scene.highlights)
    pause_seconds(timings.scene_pause_seconds)


def run_promo_storyboard(
    storyboard: PromoStoryboardConfig,
    fast_mode: bool = False,
    loop_forever: bool = False,
) -> None:
    """Végigfuttatja a konfigurációban szereplő összes promóciós jelenetet."""
    timings = resolve_effective_timings(storyboard.timings, fast_mode=fast_mode)
    clear_screen = not fast_mode
    cycle_number = 0
    try:
        while True:
            cycle_number += 1
            for scene in storyboard.scenes:
                if scene.validation_cases or scene.closing_layers:
                    _run_validation_and_closing_scene(scene, timings, clear_screen)
                else:
                    _run_simulation_scene(scene, timings, clear_screen)
            if not loop_forever:
                break
            print(colorize(f"\n--- #{cycle_number} ---", ANSI_CYAN))
    except KeyboardInterrupt:
        print(colorize("\nCtrl+C", ANSI_GREEN))
