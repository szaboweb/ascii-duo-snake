"""PROMO CONFIG LOADER — Adatvezérelt (Data-Driven) JSON betöltő a bemutatóhoz.

Ez a modul bemutatja a Data-Driven Programming alapelvét: a promóciós jelenetek
szövegei, időzítései, kezdőállapotai és szkriptelt lépései JSON-ból érkeznek,
a betöltő pedig validálja és valódi Domain Enumokká alakítja őket.
"""

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any, TypeVar

from ascii_duo_snake.domain.game_enums import Direction, FruitType, PlayerId

_EnumT = TypeVar("_EnumT", bound=Enum)


class PromoConfigError(Exception):
    """Hibás, hiányzó vagy érvénytelen promóciós storyboard konfiguráció."""


@dataclass(frozen=True)
class PromoTimingsConfig:
    """A bemutató globális időzítési paraméterei másodpercben."""

    typewriter_char_delay_seconds: float
    frame_delay_seconds: float
    scene_pause_seconds: float


@dataclass(frozen=True)
class ScriptedInputConfig:
    """Egyetlen előre megírt játékos-irányítási lépés adott tick-re."""

    tick: int
    player_id: PlayerId
    direction: Direction


@dataclass(frozen=True)
class InitialSnakeConfig:
    """Egy kígyó kezdőpozíciója és iránya a jelenet elején."""

    player_id: PlayerId
    x: int
    y: int
    direction: Direction


@dataclass(frozen=True)
class OptionalFruitConfig:
    """Opcionális kezdeti gyümölcs elhelyezése a jelenetben."""

    x: int
    y: int
    fruit_type: FruitType


@dataclass(frozen=True)
class ValidationCaseConfig:
    """Egyetlen hibás manifest-teszteset a 4. fázis bemutatásához."""

    label: str
    payload: str


@dataclass(frozen=True)
class PromoSceneConfig:
    """Egyetlen promóciós jelenet teljes, adatvezérelt leírása."""

    id: str
    phase_badge: str
    title: str
    subtitle: str
    highlights: tuple[str, ...]
    room_width: int
    room_height: int
    tick_rate_hz: float
    steps: int
    scripted_inputs: tuple[ScriptedInputConfig, ...]
    initial_snakes: tuple[InitialSnakeConfig, ...]
    optional_fruit: OptionalFruitConfig | None
    validation_cases: tuple[ValidationCaseConfig, ...]
    closing_layers: tuple[str, ...]
    pause_after_seconds: float | None = None
    theme_id: str = "classic_ascii"
    p1_bot_strategy: str | None = None
    p2_bot_strategy: str | None = None
    enable_telemetry: bool = False
    enable_replay_check: bool = False


@dataclass(frozen=True)
class PromoStoryboardConfig:
    """A teljes promóciós bemutató gyökér-konfigurációja (SSOT)."""

    timings: PromoTimingsConfig
    scenes: tuple[PromoSceneConfig, ...]


def _parse_enum(enum_cls: type[_EnumT], raw_value: Any, field_name: str) -> _EnumT:
    """Nyers JSON stringet alakít valódi Domain Enum példánnyá."""
    if not isinstance(raw_value, str):
        raise PromoConfigError(f"A(z) '{field_name}' mezőnek szövegnek kell lennie.")
    try:
        return enum_cls(raw_value)
    except ValueError as exc:
        valid = ", ".join(item.value for item in enum_cls)
        raise PromoConfigError(f"Érvénytelen '{field_name}': {raw_value!r} (engedett: {valid}).") from exc


def _parse_timings(raw: dict[str, Any]) -> PromoTimingsConfig:
    """Beolvassa és validálja a `timings` szekciót."""
    timings = PromoTimingsConfig(
        typewriter_char_delay_seconds=float(raw["typewriter_char_delay_seconds"]),
        frame_delay_seconds=float(raw["frame_delay_seconds"]),
        scene_pause_seconds=float(raw["scene_pause_seconds"]),
    )
    if min(timings.typewriter_char_delay_seconds, timings.frame_delay_seconds, timings.scene_pause_seconds) < 0.0:
        raise PromoConfigError("Az időzítési értékek nem lehetnek negatívak.")
    return timings


def _parse_optional_fruit(raw_fruit: Any) -> OptionalFruitConfig | None:
    """Opcionális kezdeti gyümölcs objektum feldolgozása."""
    if raw_fruit is None:
        return None
    return OptionalFruitConfig(
        x=int(raw_fruit["x"]),
        y=int(raw_fruit["y"]),
        fruit_type=_parse_enum(FruitType, raw_fruit["fruit_type"], "fruit_type"),
    )


def _parse_scene(raw: dict[str, Any]) -> PromoSceneConfig:
    """Egyetlen jelenet-leírás validálása és domain típusokká alakítása."""
    snakes = tuple(
        InitialSnakeConfig(
            player_id=_parse_enum(PlayerId, item["player_id"], "player_id"),
            x=int(item["x"]),
            y=int(item["y"]),
            direction=_parse_enum(Direction, item["direction"], "direction"),
        )
        for item in raw["initial_snakes"]
    )
    if {snake.player_id for snake in snakes} != {PlayerId.P1, PlayerId.P2}:
        raise PromoConfigError(f"A(z) '{raw.get('id')}' jelenetben pontosan P1 és P2 kígyó szükséges.")
    inputs = tuple(
        ScriptedInputConfig(
            tick=int(item["tick"]),
            player_id=_parse_enum(PlayerId, item["player_id"], "player_id"),
            direction=_parse_enum(Direction, item["direction"], "direction"),
        )
        for item in raw["scripted_inputs"]
    )
    cases = tuple(ValidationCaseConfig(str(c["label"]), str(c["payload"])) for c in raw["validation_cases"])
    raw_pause = raw.get("pause_after_seconds")
    pause_after = None if raw_pause is None else float(raw_pause)
    if pause_after is not None and pause_after < 0.0:
        raise PromoConfigError("A 'pause_after_seconds' mező nem lehet negatív.")
    return PromoSceneConfig(
        id=str(raw["id"]),
        phase_badge=str(raw["phase_badge"]),
        title=str(raw["title"]),
        subtitle=str(raw["subtitle"]),
        highlights=tuple(str(line) for line in raw["highlights"]),
        room_width=int(raw["room_width"]),
        room_height=int(raw["room_height"]),
        tick_rate_hz=float(raw["tick_rate_hz"]),
        steps=int(raw["steps"]),
        scripted_inputs=inputs,
        initial_snakes=snakes,
        optional_fruit=_parse_optional_fruit(raw.get("optional_fruit")),
        validation_cases=cases,
        closing_layers=tuple(str(line) for line in raw["closing_layers"]),
        pause_after_seconds=pause_after,
        theme_id=str(raw.get("theme_id", "classic_ascii")),
        p1_bot_strategy=None if raw.get("p1_bot_strategy") is None else str(raw["p1_bot_strategy"]),
        p2_bot_strategy=None if raw.get("p2_bot_strategy") is None else str(raw["p2_bot_strategy"]),
        enable_telemetry=bool(raw.get("enable_telemetry", False)),
        enable_replay_check=bool(raw.get("enable_replay_check", False)),
    )


def load_promo_storyboard_config(config_path: Path) -> PromoStoryboardConfig:
    """Betölti és validálja a promóciós storyboard JSON konfigurációt."""
    try:
        raw_text = Path(config_path).read_text(encoding="utf-8")
        data = json.loads(raw_text)
        if not isinstance(data, dict) or not isinstance(data.get("scenes"), list) or not data["scenes"]:
            raise PromoConfigError("A konfigurációnak tartalmaznia kell egy nem üres 'scenes' listát.")
        return PromoStoryboardConfig(
            timings=_parse_timings(data["timings"]),
            scenes=tuple(_parse_scene(item) for item in data["scenes"]),
        )
    except PromoConfigError:
        raise
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise PromoConfigError(f"Hibás promóciós konfiguráció ({config_path}): {exc}") from exc
