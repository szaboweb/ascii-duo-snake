"""1. DOMAIN RÉTEG — PURE FUNCTIONS & GAME RULES (A játék szíve).

Mi az a Pure Function (Tiszta függvény)?
    1. Az eredménye kizárólag a bemeneti paramétereitől függ
       (`world_state`, `delta_seconds`, `random_provider`).
    2. Nincs mellékhatása: nem ír képernyőre (`print`), nem olvas fájlt/billentyűzetet,
       és nem írja át a kapott `WorldState` objektumot — mindig egy ÚJAT ad vissza.

Miért óriási előny ez?
    Mivel a `GameRulesEngine.compute_next_world_state()` tiszta függvény, ezerszer is
    lefuttatható egy ezredmásodperc alatt terminál nélkül (headless tesztek, replay, AI szimuláció).
"""

from dataclasses import replace
from types import MappingProxyType
from typing import Mapping

from .domain_contracts import RandomNumberProvider
from .fruit_catalog import FRUIT_CATALOG
from .game_enums import Direction, FruitType, GameStatus
from .grid_point_value import GridPoint
from .snake_entity import SnakeEntity
from .world_state import WorldState

# Irány -> elmozdulás vektor (0, 0 a bal felső sarok, Y lefelé növekszik)
DIRECTION_DELTAS: Mapping[Direction, GridPoint] = MappingProxyType(
    {
        Direction.UP: GridPoint(0, -1),
        Direction.DOWN: GridPoint(0, 1),
        Direction.LEFT: GridPoint(-1, 0),
        Direction.RIGHT: GridPoint(1, 0),
    }
)

AVAILABLE_FRUIT_TYPES: tuple[FruitType, ...] = tuple(FRUIT_CATALOG.keys())


class GameRulesEngine:
    """A játék összes szabályát összefogó, állapotmentes (stateless) szabálymotor."""

    @staticmethod
    def compute_next_world_state(
        world_state: WorldState,
        delta_seconds: float,
        random_provider: RandomNumberProvider,
    ) -> WorldState:
        """Kiszámít egyetlen időlépést (tick-et): régi `WorldState` -> új `WorldState`.

        A lépés 4 tiszta fázisra tagolódik:
            1. Következő fejpozíciók kiszámítása a `GridPoint + GridPoint` operátorral.
            2. Gyümölcsevés és kígyók léptetése (`advance_snake_body`).
            3. Ütközésvizsgálat (fal, másik kígyó, saját test, és fej-helycsere).
            4. Gyümölcs-időzítő frissítése és új gyümölcs elhelyezése szabad mezőre.
        """
        if world_state.status != GameStatus.RUNNING:
            return world_state

        # 1. Következő fejpozíciók kiszámítása OPERATOR (+) segítségével
        player_one_next_head = (
            world_state.player_one_snake.head
            + DIRECTION_DELTAS[world_state.player_one_snake.direction]
        )
        player_two_next_head = (
            world_state.player_two_snake.head
            + DIRECTION_DELTAS[world_state.player_two_snake.direction]
        )

        # 2. CONDITION: Gyümölcsevés ellenőrzése és mozgatás
        player_one_ate_fruit = (
            world_state.fruit_position is not None
            and player_one_next_head == world_state.fruit_position
        )
        player_two_ate_fruit = (
            world_state.fruit_position is not None
            and player_two_next_head == world_state.fruit_position
        )
        fruit_growth_amount = FRUIT_CATALOG[world_state.fruit_type].growth_amount

        moved_player_one_snake = GameRulesEngine.advance_snake_body(
            world_state.player_one_snake,
            player_one_next_head,
            fruit_growth_amount if player_one_ate_fruit else 0,
        )
        moved_player_two_snake = GameRulesEngine.advance_snake_body(
            world_state.player_two_snake,
            player_two_next_head,
            fruit_growth_amount if player_two_ate_fruit else 0,
        )

        # 3. CONDITION: Ütközésvizsgálat
        head_swap_occurred = GameRulesEngine.is_head_swap_collision(
            player_one_next_head=player_one_next_head,
            player_two_next_head=player_two_next_head,
            player_one_previous_head=world_state.player_one_snake.head,
            player_two_previous_head=world_state.player_two_snake.head,
        )
        player_one_crashed = head_swap_occurred or GameRulesEngine.has_snake_crashed(
            head_position=player_one_next_head,
            own_snake=moved_player_one_snake,
            opponent_snake=moved_player_two_snake,
            room_width=world_state.room_width,
            room_height=world_state.room_height,
        )
        player_two_crashed = head_swap_occurred or GameRulesEngine.has_snake_crashed(
            head_position=player_two_next_head,
            own_snake=moved_player_two_snake,
            opponent_snake=moved_player_one_snake,
            room_width=world_state.room_width,
            room_height=world_state.room_height,
        )

        if player_one_crashed and player_two_crashed:
            return replace(world_state, status=GameStatus.DRAW)
        if player_one_crashed:
            return replace(world_state, status=GameStatus.PLAYER2_WON)
        if player_two_crashed:
            return replace(world_state, status=GameStatus.PLAYER1_WON)

        # 4. CONDITION: Új gyümölcs generálása a manifest szerinti időközönként (pl. 3.0 mp)
        elapsed_fruit_timer_seconds = world_state.time_since_last_fruit_seconds + delta_seconds
        next_fruit_position = (
            None if (player_one_ate_fruit or player_two_ate_fruit) else world_state.fruit_position
        )
        next_fruit_type = world_state.fruit_type

        if (
            next_fruit_position is None
            and elapsed_fruit_timer_seconds >= world_state.fruit_spawn_interval_seconds
        ):
            elapsed_fruit_timer_seconds = 0.0
            next_fruit_position = GameRulesEngine.select_free_fruit_position(
                room_width=world_state.room_width,
                room_height=world_state.room_height,
                player_one_snake=moved_player_one_snake,
                player_two_snake=moved_player_two_snake,
                random_provider=random_provider,
            )
            if next_fruit_position is not None:
                fruit_type_index = random_provider.next_int(len(AVAILABLE_FRUIT_TYPES))
                next_fruit_type = AVAILABLE_FRUIT_TYPES[fruit_type_index]

        return replace(
            world_state,
            player_one_snake=moved_player_one_snake,
            player_two_snake=moved_player_two_snake,
            fruit_position=next_fruit_position,
            fruit_type=next_fruit_type,
            time_since_last_fruit_seconds=elapsed_fruit_timer_seconds,
            tick=world_state.tick + 1,
        )

    @staticmethod
    def advance_snake_body(
        snake: SnakeEntity,
        next_head_position: GridPoint,
        eaten_growth_amount: int,
    ) -> SnakeEntity:
        """Előrelépteti a kígyót egy mezővel, és kezeli a több-lépéses növekedést.

        Logika:
            - Normál mozgásnál elöl hozzáadjuk az új fejet, hátul levágjuk a farkat (`body[:-1]`).
            - Ha van hátralévő növekedés (`pending_growth + eaten_growth_amount > 0`), NEM vágjuk le
              a farkat, így a kígyó 1 egységgel hosszabb lesz, és 1-gyel csökkentjük a tartalékot.
            - Így a `GOLDEN_MELON` (+3) pontosan 3 egymást követő lépésben növeszti a kígyót.
        """
        total_pending_growth = snake.pending_growth + eaten_growth_amount
        if total_pending_growth > 0:
            updated_body = (next_head_position, *snake.body)
            remaining_growth = total_pending_growth - 1
        else:
            updated_body = (next_head_position, *snake.body[:-1])
            remaining_growth = 0

        return replace(
            snake,
            body=updated_body,
            fruits_eaten=snake.fruits_eaten + (1 if eaten_growth_amount > 0 else 0),
            pending_growth=remaining_growth,
        )

    @staticmethod
    def is_within_room_bounds(
        cell_position: GridPoint,
        room_width: int,
        room_height: int,
    ) -> bool:
        """Tiszta predikátum: igazat ad vissza, ha a mező a szoba belső, falmentes területén van."""
        return 1 <= cell_position.x <= room_width - 2 and 1 <= cell_position.y <= room_height - 2

    @staticmethod
    def is_head_swap_collision(
        player_one_next_head: GridPoint,
        player_two_next_head: GridPoint,
        player_one_previous_head: GridPoint,
        player_two_previous_head: GridPoint,
    ) -> bool:
        """Tiszta predikátum: elkapja, ha két kígyó szemből helyet cserélne (tunneling bug)."""
        return (
            player_one_next_head == player_two_previous_head
            and player_two_next_head == player_one_previous_head
        )

    @staticmethod
    def has_snake_crashed(
        head_position: GridPoint,
        own_snake: SnakeEntity,
        opponent_snake: SnakeEntity,
        room_width: int,
        room_height: int,
    ) -> bool:
        """Tiszta predikátum: igazat ad vissza, ha a fej falba, ellenfélbe vagy saját testébe ütközött."""
        hit_wall = not GameRulesEngine.is_within_room_bounds(
            head_position,
            room_width=room_width,
            room_height=room_height,
        )
        hit_opponent = head_position in opponent_snake.body
        hit_self = head_position in own_snake.body[1:]
        return hit_wall or hit_opponent or hit_self

    @staticmethod
    def select_free_fruit_position(
        room_width: int,
        room_height: int,
        player_one_snake: SnakeEntity,
        player_two_snake: SnakeEntity,
        random_provider: RandomNumberProvider,
    ) -> GridPoint | None:
        """Garantáltan ütközésmentes gyümölcs-elhelyezés a valóban szabad mezőkből.

        Miért jobb ez, mint egy véletlen próbálkozó ciklus?
            A `set` alapú szűrés után pontosan ismerjük az összes üres mezőt (`free_cells`).
            Így sosem fordulhat elő végtelen ciklus vagy kígyóra eső gyümölcs; ha a teljes
            belső tér megtelt, tisztán `None`-t adunk vissza.
        """
        occupied_cells = set(player_one_snake.body) | set(player_two_snake.body)
        free_cells = [
            GridPoint(column_x, row_y)
            for row_y in range(1, room_height - 1)
            for column_x in range(1, room_width - 1)
            if GridPoint(column_x, row_y) not in occupied_cells
        ]
        if not free_cells:
            return None
        return free_cells[random_provider.next_int(len(free_cells))]
