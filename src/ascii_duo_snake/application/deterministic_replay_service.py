"""Eseményalapú visszajátszás (Event Sourcing & Deterministic Replay) szolgáltatás.

================================================================================
MIÉRT FONTOS EZ A MODUL? (Event Sourcing & Deterministic Replay)
================================================================================
Hogyan képesek a modern e-sport játékok (StarCraft, Dota, Rocket League) vagy
a pénzügyi elszámolórendszerek egy teljes mérkőzést vagy tranzakciótörténetet
néhány kilobájtból hajszálpontosan újraalkotni?

A titok a **Determinisztikus Visszajátszás (Deterministic Replay)** három pillére:
1. **Tiszta függvények (Pure Functions)**: A `GameRulesEngine` nem használ
   valódi rendszerórát (`time.time()`) vagy globális állapotot.
2. **Explicit Random Seed**: Ha a véletlenszám-generátort (`SeededRandomProvider`)
   ugyanazzal a kezdőmaggal (`random_seed`) indítjuk el, a gyümölcsök
   másodpercre és koordinátára pontosan ugyanott fognak megjelenni!
3. **Bemeneti eseménynapló (`InputRecord`)**: Nem kell minden képkockán
   elmenteni a teljes pályát, elég csak azt rögzíteni, hogy melyik `tick`-ben
   melyik játékos milyen irányt nyomott meg.

Ebből a három adatból (`MatchReplaySnapshot`) a `DeterministicReplayService`
bármikor bitről bitre reprodukálja a teljes mérkőzést — akár egyben a végállapotot
(`replay_match_deterministically`), akár `yield` generátorral képkockáról képkockára
(`iter_replay_states`) az animált visszajátszáshoz!
================================================================================
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from ..domain.domain_contracts import RandomNumberProvider
from ..domain.game_enums import Direction, GameStatus, PlayerId
from ..domain.world_state import WorldState
from .game_loop_controller import GameLoopController
from .input_recorder_service import InputRecord, InputRecorderService


@dataclass(frozen=True)
class MatchReplaySnapshot:
    """Egy lejátszott mérkőzés determinisztikus újrajátszásához szükséges pillanatkép.

    Attributes:
        random_seed: A mérkőzés véletlenszám-generátorának kezdőmagja.
        tick_rate_hz: A szimuláció másodpercenkénti időlépéseinek száma (Hz).
        total_ticks: A lejátszott időlépések teljes száma.
        recorded_inputs: A mérkőzés során rögzített irányváltások időrendi tuple-je.
        expected_final_status: A mérkőzés végén elvárt állapot (`GameStatus`).
    """

    random_seed: int
    tick_rate_hz: float
    total_ticks: int
    recorded_inputs: tuple[InputRecord, ...]
    expected_final_status: GameStatus


class DeterministicReplayService:
    """Mérkőzés-visszajátszások JSON szerializálását és determinisztikus futtatását végző szolgáltatás."""

    @staticmethod
    def serialize_replay_to_json(snapshot: MatchReplaySnapshot) -> str:
        """Olvasható, formázott JSON karakterlánccá alakít egy visszajátszási pillanatképet.

        Args:
            snapshot: A szerializálandó `MatchReplaySnapshot`.

        Returns:
            Formázott JSON karakterlánc.
        """
        payload = {
            "random_seed": snapshot.random_seed,
            "tick_rate_hz": snapshot.tick_rate_hz,
            "total_ticks": snapshot.total_ticks,
            "expected_final_status": snapshot.expected_final_status.value,
            "recorded_inputs": [
                {
                    "tick": record.tick,
                    "player_id": record.player_id.value,
                    "target_direction": record.target_direction.value,
                }
                for record in snapshot.recorded_inputs
            ],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    @staticmethod
    def deserialize_replay_from_json(raw_json: str) -> MatchReplaySnapshot:
        """Visszaalakít egy JSON karakterláncot típusbiztos `MatchReplaySnapshot` példánnyá.

        Args:
            raw_json: A JSON formátumú visszajátszási adat.

        Returns:
            A rekonstruált `MatchReplaySnapshot` objektum.

        Raises:
            ValueError: Ha a JSON szintaktikailag hibás, hiányos sémájú vagy érvénytelen értékű.
        """
        try:
            data = json.loads(raw_json)
            if not isinstance(data, dict):
                raise ValueError("A replay JSON gyökérelemének objektumnak kell lennie.")

            raw_inputs = data["recorded_inputs"]
            if not isinstance(raw_inputs, list):
                raise ValueError("A 'recorded_inputs' mezőnek listának kell lennie.")

            tick_rate_hz = float(data["tick_rate_hz"])
            total_ticks = int(data["total_ticks"])
            if not (1.0 <= tick_rate_hz <= 60.0):
                raise ValueError(
                    f"Érvénytelen tick_rate_hz ({tick_rate_hz}): 1.0 és 60.0 között kell lennie."
                )
            if total_ticks < 0:
                raise ValueError(
                    f"Érvénytelen total_ticks ({total_ticks}): nem lehet negatív."
                )

            recorded_inputs = tuple(
                InputRecord(
                    tick=int(item["tick"]),
                    player_id=PlayerId(str(item["player_id"])),
                    target_direction=Direction(
                        str(item.get("target_direction", item.get("direction")))
                    ),
                )
                for item in raw_inputs
            )
            return MatchReplaySnapshot(
                random_seed=int(data["random_seed"]),
                tick_rate_hz=tick_rate_hz,
                total_ticks=total_ticks,
                recorded_inputs=recorded_inputs,
                expected_final_status=GameStatus(str(data["expected_final_status"])),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"Érvénytelen replay JSON formátum: {error}") from error

    @staticmethod
    def iter_replay_states(
        initial_world_state: WorldState,
        snapshot: MatchReplaySnapshot,
        random_provider_factory: Callable[[int], RandomNumberProvider],
    ) -> Iterator[WorldState]:
        """Lépésről lépésre (`yield` generátorral) kiadja a visszajátszás minden képkockáját.

        Args:
            initial_world_state: A mérkőzés 0. tickbeli kezdőállapota.
            snapshot: A rögzített bemeneteket és random seedet tartalmazó pillanatkép.
            random_provider_factory: Függvény, amely a seedből `RandomNumberProvider`-t gyárt.

        Yields:
            A kezdő (`0.`) ticktől a `total_ticks`-edik tickig minden előálló `WorldState` pillanatképet.

        Raises:
            ValueError: Ha a pillanatkép tick-paraméterei érvénytelenek vagy a végső állapot eltér.
        """
        if snapshot.total_ticks < 0:
            raise ValueError(
                f"Érvénytelen total_ticks ({snapshot.total_ticks}): nem lehet negatív."
            )
        if not (1.0 <= snapshot.tick_rate_hz <= 60.0):
            raise ValueError(
                f"Érvénytelen tick_rate_hz ({snapshot.tick_rate_hz}): 1.0 és 60.0 között kell lennie."
            )

        controller = GameLoopController(
            initial_world_state=initial_world_state,
            random_provider=random_provider_factory(snapshot.random_seed),
            input_recorder=InputRecorderService(),
            tick_rate_hz=snapshot.tick_rate_hz,
        )

        inputs_by_tick: dict[int, list[InputRecord]] = {}
        for record in snapshot.recorded_inputs:
            inputs_by_tick.setdefault(record.tick, []).append(record)

        yield controller.current_state

        for _ in range(snapshot.total_ticks):
            tick_records = inputs_by_tick.get(controller.current_state.tick, [])
            for record in tick_records:
                controller.steer_player_snake(record.player_id, record.target_direction)
            controller.advance_simulation_tick(1.0 / controller.tick_rate_hz)
            yield controller.current_state

        if controller.current_state.status != snapshot.expected_final_status:
            raise ValueError(
                f"Determinisztikus replay eltérés: elvárt állapot={snapshot.expected_final_status.value}, "
                f"kapott={controller.current_state.status.value}"
            )

    @staticmethod
    def replay_match_deterministically(
        initial_world_state: WorldState,
        snapshot: MatchReplaySnapshot,
        random_provider_factory: Callable[[int], RandomNumberProvider],
    ) -> WorldState:
        """Újrajátssza a teljes mérkőzést a kezdőállapotból és a rögzített bemenetekből.

        Args:
            initial_world_state: A mérkőzés 0. tickbeli kezdőállapota.
            snapshot: A rögzített bemeneteket és random seedet tartalmazó pillanatkép.
            random_provider_factory: Függvény, amely a seedből `RandomNumberProvider`-t gyárt.

        Returns:
            A visszajátszás végén előálló végső `WorldState`.

        Raises:
            ValueError: Ha a pillanatkép tick-paraméterei érvénytelenek vagy a végső állapot eltér.
        """
        final_world_state = initial_world_state
        for frame_state in DeterministicReplayService.iter_replay_states(
            initial_world_state, snapshot, random_provider_factory
        ):
            final_world_state = frame_state
        return final_world_state
