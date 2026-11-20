"""2. APPLICATION RÉTEG — DEPENDENCY INJECTION, GETTER & SETTER (Karmester).

Mi az Application réteg szerepe?
    A Domain (`GameRulesEngine`) csak tiszta szabályokat tartalmaz, de nem tartja észben
    az aktuális állapotot. A `GameLoopController` a karmester: őrzi a jelenlegi
    `WorldState`-et, összeköti a `GameRulesEngine`-t az `InputRecorderService`-szel,
    és kívülről kapja meg a függőségeit (**Dependency Injection**), például a
    `RandomNumberProvider`-t.

Miért itt mutatjuk be a Getter + Setter párost?
    Míg a Domain objektumok (`WorldState`, `SnakeEntity`) megváltoztathatatlanok, addig
    a játékmotor konfigurációja (pl. a játék sebessége: `tick_rate_hz`) futásidőben
    módosítható — de csak **ellenőrzötten** (1..60 Hz között). Erre való a `@property`
    (getter) és a `@tick_rate_hz.setter` (setter) páros!
"""

from dataclasses import replace

from ..domain.domain_contracts import RandomNumberProvider
from ..domain.game_enums import Direction, PlayerId
from ..domain.game_rules_engine import GameRulesEngine
from ..domain.world_state import WorldState
from .input_recorder_service import InputRecorderService


class GameLoopController:
    """Összefogja az állapotot, a szabálymotort, a véletlengenerátort és a rögzítőt."""

    def __init__(
        self,
        initial_world_state: WorldState,
        random_provider: RandomNumberProvider,
        input_recorder: InputRecorderService,
        tick_rate_hz: float = 6.0,
    ) -> None:
        """Függőségek befecskendezése konstruktoron keresztül (Constructor DI)."""
        self._world_state = initial_world_state
        self._random_provider = random_provider
        self.input_recorder = input_recorder
        self._tick_rate_hz = 6.0
        # A setteren keresztül állítjuk be, így a konstruktor is automatikusan validál!
        self.tick_rate_hz = tick_rate_hz

    @property
    def current_state(self) -> WorldState:
        """GETTER (csak olvasható): kívülről kiolvasható az állapot, de nem írható felül."""
        return self._world_state

    @property
    def tick_rate_hz(self) -> float:
        """GETTER: visszaadja a játék frissítési sebességét (tick / másodperc)."""
        return self._tick_rate_hz

    @tick_rate_hz.setter
    def tick_rate_hz(self, target_tick_rate_hz: float) -> None:
        """SETTER (a getter párja): csak érvényes (1.0..60.0 Hz) sebességet enged be."""
        if not (1.0 <= target_tick_rate_hz <= 60.0):
            raise ValueError(
                f"A tick_rate_hz értéke 1.0 és 60.0 közé kell essen, kapott: {target_tick_rate_hz}"
            )
        self._tick_rate_hz = target_tick_rate_hz

    def steer_player_snake(self, player_id: PlayerId, target_direction: Direction) -> None:
        """Feldolgoz egy játékos-irányváltást: előbb validál, majd naplóz és frissít.

        Fontos biztonsági sorrend:
            Érvénytelen `player_id` esetén `ValueError`-t dobunk MÉG AZELŐTT, hogy az
            `input_recorder` rögzítené, így hibás parancs sosem szennyezi a visszajátszási naplót.
        """
        if player_id == PlayerId.P1:
            self.input_recorder.record_player_input(
                self._world_state.tick, player_id, target_direction
            )
            updated_snake = self._world_state.player_one_snake.change_direction(target_direction)
            self._world_state = replace(self._world_state, player_one_snake=updated_snake)
        elif player_id == PlayerId.P2:
            self.input_recorder.record_player_input(
                self._world_state.tick, player_id, target_direction
            )
            updated_snake = self._world_state.player_two_snake.change_direction(target_direction)
            self._world_state = replace(self._world_state, player_two_snake=updated_snake)
        else:
            raise ValueError(f"Ismeretlen játékos-azonosító: {player_id!r}")

    def advance_simulation_tick(self, delta_seconds: float) -> None:
        """Lépteti a játékot egy időlépéssel (`delta_seconds` mp) a tiszta `GameRulesEngine` hívásával."""
        self._world_state = GameRulesEngine.compute_next_world_state(
            world_state=self._world_state,
            delta_seconds=delta_seconds,
            random_provider=self._random_provider,
        )
