"""4. PRESENTATION (TUI) RÉTEG — CONTEXT MANAGER & KEYBOARD ADAPTER (2. előadás).

A `with TerminalKeyboardAdapter():` garantálja, hogy POSIX terminálon kilépéskor
minden esetben visszaálljon az eredeti terminál-beállítás.
"""

from types import TracebackType
import sys

from ..domain.game_enums import Direction, PlayerId

KEYBOARD_BINDINGS: dict[str, tuple[PlayerId, Direction]] = {
    "w": (PlayerId.P1, Direction.UP),
    "s": (PlayerId.P1, Direction.DOWN),
    "a": (PlayerId.P1, Direction.LEFT),
    "d": (PlayerId.P1, Direction.RIGHT),
}


class TerminalKeyboardAdapter:
    """Platform-független (Windows / POSIX) nem-blokkoló billentyűzet-adapter."""

    def __init__(self) -> None:
        self._stdin_file_descriptor: int | None = None
        self._posix_original_settings: object | None = None

    def __enter__(self) -> "TerminalKeyboardAdapter":
        if sys.platform != "win32" and sys.stdin.isatty():
            import termios
            import tty

            self._stdin_file_descriptor = sys.stdin.fileno()
            self._posix_original_settings = termios.tcgetattr(self._stdin_file_descriptor)
            tty.setcbreak(self._stdin_file_descriptor)
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        exception_traceback: TracebackType | None,
    ) -> None:
        if self._stdin_file_descriptor is not None and self._posix_original_settings is not None:
            import termios

            termios.tcsetattr(
                self._stdin_file_descriptor,
                termios.TCSADRAIN,
                self._posix_original_settings,  # type: ignore[arg-type]
            )

    def poll_keyboard_commands(self) -> tuple[list[tuple[PlayerId, Direction]], bool]:
        """Kiolvassa a várakozó billentyűket (`WASD` -> irányváltás, `Q` -> kilépés)."""
        commands: list[tuple[PlayerId, Direction]] = []
        quit_requested = False

        for pressed_character in self._read_raw_characters():
            lowered_key = pressed_character.lower()
            if lowered_key == "q":
                quit_requested = True
            elif lowered_key in KEYBOARD_BINDINGS:
                commands.append(KEYBOARD_BINDINGS[lowered_key])

        return commands, quit_requested

    def _read_raw_characters(self) -> list[str]:
        if sys.platform == "win32":
            import msvcrt

            characters: list[str] = []
            while msvcrt.kbhit():
                characters.append(msvcrt.getwch())
            return characters

        if not sys.stdin.isatty():
            return []

        import select

        characters = []
        while select.select([sys.stdin], [], [], 0.0)[0]:
            characters.append(sys.stdin.read(1))
        return characters
