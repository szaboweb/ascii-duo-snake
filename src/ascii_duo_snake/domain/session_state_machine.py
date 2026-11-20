"""Táblázatvezérelt Véges Állapotgép (Table-Driven Finite State Machine — FSM).

Ez a modul a játékmenet életciklusának (menü, aktív játék, szünet, játék vége,
visszajátszás) determinisztikus állapotátmeneteit modellezi a Domain rétegben.

Miért használunk deklaratív állapotátmeneti táblázatot (`ALLOWED_PHASE_TRANSITIONS`)
többszörösen egymásba ágyazott `if/elif/else` elágazások helyett?
1. **Alacsony ciklomatikus komplexitás (`CC <= 15`):** Egyetlen `O(1)` halmaz-tagsági
   vizsgálat (`target_phase in allowed_targets`) helyettesíti a spagetti-logikát.
2. **Adatvezérelt Egyetlen Igazságforrás (Data-Driven SSOT):** Az összes megengedett
   állapotátmenet egyetlen nem-módosítható (`MappingProxyType` + `frozenset`)
   gráfként olvasható és tesztelhető.
3. **Szigorú előfeltétel-védelem:** Érvénytelen átmenet kísérletekor a rendszer azonnal
   tartomány-specifikus kivételt (`InvalidPhaseTransitionException`) dob, megelőzve
   a konzisztencia-sérülést (pl. közvetlen `MENU -> PAUSED` ugrást).
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from types import MappingProxyType


class SessionPhase(Enum):
    """A játékmenet (Session) lehetséges életciklus-fázisainak felsorolása."""

    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    REPLAY = "replay"


class InvalidPhaseTransitionException(Exception):
    """Tartományi kivétel, amelyet érvénytelen FSM állapotátmenet esetén dobunk."""

    def __init__(
        self,
        current_phase: SessionPhase,
        target_phase: SessionPhase,
    ) -> None:
        self.current_phase = current_phase
        self.target_phase = target_phase
        super().__init__(
            f"Érvénytelen munkamenet-állapotátmenet: "
            f"'{current_phase.value}' -> '{target_phase.value}' nem engedélyezett."
        )


ALLOWED_PHASE_TRANSITIONS: Mapping[SessionPhase, frozenset[SessionPhase]] = (
    MappingProxyType(
        {
            SessionPhase.MENU: frozenset(
                {SessionPhase.PLAYING, SessionPhase.REPLAY}
            ),
            SessionPhase.PLAYING: frozenset(
                {SessionPhase.PAUSED, SessionPhase.GAME_OVER}
            ),
            SessionPhase.PAUSED: frozenset(
                {SessionPhase.PLAYING, SessionPhase.MENU}
            ),
            SessionPhase.GAME_OVER: frozenset(
                {
                    SessionPhase.MENU,
                    SessionPhase.PLAYING,
                    SessionPhase.REPLAY,
                }
            ),
            SessionPhase.REPLAY: frozenset(
                {SessionPhase.MENU, SessionPhase.GAME_OVER}
            ),
        }
    )
)


class SessionStateMachine:
    """A játékmenet aktuális fázisát és átmenet-történetét kezelő véges állapotgép."""

    def __init__(
        self,
        initial_phase: SessionPhase = SessionPhase.MENU,
    ) -> None:
        if initial_phase not in ALLOWED_PHASE_TRANSITIONS:
            raise ValueError(f"Ismeretlen kezdőfázis: {initial_phase}")
        self._current_phase: SessionPhase = initial_phase
        self._transition_history: list[SessionPhase] = [initial_phase]

    @property
    def current_phase(self) -> SessionPhase:
        """Visszaadja az állapotgép jelenlegi aktív fázisát."""
        return self._current_phase

    @property
    def transition_history(self) -> tuple[SessionPhase, ...]:
        """Visszaadja az eddig bejárt fázisok nem-módosítható (`tuple`) sorozatát."""
        return tuple(self._transition_history)

    def can_transition_to(self, target_phase: SessionPhase) -> bool:
        """Tiszta predikátum (`0` állapotmódosítás): engedélyezett-e az átmenet."""
        allowed_targets = ALLOWED_PHASE_TRANSITIONS.get(
            self._current_phase,
            frozenset(),
        )
        return target_phase in allowed_targets

    def transition_to(self, target_phase: SessionPhase) -> SessionPhase:
        """Átlépteti az állapotgépet a célfázisba, vagy kivételt dob hiba esetén."""
        if not self.can_transition_to(target_phase):
            raise InvalidPhaseTransitionException(
                current_phase=self._current_phase,
                target_phase=target_phase,
            )
        self._current_phase = target_phase
        self._transition_history.append(target_phase)
        return self._current_phase
