"""CLI BELÉPÉSI PONT — Adatvezérelt Automatikus Promóciós Demó (`promo/run_promo_demo.py`).

Használat:
    python -m promo.run_promo_demo                              # Alapértelmezett JSON bemutató
    python -m promo.run_promo_demo --fast                       # Gyors CI/előnézet (0 mp várakozás)
    python -m promo.run_promo_demo --loop                       # Kivetítő hurok (Ctrl+C)
    python -m promo.run_promo_demo --mute                       # Néma mód (8-bites hang nélkül)
    python -m promo.run_promo_demo --config sajat_promo.json    # Saját szerkesztett JSON forgatókönyv
"""

import argparse
from pathlib import Path
import sys

from promo.promo_config_loader import PromoConfigError, load_promo_storyboard_config
from promo.promo_storyboard import run_promo_storyboard

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "promo_storyboard_config.json"


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
    parser.add_argument(
        "--mute",
        action="store_true",
        help="Néma mód (kikapcsolja a 8-bites retro játéktermi hanghatásokat)",
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
        enable_sound=not args.mute,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
