"""1. DOMAIN RÉTEG — EXCEPTION (Saját üzleti kivétel).

Miért érdemes saját kivételosztályt definiálni a beépített `ValueError` helyett?
    A saját kivétel (Domain Exception) nevén nevezi a hibát. A hívó fél így
    célzottan elkaphatja a hibás pályaleírót (`except InvalidRoomManifestException:`),
    anélkül hogy más, váratlan programhibákat véletlenül elnyelne.

Összefüggés a többi fájllal:
    - `infrastructure/json_room_manifest_loader.py` dobja ezt a kivételt, ha a JSON
      hiányos, túl kicsi a szoba, vagy falra kerülne egy kezdőpozíció.
"""


class InvalidRoomManifestException(Exception):
    """Akkor dobódik, ha a betöltendő pálya-manifest megsérti a domain szabályait."""

    def __init__(self, reason: str) -> None:
        """Létrehozza a kivételt emberi olvasásra szánt indoklással."""
        self.reason = reason
        super().__init__(f"Hibás pályaleíró: {reason}")
