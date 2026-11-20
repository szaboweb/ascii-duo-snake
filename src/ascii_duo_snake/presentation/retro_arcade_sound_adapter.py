"""4. PRESENTATION RÉTEG — RETRO JÁTÉKTERMI HANGADAPTER (`RetroArcadeSoundAdapter`).

Miért a Presentation rétegben van a hang?
    A Clean Architecture szabályai szerint a hanghatás (beep / chiptune) pontosan
    olyan kimeneti mellékhatás (I/O), mint a képernyőre rajzolás (`AsciiBoardRenderer`).
    A Domain réteg (`GameRulesEngine`, `game_events.py`) nem hívhat közvetlenül
    `winsound.Beep`-et — csak tiszta `FruitEatenEvent` és `MatchEndedEvent`
    értékobjektumokat bocsát ki.

Hogyan kapcsolódik össze a kettő (Observer / Pub-Sub minta)?
    A `RetroArcadeSoundAdapter.on_domain_event()` metódust feliratkoztatjuk a
    7. fázisban megismert `GameEventBus`-ra:
        `event_bus.subscribe_listener(sound_adapter.on_domain_event)`
    Így amikor a kígyó almát, aranydinnyét eszik vagy falnak ütközik, a hangadapter
    automatikusan megszólaltatja a megfelelő 8-bites hangfrekvenciát!
"""

from collections.abc import Callable

from ..domain.game_enums import FruitType
from ..domain.game_events import FruitEatenEvent, GameDomainEvent, MatchEndedEvent

ToneEmitter = Callable[[int, int], None]

# Deklaratív (Data-Driven) hangkatalógus: gyümölcstípus -> (frekvencia_hz, hossz_ms) sorozat
FRUIT_SOUND_MELODIES: dict[FruitType, tuple[tuple[int, int], ...]] = {
    FruitType.APPLE: ((880, 85),),
    FruitType.GOLDEN_MELON: ((660, 75), (990, 75), (1320, 130)),
}

MATCH_ENDED_MELODY: tuple[tuple[int, int], ...] = ((330, 90), (220, 170))
SCENE_TRANSITION_MELODY: tuple[tuple[int, int], ...] = ((523, 55), (659, 75))
STEP_TICK_TONE: tuple[int, int] = (440, 35)


def emit_system_beep(frequency_hz: int, duration_ms: int) -> None:
    """Alapértelmezett, külső függőség nélküli rendszerhang-kibocsátó (Windows `winsound`)."""
    try:
        import winsound

        winsound.Beep(int(frequency_hz), int(duration_ms))
    except (ImportError, RuntimeError, ValueError):
        # Nem-Windows rendszeren vagy hangkártya nélküli CI környezetben némán továbbhalad.
        pass


class RetroArcadeSoundAdapter:
    """A `GameEventBus` eseményeire feliratkozó, tesztelhető 8-bites hangadapter."""

    def __init__(
        self,
        enabled: bool = True,
        tone_emitter: ToneEmitter | None = None,
    ) -> None:
        """DI konstruktor: tesztekben `tone_emitter` segítségével némán ellenőrizhető."""
        self._enabled = enabled
        self._tone_emitter: ToneEmitter = tone_emitter or emit_system_beep

    @property
    def enabled(self) -> bool:
        """GETTER: visszaadja, hogy aktív-e a hangkimenet."""
        return self._enabled

    def play_tone(self, frequency_hz: int, duration_ms: int) -> None:
        """Lejátszik egyetlen hangot (`frequency_hz` Hz, `duration_ms` ms), ha engedélyezett."""
        if not self._enabled:
            return
        self._tone_emitter(frequency_hz, duration_ms)

    def play_melody(self, notes: tuple[tuple[int, int], ...]) -> None:
        """Lejátszik egy több hangból álló rövid 8-bites dallamot."""
        for frequency_hz, duration_ms in notes:
            self.play_tone(frequency_hz, duration_ms)

    def play_scene_fanfare(self) -> None:
        """Rövid kétjegyű fanfár új előadási fázis / jelenet indulásakor."""
        self.play_melody(SCENE_TRANSITION_MELODY)

    def play_step_tick(self) -> None:
        """Finom, rövid ütemhang szimulációs lépéskor."""
        self.play_tone(STEP_TICK_TONE[0], STEP_TICK_TONE[1])

    def on_domain_event(self, event: GameDomainEvent) -> None:
        """Observer callback: a `GameEventBus` automatikusan meghívja minden eseménynél."""
        if isinstance(event, FruitEatenEvent):
            melody = FRUIT_SOUND_MELODIES.get(event.fruit_type, ((880, 85),))
            self.play_melody(melody)
        elif isinstance(event, MatchEndedEvent):
            self.play_melody(MATCH_ENDED_MELODY)
