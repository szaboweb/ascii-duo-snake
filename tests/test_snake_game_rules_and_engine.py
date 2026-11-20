"""UNIT TESZTEK — 2. előadás: 1 kígyó mozgása, 180° tiltás, falütközés, getter/setter."""

import unittest

from ascii_duo_snake.application.game_loop_controller import GameLoopController
from ascii_duo_snake.domain.game_enums import Direction, GameStatus, PlayerId
from ascii_duo_snake.domain.game_rules_engine import GameRulesEngine
from ascii_duo_snake.domain.grid_point_value import GridPoint
from ascii_duo_snake.domain.snake_entity import SnakeEntity
from ascii_duo_snake.domain.world_state import WorldState
from ascii_duo_snake.presentation.ascii_board_renderer import AsciiBoardRenderer


class PhaseTwoSingleSnakeTests(unittest.TestCase):
    def test_grid_point_addition_and_equality(self) -> None:
        self.assertEqual(GridPoint(5, 7) + GridPoint(1, 0), GridPoint(6, 7))

    def test_snake_rejects_opposite_180_degree_turn(self) -> None:
        snake = SnakeEntity(
            player_id=PlayerId.P1,
            body=(GridPoint(5, 5), GridPoint(4, 5)),
            direction=Direction.RIGHT,
        )
        self.assertEqual(snake.change_direction(Direction.LEFT).direction, Direction.RIGHT)
        self.assertEqual(snake.change_direction(Direction.UP).direction, Direction.UP)

    def test_single_snake_moves_and_hits_wall(self) -> None:
        world = WorldState(
            room_width=10,
            room_height=10,
            player_one_snake=SnakeEntity(
                player_id=PlayerId.P1,
                body=(GridPoint(8, 5), GridPoint(7, 5)),
                direction=Direction.RIGHT,
            ),
        )
        next_world = GameRulesEngine.compute_next_world_state(world)
        self.assertEqual(next_world.status, GameStatus.PLAYER2_WON)

    def test_controller_getter_and_setter_validation(self) -> None:
        world = WorldState(
            room_width=12,
            room_height=12,
            player_one_snake=SnakeEntity(
                player_id=PlayerId.P1,
                body=(GridPoint(5, 5),),
                direction=Direction.RIGHT,
            ),
        )
        controller = GameLoopController(world, tick_rate_hz=8.0)
        self.assertEqual(controller.tick_rate_hz, 8.0)

        controller.tick_rate_hz = 12.0
        self.assertEqual(controller.tick_rate_hz, 12.0)

        with self.assertRaises(ValueError):
            controller.tick_rate_hz = 0.0

        with self.assertRaises(AttributeError):
            controller.current_state = world  # type: ignore[misc]

    def test_renderer_formats_single_snake_room(self) -> None:
        world = WorldState(
            room_width=10,
            room_height=8,
            player_one_snake=SnakeEntity(
                player_id=PlayerId.P1,
                body=(GridPoint(4, 4), GridPoint(3, 4)),
                direction=Direction.RIGHT,
            ),
        )
        frame = AsciiBoardRenderer().format_board_frame(world)
        self.assertIn("#", frame)
        self.assertIn("1", frame)
        self.assertIn("o", frame)


if __name__ == "__main__":
    unittest.main()
