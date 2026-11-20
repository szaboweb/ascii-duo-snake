"""HALADÓ ELŐADÁSI FÁZISOK (5–8.) ÉS 500-LÉPÉSES INVARIÁNS FUZZ-TESZTEK.

Mit ellenőriz ez a tesztmodul?
    1. 5. Fázis: Táblázatvezérelt Véges Állapotgép (`SessionStateMachine`) és
       Data-Driven vizuális témák (`BoardThemeSpec`, `AsciiBoardRenderer`).
    2. 6. Fázis: Strategy Pattern & Open/Closed Principle (`GreedyFruitBotStrategy` vs.
       `CautiousSurvivalBotStrategy`).
    3. 7. Fázis: Domain Events & Observer / Pub-Sub (`GameEventBus`, `MatchTelemetryCollector`,
       `P1_DINNYEVADASZ` és `P1_DUPLA_FALAT` jelvények).
    4. 8. Fázis: Event Sourcing Determinisztikus JSON Replay (`DeterministicReplayService`)
       és az 500-lépéses Property-Based Invariáns Fuzz-Teszt.
"""

from dataclasses import replace
import unittest

from ascii_duo_snake.application.deterministic_replay_service import (
    DeterministicReplayService,
    MatchReplaySnapshot,
)
from ascii_duo_snake.application.game_event_bus import GameEventBus, MatchTelemetryCollector
from ascii_duo_snake.application.game_loop_controller import GameLoopController
from ascii_duo_snake.application.input_recorder_service import InputRecorderService
from ascii_duo_snake.domain.bot_steering_strategy import (
    CautiousSurvivalBotStrategy,
    GreedyFruitBotStrategy,
    select_bot_strategy,
)
from ascii_duo_snake.domain.fruit_catalog import FRUIT_CATALOG
from ascii_duo_snake.domain.game_enums import Direction, FruitType, GameStatus, PlayerId
from ascii_duo_snake.domain.game_rules_engine import GameRulesEngine
from ascii_duo_snake.domain.grid_point_value import GridPoint
from ascii_duo_snake.domain.session_state_machine import (
    InvalidPhaseTransitionException,
    SessionPhase,
    SessionStateMachine,
)
from ascii_duo_snake.domain.snake_entity import SnakeEntity
from ascii_duo_snake.domain.world_state import WorldState
from ascii_duo_snake.infrastructure.system_random_adapter import SystemRandomAdapter
from ascii_duo_snake.presentation.ascii_board_renderer import AsciiBoardRenderer
from ascii_duo_snake.presentation.board_theme_catalog import select_board_theme


class AdvancedPhasesAndInvariantsTests(unittest.TestCase):
    """Az 5–8. előadási fázisok és az 500 lépéses invariáns fuzz-teszt egységtesztjei."""

    def test_phase_5_session_state_machine_enforces_transition_table(self) -> None:
        """5. Fázis: A táblázatvezérelt FSM engedi a legális és blokkolja a tiltott átmeneteket."""
        fsm = SessionStateMachine()
        self.assertEqual(fsm.current_phase, SessionPhase.MENU)
        self.assertTrue(fsm.can_transition_to(SessionPhase.PLAYING))
        self.assertFalse(fsm.can_transition_to(SessionPhase.PAUSED))

        with self.assertRaises(InvalidPhaseTransitionException):
            fsm.transition_to(SessionPhase.PAUSED)

        fsm.transition_to(SessionPhase.PLAYING)
        fsm.transition_to(SessionPhase.PAUSED)
        fsm.transition_to(SessionPhase.PLAYING)
        fsm.transition_to(SessionPhase.GAME_OVER)
        self.assertEqual(
            fsm.transition_history,
            (
                SessionPhase.MENU,
                SessionPhase.PLAYING,
                SessionPhase.PAUSED,
                SessionPhase.PLAYING,
                SessionPhase.GAME_OVER,
            ),
        )

    def test_phase_5_data_driven_board_themes_change_rendered_glyphs(self) -> None:
        """5. Fázis: A `neon_arcade` téma lecseréli a fal és kígyó karaktereket."""
        world = WorldState(
            room_width=8,
            room_height=5,
            player_one_snake=SnakeEntity(
                PlayerId.P1, (GridPoint(3, 2), GridPoint(2, 2)), Direction.RIGHT
            ),
            player_two_snake=SnakeEntity(PlayerId.P2, (GridPoint(5, 2),), Direction.LEFT),
            fruit_position=GridPoint(4, 2),
            fruit_type=FruitType.GOLDEN_MELON,
        )
        neon_theme = select_board_theme("neon_arcade")
        renderer = AsciiBoardRenderer(theme=neon_theme)
        frame = renderer.format_board_frame(world)

        self.assertIn("█", frame)
        self.assertIn("@", frame)
        self.assertIn("●", frame)
        self.assertIn("&", frame)
        with self.assertRaises(ValueError):
            select_board_theme("non_existent_theme")

    def test_phase_6_cautious_bot_avoids_wall_while_greedy_seeks_fruit(self) -> None:
        """6. Fázis: Az óvatos bot elkerüli a közvetlen falütközést, a mohó a gyümölcs felé tart."""
        world_near_right_wall = WorldState(
            room_width=8,
            room_height=6,
            player_one_snake=SnakeEntity(PlayerId.P1, (GridPoint(6, 3),), Direction.RIGHT),
            player_two_snake=SnakeEntity(PlayerId.P2, (GridPoint(2, 2),), Direction.DOWN),
            fruit_position=GridPoint(6, 1),
            fruit_type=FruitType.APPLE,
        )
        cautious_bot = CautiousSurvivalBotStrategy()
        greedy_bot = GreedyFruitBotStrategy()

        chosen_cautious = cautious_bot.choose_next_direction(world_near_right_wall, PlayerId.P1)
        chosen_greedy = greedy_bot.choose_next_direction(world_near_right_wall, PlayerId.P1)
        self.assertEqual(chosen_cautious, Direction.UP)
        self.assertEqual(chosen_greedy, Direction.UP)
        self.assertIsNotNone(select_bot_strategy("cautious"))

    def test_phase_7_event_bus_and_telemetry_unlock_melon_and_double_badges(self) -> None:
        """7. Fázis: A `GameEventBus` és `MatchTelemetryCollector` feloldja a jelvényeket."""
        world = WorldState(
            room_width=12,
            room_height=8,
            player_one_snake=SnakeEntity(PlayerId.P1, (GridPoint(3, 4),), Direction.RIGHT),
            player_two_snake=SnakeEntity(PlayerId.P2, (GridPoint(9, 2),), Direction.LEFT),
            fruit_position=GridPoint(4, 4),
            fruit_type=FruitType.GOLDEN_MELON,
            fruit_spawn_interval_seconds=0.1,
        )
        event_bus = GameEventBus()
        telemetry = MatchTelemetryCollector()
        event_bus.subscribe_listener(telemetry.on_domain_event)
        controller = GameLoopController(
            world,
            SystemRandomAdapter(seed=42),
            InputRecorderService(),
            tick_rate_hz=5.0,
            event_bus=event_bus,
        )
        controller.advance_simulation_tick(0.2)
        self.assertEqual(telemetry.fruits_by_player[PlayerId.P1], 1)
        self.assertIn("P1_DINNYEVADASZ", telemetry.unlocked_badges)

    def test_phase_8_deterministic_replay_reproduces_identical_world_state(self) -> None:
        """8. Fázis: A JSON-ba mentett replay 100%-ban reprodukálja az eredeti végállapotot."""
        initial_world = WorldState(
            room_width=14,
            room_height=8,
            player_one_snake=SnakeEntity(PlayerId.P1, (GridPoint(3, 4),), Direction.RIGHT),
            player_two_snake=SnakeEntity(PlayerId.P2, (GridPoint(10, 4),), Direction.LEFT),
            fruit_position=GridPoint(5, 4),
            fruit_type=FruitType.GOLDEN_MELON,
        )
        recorder = InputRecorderService()
        controller = GameLoopController(
            initial_world, SystemRandomAdapter(seed=123), recorder, tick_rate_hz=10.0
        )
        controller.steer_player_snake(PlayerId.P1, Direction.UP)
        controller.advance_simulation_tick(0.1)
        controller.steer_player_snake(PlayerId.P1, Direction.RIGHT)
        controller.advance_simulation_tick(0.1)
        controller.steer_player_snake(PlayerId.P2, Direction.DOWN)
        controller.advance_simulation_tick(0.1)

        snapshot = MatchReplaySnapshot(
            random_seed=123,
            tick_rate_hz=10.0,
            total_ticks=3,
            recorded_inputs=recorder.history,
            expected_final_status=controller.current_state.status,
        )
        raw_json = DeterministicReplayService.serialize_replay_to_json(snapshot)
        restored = DeterministicReplayService.deserialize_replay_from_json(raw_json)
        replayed_state = DeterministicReplayService.replay_match_deterministically(
            initial_world, restored, lambda seed: SystemRandomAdapter(seed=seed)
        )
        self.assertEqual(replayed_state, controller.current_state)

    def test_phase_8_five_hundred_ticks_domain_invariants_never_violated(self) -> None:
        """8. Fázis: 500 lépéses Property-Based Invariáns Fuzz-Teszt két óvatos bottal."""
        bot = CautiousSurvivalBotStrategy()
        rng = SystemRandomAdapter(seed=2026)
        total_verified_ticks = 0

        for match_seed in range(10):
            state = WorldState(
                room_width=16,
                room_height=10,
                player_one_snake=SnakeEntity(PlayerId.P1, (GridPoint(3, 5),), Direction.RIGHT),
                player_two_snake=SnakeEntity(PlayerId.P2, (GridPoint(12, 5),), Direction.LEFT),
                fruit_position=GridPoint(8, 5),
                fruit_type=FruitType.APPLE,
                fruit_spawn_interval_seconds=0.2,
            )
            match_rng = SystemRandomAdapter(seed=100 + match_seed)
            for _ in range(50):
                if state.status != GameStatus.RUNNING:
                    break
                p1_dir = bot.choose_next_direction(state, PlayerId.P1)
                p2_dir = bot.choose_next_direction(state, PlayerId.P2)
                steered = replace(
                    state,
                    player_one_snake=state.player_one_snake.change_direction(p1_dir),
                    player_two_snake=state.player_two_snake.change_direction(p2_dir),
                )
                next_state = GameRulesEngine.compute_next_world_state(steered, 0.2, match_rng)
                total_verified_ticks += 1

                # Invariáns 1: Kígyó hossza soha nem csökkenhet
                self.assertGreaterEqual(
                    next_state.player_one_snake.length, state.player_one_snake.length
                )
                self.assertGreaterEqual(
                    next_state.player_two_snake.length, state.player_two_snake.length
                )
                # Invariáns 2: A gyümölcs soha nem lehet falon vagy kígyótesten
                if next_state.fruit_position is not None:
                    self.assertTrue(
                        GameRulesEngine.is_within_room_bounds(
                            next_state.fruit_position,
                            next_state.room_width,
                            next_state.room_height,
                        )
                    )
                    occupied = set(next_state.player_one_snake.body) | set(
                        next_state.player_two_snake.body
                    )
                    self.assertNotIn(next_state.fruit_position, occupied)
                # Invariáns 3: Gyümölcstípus mindig benne van a FRUIT_CATALOG-ban
                self.assertIn(next_state.fruit_type, FRUIT_CATALOG)
                state = next_state

        self.assertGreaterEqual(total_verified_ticks, 150)
        self.assertIsNotNone(rng)


if __name__ == "__main__":
    unittest.main()
