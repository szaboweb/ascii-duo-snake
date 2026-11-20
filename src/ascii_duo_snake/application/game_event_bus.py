"""Eseménybusz (Observer / Pub-Sub minta) és mérkőzés-telemetria gyűjtő modul.

================================================================================
MIÉRT FONTOS EZ A MODUL? (Observer Pattern & Loose Coupling)
================================================================================
Amikor egy játékhoz új funkciókat adunk hozzá (például jelvények feloldása,
statisztikák gyűjtése, hangeffektek lejátszása), a naiv megközelítésben minden
új funkciót közvetlenül a fő játékciklusba (`GameSessionOrchestrator`) drótoznak be.
Ez hamarosan egy átláthatatlan, több száz soros "Spaghetti God Class"-hoz vezet.

A **Megfigyelő (Observer / Publish-Subscribe) tervezési minta** megoldja ezt:
1. A `GameEventBus` egy központi elosztó: az orchestrator csak annyit mond,
   hogy `event_bus.publish_events(events)`.
2. Tetszőleges számú megfigyelő (például a `MatchTelemetryCollector`)
   feliratkozhat (`subscribe_listener`) az eseményekre.
3. Ezáltal a játékmenet-vezérlő és a statisztika/jelvényrendszer **lazán csatolt**
   (loosely coupled) marad, és az Open/Closed Principle (OCP) szerint új
   megfigyelőket adhatunk hozzá a meglévő kód módosítása nélkül!
================================================================================
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from ..domain.game_enums import FruitType, GameStatus, PlayerId
from ..domain.game_events import (
    FruitEatenEvent,
    GameDomainEvent,
    MatchEndedEvent,
)

GameEventListener = Callable[[GameDomainEvent], None]


class GameEventBus:
    """Szinkron Publish-Subscribe eseménybusz tartományi események továbbítására."""

    def __init__(self) -> None:
        """Inicializálja az üres feliratkozó- és eseménynapló-listát."""
        self._listeners: list[GameEventListener] = []
        self._published_events: list[GameDomainEvent] = []

    @property
    def published_events(self) -> tuple[GameDomainEvent, ...]:
        """Visszaadja az eddig publikált összes esemény olvasható tuple másolatát."""
        return tuple(self._published_events)

    def subscribe_listener(self, listener: GameEventListener) -> None:
        """Feliratkoztat egy új eseményfigyelő függvényt vagy metódust.

        Args:
            listener: A meghívandó callback, amely egy `GameDomainEvent` példányt vár.
        """
        self._listeners.append(listener)

    def publish_event(self, event: GameDomainEvent) -> None:
        """Elment egy tartományi eseményt és értesíti az összes feliratkozót.

        Args:
            event: A bekövetkezett tartományi esemény.
        """
        self._published_events.append(event)
        for listener in self._listeners:
            listener(event)

    def publish_events(self, events: Iterable[GameDomainEvent]) -> None:
        """Sorban publikál több tartományi eseményt.

        Args:
            events: A publikálandó tartományi események gyűjteménye.
        """
        for event in events:
            self.publish_event(event)


class MatchTelemetryCollector:
    """Megfigyelő (Observer), amely statisztikákat és jelvényeket gyűjt az eseményekből."""

    def __init__(self) -> None:
        """Inicializálja a játékosonkénti gyümölcsszámlálót és jelvénylistát."""
        self._fruits_by_player: dict[PlayerId, int] = {
            PlayerId.P1: 0,
            PlayerId.P2: 0,
        }
        self._unlocked_badges: list[str] = []
        self._final_status: GameStatus | None = None

    @property
    def fruits_by_player(self) -> dict[PlayerId, int]:
        """Visszaadja a játékosonként elfogyasztott gyümölcsök számát."""
        return dict(self._fruits_by_player)

    @property
    def unlocked_badges(self) -> tuple[str, ...]:
        """Visszaadja a mérkőzés során feloldott jelvények sorrendtartó tuple-jét."""
        return tuple(self._unlocked_badges)

    @property
    def final_status(self) -> GameStatus | None:
        """Visszaadja a mérkőzés záró állapotát, vagy `None`-t, ha még tart."""
        return self._final_status

    def on_domain_event(self, event: GameDomainEvent) -> None:
        """Feldolgoz egy beérkező tartományi eseményt.

        Args:
            event: Az eseménybuszról érkező `FruitEatenEvent` vagy `MatchEndedEvent`.
        """
        if isinstance(event, FruitEatenEvent):
            self._handle_fruit_eaten(event)
        elif isinstance(event, MatchEndedEvent):
            self._final_status = event.final_status

    def _handle_fruit_eaten(self, event: FruitEatenEvent) -> None:
        """Frissíti a gyümölcsszámlálót és ellenőrzi a jelvényfeltételeket."""
        self._fruits_by_player[event.player_id] = event.new_fruits_eaten_count

        if event.fruit_type == FruitType.GOLDEN_MELON:
            self._unlock_badge_once(f"{event.player_id.value}_DINNYEVADASZ")

        if event.new_fruits_eaten_count >= 2:
            self._unlock_badge_once(f"{event.player_id.value}_DUPLA_FALAT")

    def _unlock_badge_once(self, badge_code: str) -> None:
        """Hozzáad egy jelvényt a listához, ha korábban még nem volt feloldva."""
        if badge_code not in self._unlocked_badges:
            self._unlocked_badges.append(badge_code)
