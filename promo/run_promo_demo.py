"""CLI BELÉPÉSI PONT — Adatvezérelt Automatikus Promóciós Demó (`promo/run_promo_demo.py`).

Használat:
    python promo/run_promo_demo.py                              # Alapértelmezett JSON bemutató
    python promo/run_promo_demo.py --fast                       # Gyors CI/előnézet (0 mp várakozás)
    python promo/run_promo_demo.py --loop                       # Kivetítő hurok (Ctrl+C)
    python promo/run_promo_demo.py --config sajat_promo.json    # Saját szerkesztett JSON forgatókönyv
"""

import argparse
from pathlib import Path
import sys

# Biztosítja, hogy a `promo/` és a `src/` közvetlen futtatáskor is megtalálható legyen
_PROMO_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _PROMO_DIR.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
if str(_PROMO_DIR) not in sys.path:
    sys.path.insert(0, str(_PROMO_DIR))

from promo_config_loader import PromoConfigError, load_promo_storyboard_config  # noqa: E402
from promo_storyboard import run_promo_storyboard  # noqa: E402

DEFAULT_CONFIG_PATH = _PROMO_DIR / "promo_storyboard_config.json"


def configure_utf8_stdout() -> None:
    """Windows konzolon is biztosítja a magyar ékezetek hibamentes kiírását."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")


def parse_cli_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parancssori kapcsolók (`--config`, `--fast`, `--loop`) feldolgozása."""
    parser = argparse.ArgumentParser(
        description="ASCII Duo Snake — Adatvezérelt (Data-Driven) 4 fázisú promóciós demó"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="A promóciós storyboard JSON fájl elérési útja (alapértelmezett: promo/promo_storyboard_config.json)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Gyors, nem-blokkoló előnézet (0 mp késleltetés, képernyőtörlés nélkül)",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Folyamatos konferencia / kivetítő hurok (kilépés: Ctrl+C)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Betölti a JSON forgatókönyvet és elindítja a promóciós bemutatót."""
    configure_utf8_stdout()
    args = parse_cli_arguments(argv)
    try:
        storyboard = load_promo_storyboard_config(args.config)
    except PromoConfigError as exc:
        print(f"[HIBA] {exc}", file=sys.stderr)
        return 1

    run_promo_storyboard(
        storyboard=storyboard,
        fast_mode=args.fast,
        loop_forever=args.loop,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
