"""Headless unit tesztek (Phase 1: Value Object, Entity getterek, statikus megjelenítés)."""

import unittest

from ascii_duo_snake.domain.game_enums import Direction, PlayerId
from ascii_duo_snake.domain.grid_point_value import GridPoint
from ascii_duo_snake.domain.snake_entity import SnakeEntity
from ascii_duo_snake.domain.world_state import WorldState
from ascii_duo_snake.presentation.ascii_board_renderer import AsciiBoardRenderer


class TestPhaseOneDataModelAndRenderer(unittest.TestCase):
    """Ellenőrzi az 1. fázis adattípusait és a statikus szoba formázását."""

    def test_grid_point_addition_and_equality(self) -> None:
        origin = GridPoint(5, 7)
        step = GridPoint(1, -2)

        result = origin + step

        self.assertEqual(result, GridPoint(6, 5))
        self.assertEqual(GridPoint(6, 5), result)
        self.assertNotEqual(origin, result)

    def test_snake_entity_head_and_length_getters(self) -> None:
        player_one_snake = SnakeEntity(
            player_id=PlayerId.P1,
            body=(GridPoint(5, 5), GridPoint(4, 5), GridPoint(3, 5)),
            direction=Direction.RIGHT,
        )

        self.assertEqual(player_one_snake.head, GridPoint(5, 5))
        self.assertEqual(player_one_snake.length, 3)

    def test_ascii_board_renderer_formats_walls_and_player_one_snake(self) -> None:
        player_one_snake = SnakeEntity(
            player_id=PlayerId.P1,
            body=(GridPoint(3, 2), GridPoint(2, 2)),
            direction=Direction.RIGHT,
        )
        world_state = WorldState(
            room_width=8,
            room_height=5,
            player_one_snake=player_one_snake,
        )
        board_renderer = AsciiBoardRenderer()

        frame_text = board_renderer.format_board_frame(world_state)

        self.assertIn("########", frame_text)
        self.assertIn("# o1   #", frame_text)
        self.assertIn("P1 Hossz: 2", frame_text)


if __name__ == "__main__":
    unittest.main()
