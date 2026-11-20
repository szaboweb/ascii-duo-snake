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
bármikor bitről bitre reprodukálja a teljes mérkőzést!
================================================================================
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, replace

from ..domain.domain_contracts import RandomNumberProvider
from ..domain.game_enums import Direction, GameStatus, PlayerId
from ..domain.game_rules_engine import GameRulesEngine
from ..domain.world_state import WorldState
from .input_recorder_service import InputRecord


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
            ValueError: Ha a JSON szintaktikailag hibás vagy hiányos sémájú.
        """
        try:
            data = json.loads(raw_json)
            if not isinstance(data, dict):
                raise ValueError("A replay JSON gyökérelemének objektumnak kell lennie.")

            raw_inputs = data["recorded_inputs"]
            if not isinstance(raw_inputs, list):
                raise ValueError("A 'recorded_inputs' mezőnek listának kell lennie.")

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
                tick_rate_hz=float(data["tick_rate_hz"]),
                total_ticks=int(data["total_ticks"]),
                recorded_inputs=recorded_inputs,
                expected_final_status=GameStatus(str(data["expected_final_status"])),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"Érvénytelen replay JSON formátum: {error}") from error

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
        """
        random_provider = random_provider_factory(snapshot.random_seed)
        delta_seconds = 1.0 / snapshot.tick_rate_hz

        inputs_by_tick: dict[int, list[InputRecord]] = {}
        for record in snapshot.recorded_inputs:
            inputs_by_tick.setdefault(record.tick, []).append(record)

        current_state = initial_world_state
        for _ in range(snapshot.total_ticks):
            tick_records = inputs_by_tick.get(current_state.tick, [])
            for record in tick_records:
                current_state = DeterministicReplayService._apply_input_record(
                    current_state,
                    record,
                )
            current_state = GameRulesEngine.compute_next_world_state(
                current_state,
                delta_seconds,
                random_provider,
            )

        return current_state

    @staticmethod
    def _apply_input_record(
        world_state: WorldState,
        record: InputRecord,
    ) -> WorldState:
        """Alkalmaz egyetlen rögzített irányváltást az adott világállapotra."""
        if record.player_id == PlayerId.P1:
            updated_snake = world_state.player_one_snake.change_direction(
                record.target_direction
            )
            return replace(world_state, player_one_snake=updated_snake)

        updated_snake = world_state.player_two_snake.change_direction(
            record.target_direction
        )
        return replace(world_state, player_two_snake=updated_snake)
