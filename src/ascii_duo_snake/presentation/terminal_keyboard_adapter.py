"""4. PRESENTATION (TUI) RÉTEG — INPUT ADAPTER & CONTEXT MANAGER.

Miért kell nem-blokkoló billentyűzet-olvasás?
    A sima `input()` megállítja a programot, amíg a felhasználó Enter-t nem nyom —
    egy folyamatosan mozgó Snake játékban viszont a kígyóknak gombnyomás nélkül is
    lépniük kell minden tick-ben.

Mi az a Context Manager (`__enter__` és `__exit__`, azaz `with TerminalKeyboardAdapter():`)?
    Linux/macOS (POSIX) terminálon át kell állítani a terminált `cbreak` módba, hogy
    Enter nélkül is azonnal megérkezzenek a billentyűk. A `with` blokk garantálja, hogy
    kilépéskor — még hiba esetén is! — visszaállítsuk a terminál eredeti beállításait.
"""

from types import MappingProxyType, TracebackType
from typing import Mapping
import sys

from ..domain.game_enums import Direction, PlayerId

# Deklaratív billentyűkiosztás: könnyen bővíthető/módosítható egy helyen.
KEYBOARD_BINDINGS: Mapping[str, tuple[PlayerId, Direction]] = MappingProxyType(
    {
        "w": (PlayerId.P1, Direction.UP),
        "s": (PlayerId.P1, Direction.DOWN),
        "a": (PlayerId.P1, Direction.LEFT),
        "d": (PlayerId.P1, Direction.RIGHT),
        "i": (PlayerId.P2, Direction.UP),
        "k": (PlayerId.P2, Direction.DOWN),
        "j": (PlayerId.P2, Direction.LEFT),
        "l": (PlayerId.P2, Direction.RIGHT),
    }
)


class TerminalKeyboardAdapter:
    """Platform-független (Windows / POSIX) nem-blokkoló billentyűzet-adapter."""

    def __init__(self) -> None:
        self._stdin_file_descriptor: int | None = None
        self._saved_terminal_settings: object | None = None

    def __enter__(self) -> "TerminalKeyboardAdapter":
        """Belépés a `with` blokkba: POSIX-on aktiválja a nyers (cbreak) karakterolvasást."""
        if sys.platform != "win32" and sys.stdin.isatty():
            import termios
            import tty

            self._stdin_file_descriptor = sys.stdin.fileno()
            self._saved_terminal_settings = termios.tcgetattr(self._stdin_file_descriptor)
            tty.setcbreak(self._stdin_file_descriptor)
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        exception_traceback: TracebackType | None,
    ) -> None:
        """Kilépés a `with` blokkból: mindig visszaállítja a terminál eredeti módját."""
        if self._stdin_file_descriptor is not None and self._saved_terminal_settings is not None:
            import termios

            termios.tcsetattr(
                self._stdin_file_descriptor,
                termios.TCSADRAIN,
                self._saved_terminal_settings,  # type: ignore[arg-type]
            )

    def poll_keyboard_commands(self) -> tuple[list[tuple[PlayerId, Direction]], bool]:
        """Kiolvassa a várakozó billentyűket és domain parancsokká fordítja őket.

        Visszatérési érték:
            `(queued_commands, quit_requested)` — az érvényes irányváltások listája,
            illetve igaz, ha a felhasználó megnyomta a `Q` kilépés gombot.
        """
        queued_commands: list[tuple[PlayerId, Direction]] = []
        quit_requested = False

        for pressed_character in self._read_raw_characters():
            normalized_character = pressed_character.lower()
            if normalized_character == "q":
                quit_requested = True
            elif normalized_character in KEYBOARD_BINDINGS:
                queued_commands.append(KEYBOARD_BINDINGS[normalized_character])

        return queued_commands, quit_requested

    def _read_raw_characters(self) -> list[str]:
        """Kiüríti a billentyűzet-puffert anélkül, hogy várakozna (non-blocking)."""
        if sys.platform == "win32":
            import msvcrt

            raw_characters: list[str] = []
            while msvcrt.kbhit():
                raw_characters.append(msvcrt.getwch())
            return raw_characters

        if not sys.stdin.isatty():
            return []

        import select

        raw_characters = []
        while select.select([sys.stdin], [], [], 0.0)[0]:
            raw_characters.append(sys.stdin.read(1))
        return raw_characters
