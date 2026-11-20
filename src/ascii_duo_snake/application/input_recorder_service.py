"""2. APPLICATION RÉTEG — RECORDER & ENCAPSULATION (Naplózás és Egységbezárás).

Miért külön osztály az `InputRecorderService`?
    A Single Responsibility Principle (Egyetlen Felelősség Elve) szerint a játékvezérlő
    feladata a szimuláció futtatása, a rögzítő szolgáltatás feladata pedig a bemenetek
    tárolása. Mivel minden irányváltáshoz elmentjük a pontos `tick` számot, később a
    teljes meccs 100%-ban visszajátszható (Deterministic Replay) ugyanazzal a random seed-del!

Encapsulation (Egységbezárás):
    Az `_input_history` lista privát (`_` előtag), a `history` getter pedig
    megváltoztathatatlan `tuple`-t ad ki — így a hívók olvashatják a naplót,
    de nem tudják utólag átírni.
"""

from dataclasses import dataclass

from ..domain.game_enums import Direction, PlayerId


@dataclass(frozen=True)
class InputRecord:
    """Egyetlen rögzített játékos-bemenet időbélyeggel (tick-kel)."""

    tick: int
    player_id: PlayerId
    target_direction: Direction


class InputRecorderService:
    """Naplózza a játékosok irányváltásait tick-re pontosan."""

    def __init__(self) -> None:
        self._input_history: list[InputRecord] = []

    def record_player_input(
        self,
        tick: int,
        player_id: PlayerId,
        target_direction: Direction,
    ) -> None:
        """Új bemeneti eseményt fűz a belső napló végére."""
        self._input_history.append(
            InputRecord(tick=tick, player_id=player_id, target_direction=target_direction)
        )

    @property
    def history(self) -> tuple[InputRecord, ...]:
        """GETTER (csak olvasható): megváltoztathatatlan másolatot ad az előzményekről."""
        return tuple(self._input_history)
