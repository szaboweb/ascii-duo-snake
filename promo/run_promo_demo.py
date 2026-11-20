"""CLI BELÉPÉSI PONT — Automatikus Promóciós Demó (`promo/run_promo_demo.py`).

Használat:
    $env:PYTHONPATH="src"; python promo/run_promo_demo.py           # Animált bemutató
    $env:PYTHONPATH="src"; python promo/run_promo_demo.py --fast    # Gyors CI/előnézet
    $env:PYTHONPATH="src"; python promo/run_promo_demo.py --loop    # Kivetítő hurok (Ctrl+C)
"""

import argparse
from pathlib import Path
import sys

# Biztosítja, hogy a `promo/` és a `src/` közvetlen futtatáskor is megtalálható legyen
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from promo_storyboard import (  # noqa: E402
    ANSI_CYAN,
    ANSI_GREEN,
    PromoPlaybackConfig,
    build_promo_scenes,
    colorize,
)


def configure_utf8_stdout() -> None:
    """Windows konzolon is biztosítja a magyar ékezetek hibamentes kiírását."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")


def run_promo_showcase(config: PromoPlaybackConfig, loop_forever: bool) -> None:
    """Végigfuttatja a 4 promóciós jelenetet egyszer vagy folyamatos hurokban."""
    scenes = build_promo_scenes()
    cycle_number = 0
    try:
        while True:
            cycle_number += 1
            for scene in scenes:
                scene.runner(config)
            if not loop_forever:
                break
            print(colorize(f"\n--- Promóciós kör #{cycle_number} befejezve, újraindítás... ---", ANSI_CYAN))
    except KeyboardInterrupt:
        print(colorize("\nPromóciós bemutató leállítva (Ctrl+C).", ANSI_GREEN))


def main() -> None:
    """Argumentumok feldolgozása és a 4 jelenetes promóciós demó elindítása."""
    configure_utf8_stdout()
    parser = argparse.ArgumentParser(
        description="ASCII Duo Snake — 4 előadási fázis automatikus promóciós demója"
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
    args = parser.parse_args()

    config = PromoPlaybackConfig(
        frame_delay_seconds=0.0 if args.fast else 0.28,
        typewriter_delay_seconds=0.0 if args.fast else 0.012,
        clear_screen=not args.fast,
    )
    run_promo_showcase(config=config, loop_forever=args.loop)


if __name__ == "__main__":
    main()
