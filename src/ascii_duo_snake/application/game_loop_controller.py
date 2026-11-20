"""2. APPLICATION RÉTEG — CONTROLLER, GETTER & SETTER (2. előadás).

A `GameLoopController` őrzi a jelenlegi `WorldState`-et, és megmutatja a
Getter (`@property`) + Setter (`@tick_rate_hz.setter`) párost validációval.
"""

from dataclasses import replace

from ..domain.game_enums import Direction, PlayerId
from ..domain.game_rules_engine import GameRulesEngine
from ..domain.world_state import WorldState


class GameLoopController:
    """Összefogja az állapotot és a tiszta `GameRulesEngine`-t."""

    def __init__(self, initial_world_state: WorldState, tick_rate_hz: float = 6.0) -> None:
        self._world_state = initial_world_state
        self._tick_rate_hz = 6.0
        self.tick_rate_hz = tick_rate_hz  # Validált SETTER-en keresztül

    @property
    def current_state(self) -> WorldState:
        """GETTER (csak olvasható): az állapot kívülről nem írható felül."""
        return self._world_state

    @property
    def tick_rate_hz(self) -> float:
        """GETTER: visszaadja a játék frissítési sebességét (tick / mp)."""
        return self._tick_rate_hz

    @tick_rate_hz.setter
    def tick_rate_hz(self, target_rate_hz: float) -> None:
        """SETTER (a getter párja): csak 1.0..60.0 Hz közötti sebességet enged be."""
        if not (1.0 <= target_rate_hz <= 60.0):
            raise ValueError(
                f"A tick_rate_hz értéke 1.0 és 60.0 közé kell essen, kapott: {target_rate_hz}"
            )
        self._tick_rate_hz = target_rate_hz

    def steer_player_snake(self, player_id: PlayerId, target_direction: Direction) -> None:
        """Irányváltási parancsot továbbít az 1-es kígyónak."""
        if player_id == PlayerId.P1:
            self._world_state = replace(
                self._world_state,
                player_one_snake=self._world_state.player_one_snake.change_direction(
                    target_direction
                ),
            )
        else:
            raise ValueError(f"Ebben a fázisban csak P1 irányítható, kapott: {player_id!r}")

    def advance_simulation_tick(self) -> None:
        """Lépteti a játékot egy tick-kel a tiszta `GameRulesEngine` hívásával."""
        self._world_state = GameRulesEngine.compute_next_world_state(self._world_state)
