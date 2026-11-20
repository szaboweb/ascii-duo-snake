"""3. INFRASTRUCTURE RÉTEG — DESERIALIZATION & CONTRACT IMPLEMENTATION.

Miért itt van a `json` és a `pathlib` import?
    Az Infrastructure réteg az egyetlen hely, amely beszélgethet a külvilággal
    (fájlrendszer, adatbázis, hálózat). Ez az osztály megvalósítja a Domain-ben
    definiált `RoomManifestLoader` szerződést (`domain_contracts.py`), és a nyers
    JSON adatot **validált** `WorldState` objektummá alakítja (Deserialization).

Hiba-absztrakció (Exception Wrapping):
    Minden alacsony szintű hibát (`JSONDecodeError`, `KeyError`, `TypeError`, `ValueError`)
    elkapunk és átcsomagolunk a saját `InvalidRoomManifestException` kivételünkbe,
    így a felsőbb rétegeknek nem kell ismerniük a JSON formátum részleteit.
"""

import json
from pathlib import Path

from ..domain.domain_exceptions import InvalidRoomManifestException
from ..domain.game_enums import Direction, PlayerId
from ..domain.game_rules_engine import GameRulesEngine
from ..domain.grid_point_value import GridPoint
from ..domain.snake_entity import SnakeEntity
from ..domain.world_state import WorldState


class JsonRoomManifestLoader:
    """A `RoomManifestLoader` szerződés fájlrendszer-alapú megvalósítása JSON manifesthez."""

    def load_initial_world_state(self, manifest_path: str) -> WorldState:
        """Beolvassa a JSON pályaleírót a fájlrendszerből, majd validált `WorldState`-et épít."""
        manifest_file_path = Path(manifest_path)
        if not manifest_file_path.exists():
            raise InvalidRoomManifestException(f"A fájl nem található: {manifest_path}")

        try:
            raw_json_text = manifest_file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as io_error:
            raise InvalidRoomManifestException(
                f"Nem sikerült beolvasni a manifest fájlt ({manifest_path}): {io_error}"
            ) from io_error

        return self.parse_manifest_text(raw_json_text)

    def parse_manifest_text(self, raw_json_text: str) -> WorldState:
        """Feldolgozza a nyers JSON szöveget, ellenőrzi a szabályokat, és `WorldState`-et épít.

        Validált szabályok (invariánsok):
            - A bemenet érvényes JSON objektum.
            - A szoba legalább 10x10-es, a gyümölcs-időköz pozitív.
            - Mindkét kígyó kezdőpontja a falakon belül van (`1..room_width-2`, `1..room_height-2`).
            - A két játékos nem indulhat azonos mezőről.
        """
        try:
            manifest_data = json.loads(raw_json_text)
        except (json.JSONDecodeError, TypeError) as json_error:
            raise InvalidRoomManifestException(f"Érvénytelen JSON: {json_error}") from json_error

        if not isinstance(manifest_data, dict):
            raise InvalidRoomManifestException("A manifest gyökere JSON objektum kell legyen.")

        try:
            room_width = int(manifest_data["width"])
            room_height = int(manifest_data["height"])
            fruit_spawn_interval_seconds = float(
                manifest_data.get("fruitSpawnIntervalSeconds", 3.0)
            )
            player_one_spawn = GridPoint(
                int(manifest_data["p1Start"]["x"]),
                int(manifest_data["p1Start"]["y"]),
            )
            player_two_spawn = GridPoint(
                int(manifest_data["p2Start"]["x"]),
                int(manifest_data["p2Start"]["y"]),
            )
        except (KeyError, TypeError, ValueError) as schema_error:
            raise InvalidRoomManifestException(
                f"Hiányzó vagy hibás mező a manifestben: {schema_error}"
            ) from schema_error

        if room_width < 10 or room_height < 10:
            raise InvalidRoomManifestException(
                f"Túl kicsi szoba ({room_width} x {room_height})"
            )
        if fruit_spawn_interval_seconds <= 0:
            raise InvalidRoomManifestException(
                f"Érvénytelen gyümölcs-időköz: {fruit_spawn_interval_seconds}"
            )

        self._validate_spawn_position(player_one_spawn, room_width, room_height, PlayerId.P1)
        self._validate_spawn_position(player_two_spawn, room_width, room_height, PlayerId.P2)
        if player_one_spawn == player_two_spawn:
            raise InvalidRoomManifestException("P1 és P2 nem indulhat azonos pozícióról.")

        return WorldState(
            room_width=room_width,
            room_height=room_height,
            fruit_spawn_interval_seconds=fruit_spawn_interval_seconds,
            player_one_snake=SnakeEntity(
                player_id=PlayerId.P1,
                body=(player_one_spawn,),
                direction=Direction.RIGHT,
            ),
            player_two_snake=SnakeEntity(
                player_id=PlayerId.P2,
                body=(player_two_spawn,),
                direction=Direction.LEFT,
            ),
        )

    @staticmethod
    def _validate_spawn_position(
        spawn_position: GridPoint,
        room_width: int,
        room_height: int,
        player_id: PlayerId,
    ) -> None:
        """Ellenőrzi, hogy a kezdőkoordináta nem esik falra vagy a szobán kívülre."""
        if not GameRulesEngine.is_within_room_bounds(spawn_position, room_width, room_height):
            raise InvalidRoomManifestException(
                f"{player_id.value} kezdőpozíciója falon vagy kívül van: "
                f"({spawn_position.x}, {spawn_position.y})"
            )
