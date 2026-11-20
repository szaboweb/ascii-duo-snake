"""Tartományi események (Domain Events) és állapotátmenet-elemző modul.

================================================================================
MIÉRT FONTOS EZ A MODUL? (Domain Events & Event-Driven Architecture)
================================================================================
A Clean Architecture legbelső rétege (Domain) nem hívhatja közvetlenül a
hanglejátszót, az eredményjelzőt vagy a statisztikagyűjtőt, amikor egy kígyó
megeszik egy gyümölcsöt vagy véget ér a mérkőzés.

Ehelyett a **Domain Events (Tartományi Események)** mintát alkalmazzuk:
1. A szabálymotor (`GameRulesEngine`) tisztán kiszámítja a következő állapotot:
   `previous_state -> next_state`.
2. A `detect_transition_events(previous_state, next_state)` tiszta függvény
   összehasonlítja a két megváltoztathatatlan állapotot, és kibocsátja a
   megtörtént üzleti tényeket (`FruitEatenEvent`, `MatchEndedEvent`).
3. A külső rétegek (hang, analitika, jelvényrendszer) ezekre a megváltoztathatatlan
   (immutable) eseményekre iratkozhatnak fel anélkül, hogy a szabálymotor
   bármit tudna róluk!
================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass

from .game_enums import FruitType, GameStatus, PlayerId
from .grid_point_value import GridPoint
from .world_state import WorldState


@dataclass(frozen=True)
class FruitEatenEvent:
    """Megváltoztathatatlan tartományi esemény: egy játékos megevett egy gyümölcsöt.

    Attributes:
        tick: Az időlépés, amelyben a gyümölcs elfogyasztása megtörtént.
        player_id: A gyümölcsöt elfogyasztó játékos azonosítója (`P1` vagy `P2`).
        fruit_type: Az elfogyasztott gyümölcs típusa (`APPLE` vagy `GOLDEN_MELON`).
        eaten_at: A rácsmező koordinátája, ahol a gyümölcs volt.
        new_fruits_eaten_count: A játékos által eddig megevett gyümölcsök új összege.
    """

    tick: int
    player_id: PlayerId
    fruit_type: FruitType
    eaten_at: GridPoint
    new_fruits_eaten_count: int


@dataclass(frozen=True)
class MatchEndedEvent:
    """Megváltoztathatatlan tartományi esemény: a mérkőzés véget ért.

    Attributes:
        tick: Az időlépés, amelyben a mérkőzés lezárult.
        final_status: A mérkőzés végső kimenetele (`P1_WON`, `P2_WON` vagy `DRAW`).
    """

    tick: int
    final_status: GameStatus


GameDomainEvent = FruitEatenEvent | MatchEndedEvent


def detect_transition_events(
    previous_state: WorldState,
    next_state: WorldState,
) -> tuple[GameDomainEvent, ...]:
    """Tiszta függvény: kinyeri a tartományi eseményeket két egymást követő állapotból.

    Args:
        previous_state: Az időlépés előtti világállapot.
        next_state: Az időlépés utáni új világállapot.

    Returns:
        Az állapotátmenet során bekövetkezett tartományi események tuple-je.
    """
    events: list[GameDomainEvent] = []

    if (
        next_state.player_one_snake.fruits_eaten
        > previous_state.player_one_snake.fruits_eaten
        and previous_state.fruit_position is not None
    ):
        events.append(
            FruitEatenEvent(
                tick=next_state.tick,
                player_id=PlayerId.P1,
                fruit_type=previous_state.fruit_type,
                eaten_at=previous_state.fruit_position,
                new_fruits_eaten_count=next_state.player_one_snake.fruits_eaten,
            )
        )

    if (
        next_state.player_two_snake.fruits_eaten
        > previous_state.player_two_snake.fruits_eaten
        and previous_state.fruit_position is not None
    ):
        events.append(
            FruitEatenEvent(
                tick=next_state.tick,
                player_id=PlayerId.P2,
                fruit_type=previous_state.fruit_type,
                eaten_at=previous_state.fruit_position,
                new_fruits_eaten_count=next_state.player_two_snake.fruits_eaten,
            )
        )

    if (
        previous_state.status == GameStatus.RUNNING
        and next_state.status != GameStatus.RUNNING
    ):
        events.append(
            MatchEndedEvent(
                tick=next_state.tick,
                final_status=next_state.status,
            )
        )

    return tuple(events)
