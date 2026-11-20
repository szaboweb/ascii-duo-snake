"""PROMO STORYBOARD — 0 külső függőséges, élő játékmotort futtató bemutató jelenetek.

Ez a modul szigorúan elkülönül a `src/ascii_duo_snake/` rétegektől: kizárólag
fogyasztója a valódi `GameRulesEngine`, `AsciiBoardRenderer`, `JsonRoomManifestLoader`,
`InputRecorderService` és `GameLoopController` osztályoknak.
"""

from dataclasses import dataclass
from pathlib import Path
import tempfile
import time
from typing import Callable

from ascii_duo_snake.application.game_loop_controller import GameLoopController
from ascii_duo_snake.application.input_recorder_service import InputRecorderService
from ascii_duo_snake.domain.domain_exceptions import InvalidRoomManifestException
from ascii_duo_snake.domain.game_enums import Direction, FruitType, PlayerId
from ascii_duo_snake.domain.game_rules_engine import GameRulesEngine
from ascii_duo_snake.domain.grid_point_value import GridPoint
from ascii_duo_snake.domain.snake_entity import SnakeEntity
from ascii_duo_snake.domain.world_state import WorldState
from ascii_duo_snake.infrastructure.json_room_manifest_loader import JsonRoomManifestLoader
from ascii_duo_snake.presentation.ascii_board_renderer import AsciiBoardRenderer

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_CYAN = "\033[36m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"


@dataclass(frozen=True)
class PromoPlaybackConfig:
    """A promóciós bemutató időzítési és megjelenítési beállításai."""

    frame_delay_seconds: float = 0.25
    typewriter_delay_seconds: float = 0.015
    clear_screen: bool = True


@dataclass(frozen=True)
class PromoScene:
    """Egyetlen koreografált előadási jelenet leírása."""

    phase_number: int
    title: str
    subtitle: str
    runner: Callable[[PromoPlaybackConfig], None]


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


def clear_terminal_if_enabled(config: PromoPlaybackConfig) -> None:
    """Törli a terminált, ha a konfiguráció engedélyezi."""
    if config.clear_screen:
        print("\033[H\033[J", end="")


def print_typewriter_banner(title: str, subtitle: str, config: PromoPlaybackConfig) -> None:
    """Kiírja a jelenet címét opcionális írógép-effekttel."""
    border = colorize("=" * 66, ANSI_CYAN)
    print(f"\n{border}")
    if config.typewriter_delay_seconds > 0.0:
        for char in title:
            print(colorize(char, ANSI_BOLD + ANSI_CYAN), end="", flush=True)
            time.sleep(config.typewriter_delay_seconds)
        print()
    else:
        print(colorize(title, ANSI_BOLD + ANSI_CYAN))
    print(colorize(subtitle, ANSI_DIM))
    print(border)


def format_wasd_badge(active_key: str | None) -> str:
    """Kiemeli az épp lenyomott WASD gombot a 2. jelenethez."""
    parts: list[str] = []
    for key in ("W", "A", "S", "D"):
        if key == active_key:
            parts.append(colorize(f"[{key}]", ANSI_BOLD + ANSI_GREEN))
        else:
            parts.append(colorize(f" {key} ", ANSI_DIM))
    return "Billentyűzet: " + " ".join(parts)


def run_scene_one_foundations(config: PromoPlaybackConfig) -> None:
    """1. jelenet — 1. fázis (Alapok): statikus szoba, GridPoint, WorldState, Enum."""
    clear_terminal_if_enabled(config)
    print_typewriter_banner(
        "1. FÁZIS — ALAPOK: Adattípusok és Statikus Szoba",
        "Fogalmak: GridPoint (Value Object), Enum (Direction, PlayerId), WorldState (SSOT)",
        config,
    )
    renderer = AsciiBoardRenderer()
    static_world = WorldState(
        room_width=18,
        room_height=8,
        player_one_snake=SnakeEntity(PlayerId.P1, (GridPoint(4, 4),), Direction.RIGHT),
        player_two_snake=SnakeEntity(PlayerId.P2, (GridPoint(13, 4),), Direction.LEFT),
    )
    print(renderer.format_board_frame(static_world))
    print(colorize("  * GridPoint(4, 4) + GridPoint(1, 0) == GridPoint(5, 4)  [Operator +]", ANSI_YELLOW))
    print(colorize("  * WorldState(frozen=True) -> 100% megváltoztathatatlan SSOT", ANSI_GREEN))
    pause_seconds(config.frame_delay_seconds * 3)


def run_scene_two_single_snake_control(config: PromoPlaybackConfig) -> None:
    """2. jelenet — 2. fázis: WASD irányítás, tick_rate_hz setter és falütközés."""
    renderer = AsciiBoardRenderer()
    initial_world = WorldState(
        room_width=14,
        room_height=8,
        player_one_snake=SnakeEntity(PlayerId.P1, (GridPoint(9, 4),), Direction.RIGHT),
        player_two_snake=SnakeEntity(PlayerId.P2, (GridPoint(2, 2),), Direction.DOWN),
        fruit_spawn_interval_seconds=99.0,
    )
    controller = GameLoopController(
        initial_world_state=initial_world,
        random_provider=PromoRandomProvider([0]),
        input_recorder=InputRecorderService(),
        tick_rate_hz=6.0,
    )
    controller.tick_rate_hz = 12.0
    setter_badge = colorize("[SETTER OK] tick_rate_hz: 6.0 -> 12.0 Hz (1..60 Hz)", ANSI_GREEN)
    scripted_steps: list[tuple[str | None, Direction | None]] = [
        ("W", Direction.UP),
        ("D", Direction.RIGHT),
        ("S", Direction.DOWN),
        ("D", Direction.RIGHT),
        ("D", None),
        ("D", None),
    ]
    for active_key, direction in scripted_steps:
        if direction is not None:
            controller.steer_player_snake(PlayerId.P1, direction)
        controller.advance_simulation_tick(1.0 / controller.tick_rate_hz)
        clear_terminal_if_enabled(config)
        print_typewriter_banner(
            "2. FÁZIS — 1 KÍGYÓ IRÁNYÍTÁSA: WASD, Setter és Falütközés",
            "Fogalmak: Pure Function, GameLoopController, @property + @setter",
            config,
        )
        print(f"  {format_wasd_badge(active_key)}   |   {setter_badge}")
        print(renderer.format_board_frame(controller.current_state))
        pause_seconds(config.frame_delay_seconds)
    print(colorize(f"  -> Falütközés észlelve: {controller.current_state.status.value}", ANSI_RED))
    pause_seconds(config.frame_delay_seconds * 2)


def run_scene_three_duo_fruit_and_head_swap(config: PromoPlaybackConfig) -> None:
    """3. jelenet — 3. fázis: 2 kígyó, GOLDEN_MELON (+3 növekedés) és head-swap (DRAW)."""
    renderer = AsciiBoardRenderer()
    rng = PromoRandomProvider([0, 0])
    world = WorldState(
        room_width=16,
        room_height=8,
        player_one_snake=SnakeEntity(PlayerId.P1, (GridPoint(3, 4),), Direction.RIGHT),
        player_two_snake=SnakeEntity(PlayerId.P2, (GridPoint(12, 2),), Direction.LEFT),
        fruit_position=GridPoint(4, 4),
        fruit_type=FruitType.GOLDEN_MELON,
        fruit_spawn_interval_seconds=99.0,
    )
    for step_index in range(4):
        clear_terminal_if_enabled(config)
        print_typewriter_banner(
            "3. FÁZIS — 2 KÍGYÓ, GYÜMÖLCS & NÖVEKEDÉS (GOLDEN_MELON +3)",
            "Fogalmak: FRUIT_CATALOG, RandomNumberProvider DI, pending_growth, head-swap",
            config,
        )
        p1 = world.player_one_snake
        print(colorize(f"  Lépés #{step_index}: P1 hossz={p1.length}, pending_growth={p1.pending_growth}", ANSI_YELLOW))
        print(renderer.format_board_frame(world))
        pause_seconds(config.frame_delay_seconds)
        world = GameRulesEngine.compute_next_world_state(world, 0.2, rng)

    head_swap_world = WorldState(
        room_width=14,
        room_height=7,
        player_one_snake=SnakeEntity(PlayerId.P1, (GridPoint(6, 3),), Direction.RIGHT),
        player_two_snake=SnakeEntity(PlayerId.P2, (GridPoint(7, 3),), Direction.LEFT),
    )
    swap_result = GameRulesEngine.compute_next_world_state(head_swap_world, 0.2, rng)
    print(colorize(f"  [HEAD-SWAP VÉDELEM] P1(6,3)->(7,3) vs P2(7,3)->(6,3) => {swap_result.status.value.upper()}", ANSI_GREEN))
    pause_seconds(config.frame_delay_seconds * 2)


def run_scene_four_validation_and_architecture(config: PromoPlaybackConfig) -> None:
    """4. jelenet — 4. fázis: Manifest validáció, InputRecorderService és 4 réteg zárókártya."""
    clear_terminal_if_enabled(config)
    print_typewriter_banner(
        "4. FÁZIS — ÁLLAPOT-ELLENŐRZÉS, RECORDER & CLEAN ARCHITECTURE",
        "Fogalmak: JsonRoomManifestLoader, InvalidRoomManifestException, InputRecorderService",
        config,
    )
    loader = JsonRoomManifestLoader()
    real_manifest = Path(__file__).resolve().parents[1] / "assets" / "room_manifest.json"
    loaded_world = loader.load_initial_world_state(str(real_manifest))
    print(colorize(f"  [OK] Valódi manifest betöltve: {loaded_world.room_width}x{loaded_world.room_height}", ANSI_GREEN))

    bad_cases = [
        ("Falon lévő P1 spawn", '{"width": 20, "height": 15, "p1Start": {"x": 0, "y": 5}, "p2Start": {"x": 10, "y": 5}}'),
        ("Ütköző kezdőpontok", '{"width": 20, "height": 15, "p1Start": {"x": 5, "y": 5}, "p2Start": {"x": 5, "y": 5}}'),
    ]
    for label, payload in bad_cases:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            tmp.write(payload)
            tmp_path = tmp.name
        try:
            loader.load_initial_world_state(tmp_path)
        except InvalidRoomManifestException as exc:
            print(colorize(f"  [OK] elkapva! ({label}) -> {exc}", ANSI_YELLOW))
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    recorder = InputRecorderService()
    controller = GameLoopController(loaded_world, PromoRandomProvider([1]), recorder)
    controller.steer_player_snake(PlayerId.P1, Direction.UP)
    controller.advance_simulation_tick(0.2)
    controller.steer_player_snake(PlayerId.P2, Direction.DOWN)
    print(colorize(f"  [RECORDER] InputRecorderService.history ({len(recorder.history)} db): {recorder.history}", ANSI_CYAN))

    print(colorize("\n  +--------------------------------------------------------------+", ANSI_BOLD + ANSI_CYAN))
    print(colorize("  |  4 RÉTEGŰ CLEAN ARCHITECTURE (Nyilak mindig befelé!)         |", ANSI_BOLD + ANSI_CYAN))
    print(colorize("  |  4. Presentation -> 2. Application -> 1. Domain (0 I/O)      |", ANSI_GREEN))
    print(colorize("  |  3. Infrastructure (JSON, RNG) -----> 1. Domain (Protocol)   |", ANSI_GREEN))
    print(colorize("  +--------------------------------------------------------------+", ANSI_BOLD + ANSI_CYAN))
    pause_seconds(config.frame_delay_seconds * 3)


def build_promo_scenes() -> tuple[PromoScene, ...]:
    """Visszaadja a 4 koreografált promóciós jelenet listáját."""
    return (
        PromoScene(1, "1. fázis — Alapok", "Statikus szoba, GridPoint, WorldState, Enum", run_scene_one_foundations),
        PromoScene(2, "2. fázis — 1 kígyó irányítása", "WASD, setter és falütközés", run_scene_two_single_snake_control),
        PromoScene(3, "3. fázis — 2 kígyó & növekedés", "GOLDEN_MELON +3 és head-swap DRAW", run_scene_three_duo_fruit_and_head_swap),
        PromoScene(4, "4. fázis — Validáció & Architektúra", "Manifest, Exception, Recorder, 4 réteg", run_scene_four_validation_and_architecture),
    )
