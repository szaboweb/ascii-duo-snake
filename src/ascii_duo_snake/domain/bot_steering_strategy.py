"""Gépi irányítási stratégiák (Strategy Pattern & Open/Closed Principle).

Ez a modul a Stratégia tervezési mintát (`typing.Protocol` struktúrális altípusozás)
és a Nyílt/Zárt Elvet (Open/Closed Principle — OCP) szemlélteti a Domain rétegben.

Miért különítjük el a bot döntéshozatali algoritmusait a `GameRulesEngine` motorból?
1. **Nyílt a bővítésre, zárt a módosításra (OCP):** Új mesterséges intelligencia
   (pl. mohó gyümölcsvadász vagy óvatos túlélő) úgy adható a rendszerhez, hogy a
   központi fizikai és ütközésvizsgáló szabálymotort (`GameRulesEngine`) egyetlen
   sorban sem kell módosítani.
2. **Tiszta, mellékhatásmentes függvények:** Minden stratégia egy nem-módosítható
   `WorldState` pillanatképet kap, és kizárólag a következő `Direction` irányt
   adja vissza anélkül, hogy közvetlenül mutálná a játékállapotot.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Protocol

from .game_enums import Direction, PlayerId
from .game_rules_engine import DIRECTION_DELTAS, GameRulesEngine
from .grid_point_value import GridPoint
from .snake_entity import SnakeEntity, is_opposite_direction
from .world_state import WorldState

CANDIDATE_DIRECTIONS: tuple[Direction, ...] = (
    Direction.UP,
    Direction.RIGHT,
    Direction.DOWN,
    Direction.LEFT,
)


class BotSteeringStrategy(Protocol):
    """Strukturális interfész (Protocol) a gépi kígyóirányító algoritmusokhoz."""

    def choose_next_direction(
        self,
        world_state: WorldState,
        controlled_player: PlayerId,
    ) -> Direction:
        """Kiválasztja az irányított kígyó következő lépésirányát."""


def compute_manhattan_distance(
    first_point: GridPoint,
    second_point: GridPoint,
) -> int:
    """Kiszámítja két rácspont közötti L1 (Manhattan) távolságot: |dx| + |dy|."""
    return abs(first_point.x - second_point.x) + abs(
        first_point.y - second_point.y
    )


def is_cell_safe_for_bot(
    target_point: GridPoint,
    world_state: WorldState,
) -> bool:
    """Tiszta predikátum: a célmező pályán belül van-e és mentes-e kígyótesttől."""
    if not GameRulesEngine.is_within_room_bounds(
        target_point,
        world_state.room_width,
        world_state.room_height,
    ):
        return False
    if target_point in world_state.player_one_snake.body:
        return False
    return target_point not in world_state.player_two_snake.body


def _resolve_controlled_snake(
    world_state: WorldState,
    controlled_player: PlayerId,
) -> SnakeEntity:
    """Visszaadja az adott játékosazonosítóhoz tartozó kígyó entitást."""
    if controlled_player == PlayerId.P1:
        return world_state.player_one_snake
    return world_state.player_two_snake


def _list_non_opposite_directions(
    current_direction: Direction,
) -> list[Direction]:
    """Kiszűri a 180 fokos (azonnali öngyilkosságot okozó) hátrafordulási irányt."""
    return [
        candidate
        for candidate in CANDIDATE_DIRECTIONS
        if not is_opposite_direction(current_direction, candidate)
    ]


class GreedyFruitBotStrategy:
    """Mohó gyümölcsvadász stratégia: mindig a gyümölcshöz legközelebbi irányt választja."""

    def choose_next_direction(
        self,
        world_state: WorldState,
        controlled_player: PlayerId,
    ) -> Direction:
        """A nem-ellentétes irányok közül minimalizálja a gyümölcstől való távolságot."""
        snake = _resolve_controlled_snake(world_state, controlled_player)
        fruit_pos = world_state.fruit_position
        if fruit_pos is None:
            return snake.direction
        valid_candidates = _list_non_opposite_directions(snake.direction)
        return min(
            valid_candidates,
            key=lambda candidate: compute_manhattan_distance(
                snake.head + DIRECTION_DELTAS[candidate],
                fruit_pos,
            ),
        )


class CautiousSurvivalBotStrategy:
    """Óvatos túlélő stratégia: először kizárja a fal- és testütközéseket, majd közelít."""

    def choose_next_direction(
        self,
        world_state: WorldState,
        controlled_player: PlayerId,
    ) -> Direction:
        """A biztonságos szomszédos mezők közül választja a gyümölcshöz legközelebbit."""
        snake = _resolve_controlled_snake(world_state, controlled_player)
        safe_candidates = [
            candidate
            for candidate in _list_non_opposite_directions(snake.direction)
            if is_cell_safe_for_bot(
                snake.head + DIRECTION_DELTAS[candidate],
                world_state,
            )
        ]
        if not safe_candidates:
            return snake.direction
        fruit_pos = world_state.fruit_position
        if fruit_pos is not None:
            return min(
                safe_candidates,
                key=lambda candidate: compute_manhattan_distance(
                    snake.head + DIRECTION_DELTAS[candidate],
                    fruit_pos,
                ),
            )
        if snake.direction in safe_candidates:
            return snake.direction
        return safe_candidates[0]


BOT_STRATEGY_CATALOG: Mapping[str, BotSteeringStrategy] = MappingProxyType(
    {
        "greedy": GreedyFruitBotStrategy(),
        "cautious": CautiousSurvivalBotStrategy(),
    }
)


def select_bot_strategy(strategy_id: str) -> BotSteeringStrategy:
    """Kikeresi a megadott azonosítójú bot-irányítási stratégiát a katalógusból."""
    strategy = BOT_STRATEGY_CATALOG.get(strategy_id)
    if strategy is None:
        valid_ids = ", ".join(sorted(BOT_STRATEGY_CATALOG.keys()))
        raise ValueError(
            f"Ismeretlen bot-stratégia azonosító: '{strategy_id}'. "
            f"Érvényes stratégiák: [{valid_ids}]"
        )
    return strategy
