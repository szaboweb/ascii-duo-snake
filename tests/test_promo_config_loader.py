"""UNIT TESZTEK — Adatvezérelt Promóciós Konfiguráció Betöltő (`promo_config_loader.py`).

Ellenőrzi, hogy a `promo/promo_storyboard_config.json` hibátlanul betölthető
valódi Domain Enumokká (`PlayerId`, `Direction`, `FruitType`), valamint hogy
hibás vagy hiányzó fájl esetén célzott `PromoConfigError` kivétel keletkezik.
"""

import json
from pathlib import Path
import sys
import tempfile
import unittest

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PROMO_DIR = _PROJECT_ROOT / "promo"
if str(_PROMO_DIR) not in sys.path:
    sys.path.insert(0, str(_PROMO_DIR))

from ascii_duo_snake.domain.game_enums import Direction, FruitType, PlayerId  # noqa: E402
from promo_config_loader import (  # noqa: E402
    PromoConfigError,
    load_promo_storyboard_config,
)


class TestPromoConfigLoader(unittest.TestCase):
    """A `load_promo_storyboard_config()` helyes és hibás eseteinek ellenőrzése."""

    def test_loads_default_storyboard_config_with_valid_domain_enums(self) -> None:
        config_path = _PROMO_DIR / "promo_storyboard_config.json"
        storyboard = load_promo_storyboard_config(config_path)

        self.assertEqual(len(storyboard.scenes), 8)
        self.assertGreaterEqual(storyboard.timings.frame_delay_seconds, 0.0)
        self.assertGreaterEqual(storyboard.timings.typewriter_char_delay_seconds, 0.0)
        self.assertGreaterEqual(storyboard.timings.scene_pause_seconds, 0.0)

        for scene in storyboard.scenes:
            self.assertTrue(scene.title)
            self.assertTrue(scene.highlights)
            for snake in scene.initial_snakes:
                self.assertIsInstance(snake.player_id, PlayerId)
                self.assertIsInstance(snake.direction, Direction)
            for scripted_input in scene.scripted_inputs:
                self.assertIsInstance(scripted_input.player_id, PlayerId)
                self.assertIsInstance(scripted_input.direction, Direction)
            if scene.optional_fruit is not None:
                self.assertIsInstance(scene.optional_fruit.fruit_type, FruitType)

        scene_three = storyboard.scenes[2]
        self.assertIsNotNone(scene_three.optional_fruit)
        assert scene_three.optional_fruit is not None
        self.assertEqual(scene_three.optional_fruit.fruit_type, FruitType.GOLDEN_MELON)

        scene_four = storyboard.scenes[3]
        self.assertGreaterEqual(len(scene_four.validation_cases), 2)
        self.assertGreaterEqual(len(scene_four.closing_layers), 3)

    def test_raises_promo_config_error_on_missing_file(self) -> None:
        missing_path = _PROMO_DIR / "nem_letezo_storyboard.json"
        with self.assertRaises(PromoConfigError):
            load_promo_storyboard_config(missing_path)

    def test_raises_promo_config_error_on_invalid_enum_value(self) -> None:
        default_data = json.loads((_PROMO_DIR / "promo_storyboard_config.json").read_text(encoding="utf-8"))
        default_data["scenes"][0]["initial_snakes"][0]["direction"] = "diagonal_invalid"

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            json.dump(default_data, tmp)
            tmp_path = Path(tmp.name)
        try:
            with self.assertRaises(PromoConfigError):
                load_promo_storyboard_config(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_raises_promo_config_error_on_invalid_json_syntax(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
            tmp.write("{ nem ervenyes json")
            tmp_path = Path(tmp.name)
        try:
            with self.assertRaises(PromoConfigError):
                load_promo_storyboard_config(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
