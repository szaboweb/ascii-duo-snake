"""1. DOMAIN RÉTEG — PURE FUNCTIONS & GAME RULES (2. előadás: 1 kígyó mozgása).

Pure Function (Tiszta függvény):
    A `compute_next_world_state()` nem ír képernyőre és nem változtatja meg
    a régi `WorldState`-et — mindig egy ÚJ pillanatképet ad vissza.
"""

from dataclasses import replace

from .game_enums import Direction, GameStatus
from .grid_point_value import GridPoint
from .snake_entity import SnakeEntity
from .world_state import WorldState

DIRECTION_DELTAS: dict[Direction, GridPoint] = {
    Direction.UP: GridPoint(0, -1),
    Direction.DOWN: GridPoint(0, 1),
    Direction.LEFT: GridPoint(-1, 0),
    Direction.RIGHT: GridPoint(1, 0),
}


class GameRulesEngine:
    """Állapotmentes (stateless) szabálymotor 1 kígyó mozgásához és ütközéséhez."""

    @staticmethod
    def compute_next_world_state(world_state: WorldState) -> WorldState:
        """Kiszámít egyetlen időlépést (tick-et): régi `WorldState` -> új `WorldState`."""
        if world_state.status != GameStatus.RUNNING:
            return world_state

        player_one_next_head = (
            world_state.player_one_snake.head
            + DIRECTION_DELTAS[world_state.player_one_snake.direction]
        )
        moved_player_one = GameRulesEngine.advance_snake_body(
            world_state.player_one_snake,
            player_one_next_head,
        )

        if GameRulesEngine.has_snake_crashed(player_one_next_head, moved_player_one, world_state):
            return replace(world_state, status=GameStatus.PLAYER2_WON)

        return replace(
            world_state,
            player_one_snake=moved_player_one,
            tick=world_state.tick + 1,
        )

    @staticmethod
    def advance_snake_body(snake_entity: SnakeEntity, next_head_position: GridPoint) -> SnakeEntity:
        """Előrelépteti a kígyót egy mezővel: új fej elöl, farok levágva hátul."""
        next_body = (next_head_position, *snake_entity.body[:-1])
        return replace(snake_entity, body=next_body)

    @staticmethod
    def has_snake_crashed(
        head_position: GridPoint,
        own_snake: SnakeEntity,
        world_state: WorldState,
    ) -> bool:
        """Tiszta predikátum: igaz, ha a fej falnak vagy saját testének ütközött."""
        hit_wall = (
            head_position.x <= 0
            or head_position.x >= world_state.room_width - 1
            or head_position.y <= 0
            or head_position.y >= world_state.room_height - 1
        )
        hit_self = head_position in own_snake.body[1:]
        return hit_wall or hit_self
