"""UNIT TEST & MOCK (1-3. előadás): Headless szabálymotor, DI és regressziós tesztek."""

import unittest

from ascii_duo_snake.application.game_loop_controller import GameLoopController
from ascii_duo_snake.domain.game_enums import Direction, FruitType, GameStatus, PlayerId
from ascii_duo_snake.domain.game_rules_engine import GameRulesEngine
from ascii_duo_snake.domain.grid_point_value import GridPoint
from ascii_duo_snake.domain.snake_entity import SnakeEntity, is_opposite_direction
from ascii_duo_snake.domain.world_state import WorldState


class FakeRandomNumberProvider:
    """MOCK (`RandomNumberProvider`): Determinisztikus véletlen teszteléshez."""

    def __init__(self, values: list[int]) -> None:
        self._values = values
        self._next_index = 0

    def next_int(self, upper_exclusive: int) -> int:
        selected_value = self._values[self._next_index % len(self._values)]
        self._next_index += 1
        return selected_value % upper_exclusive


class SnakeGameRulesAndEngineTests(unittest.TestCase):
    def test_wall_collision_player_one_loses(self) -> None:
        initial_world_state = WorldState(
            room_width=10,
            room_height=10,
            player_one_snake=SnakeEntity(
                player_id=PlayerId.P1,
                body=(GridPoint(8, 5),),
                direction=Direction.RIGHT,
            ),
            player_two_snake=SnakeEntity(
                player_id=PlayerId.P2,
                body=(GridPoint(2, 5),),
                direction=Direction.LEFT,
            ),
        )
        next_world_state = GameRulesEngine.compute_next_world_state(
            world_state=initial_world_state,
            delta_seconds=0.2,
            random_provider=FakeRandomNumberProvider([3]),
        )
        self.assertEqual(next_world_state.status, GameStatus.PLAYER2_WON)

    def test_snake_collision_player_two_hits_player_one_body(self) -> None:
        initial_world_state = WorldState(
            room_width=12,
            room_height=12,
            player_one_snake=SnakeEntity(
                player_id=PlayerId.P1,
                body=(GridPoint(5, 5), GridPoint(5, 6), GridPoint(5, 7)),
                direction=Direction.UP,
            ),
            player_two_snake=SnakeEntity(
                player_id=PlayerId.P2,
                body=(GridPoint(6, 6),),
                direction=Direction.LEFT,
            ),
        )
        next_world_state = GameRulesEngine.compute_next_world_state(
            world_state=initial_world_state,
            delta_seconds=0.2,
            random_provider=FakeRandomNumberProvider([2]),
        )
        self.assertEqual(next_world_state.status, GameStatus.PLAYER1_WON)

    def test_head_swap_tunneling_is_detected_as_draw(self) -> None:
        """Regressziós teszt: két 1 hosszú kígyó nem csúszhat át egymáson."""
        initial_world_state = WorldState(
            room_width=12,
            room_height=12,
            player_one_snake=SnakeEntity(
                player_id=PlayerId.P1,
                body=(GridPoint(5, 5),),
                direction=Direction.RIGHT,
            ),
            player_two_snake=SnakeEntity(
                player_id=PlayerId.P2,
                body=(GridPoint(6, 5),),
                direction=Direction.LEFT,
            ),
        )
        next_world_state = GameRulesEngine.compute_next_world_state(
            world_state=initial_world_state,
            delta_seconds=0.2,
            random_provider=FakeRandomNumberProvider([0]),
        )
        self.assertEqual(next_world_state.status, GameStatus.DRAW)

    def test_opposite_direction_predicate_blocks_reversal(self) -> None:
        self.assertTrue(is_opposite_direction(Direction.RIGHT, Direction.LEFT))
        self.assertFalse(is_opposite_direction(Direction.RIGHT, Direction.UP))

    def test_golden_melon_grows_snake_by_three(self) -> None:
        world_state = WorldState(
            room_width=15,
            room_height=15,
            player_one_snake=SnakeEntity(
                player_id=PlayerId.P1,
                body=(GridPoint(4, 5),),
                direction=Direction.RIGHT,
            ),
            player_two_snake=SnakeEntity(
                player_id=PlayerId.P2,
                body=(GridPoint(12, 10),),
                direction=Direction.LEFT,
            ),
            fruit_position=GridPoint(5, 5),
            fruit_type=FruitType.GOLDEN_MELON,
        )
        random_provider = FakeRandomNumberProvider([0, 0])
        for _ in range(3):
            world_state = GameRulesEngine.compute_next_world_state(
                world_state=world_state,
                delta_seconds=0.2,
                random_provider=random_provider,
            )

        self.assertEqual(world_state.player_one_snake.fruits_eaten, 1)
        self.assertEqual(world_state.player_one_snake.length, 4)

    def test_fruit_spawns_only_on_free_cells_or_none_when_full(self) -> None:
        """Regressziós teszt: gyümölcs sosem kerülhet kígyóra, teli pályán None."""
        world_state = WorldState(
            room_width=4,
            room_height=4,
            player_one_snake=SnakeEntity(
                player_id=PlayerId.P1,
                body=(GridPoint(1, 1), GridPoint(1, 2)),
                direction=Direction.RIGHT,
            ),
            player_two_snake=SnakeEntity(
                player_id=PlayerId.P2,
                body=(GridPoint(2, 2),),
                direction=Direction.LEFT,
            ),
            fruit_spawn_interval_seconds=3.0,
        )
        next_world_state = GameRulesEngine.compute_next_world_state(
            world_state=world_state,
            delta_seconds=3.0,
            random_provider=FakeRandomNumberProvider([0, 0]),
        )
        self.assertEqual(next_world_state.fruit_position, GridPoint(2, 2))

        full_player_one_snake = SnakeEntity(
            player_id=PlayerId.P1,
            body=(GridPoint(1, 1), GridPoint(2, 1)),
            direction=Direction.RIGHT,
        )
        full_player_two_snake = SnakeEntity(
            player_id=PlayerId.P2,
            body=(GridPoint(1, 2), GridPoint(2, 2)),
            direction=Direction.LEFT,
        )
        self.assertIsNone(
            GameRulesEngine.select_free_fruit_position(
                room_width=4,
                room_height=4,
                player_one_snake=full_player_one_snake,
                player_two_snake=full_player_two_snake,
                random_provider=FakeRandomNumberProvider([0]),
            )
        )

    def test_getter_setter_and_invalid_player_id_guard(self) -> None:
        initial_world_state = WorldState(
            room_width=12,
            room_height=12,
            player_one_snake=SnakeEntity(
                player_id=PlayerId.P1,
                body=(GridPoint(3, 5),),
                direction=Direction.RIGHT,
            ),
            player_two_snake=SnakeEntity(
                player_id=PlayerId.P2,
                body=(GridPoint(8, 5),),
                direction=Direction.LEFT,
            ),
        )
        controller = GameLoopController(
            initial_world_state=initial_world_state,
            random_provider=FakeRandomNumberProvider([1]),
            tick_rate_hz=8.0,
        )

        self.assertEqual(controller.tick_rate_hz, 8.0)
        controller.tick_rate_hz = 12.0
        self.assertEqual(controller.tick_rate_hz, 12.0)

        with self.assertRaises(ValueError):
            controller.tick_rate_hz = 0.0

        with self.assertRaises(AttributeError):
            controller.current_state = initial_world_state  # type: ignore[misc]

        with self.assertRaises(ValueError):
            controller.steer_player_snake("P3", Direction.UP)  # type: ignore[arg-type]

        controller.steer_player_snake(PlayerId.P1, Direction.UP)
        controller.steer_player_snake(PlayerId.P2, Direction.DOWN)
        self.assertEqual(controller.current_state.player_one_snake.direction, Direction.UP)
        self.assertEqual(controller.current_state.player_two_snake.direction, Direction.DOWN)


if __name__ == "__main__":
    unittest.main()
