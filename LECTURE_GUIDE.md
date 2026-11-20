# Oktatói Segédlet — 8 Fázisú Clean Architecture & Szoftvermérnöki Kurzus (`phase-1` .. `phase-8`)

Ez a repó **8 egymásra épülő, nehézségi fokozat szerint rendezett (~45 perces) előadási fázisra** van bontva. Minden fázis önálló Git tagként (`phase-1` .. `phase-8`) és branchként is elérhető, önállóan futtatható és tesztelhető.

---

## Alapozó Modulok (1–4. Előadás)

1. **1. Előadás (`phase-1` / `phase-1-alapok`) — Alapok, Adattípusok és Statikus Szoba (~45 perc)**
   - **Fogalmak:** `Enum` (`PlayerId`, `Direction`, `GameStatus`), `GridPoint` Value Object (`__add__`), Immutable Entity (`SnakeEntity`), Single Source of Truth (`WorldState`), Stateless `AsciiBoardRenderer`.
2. **2. Előadás (`phase-2` / `phase-2-egy-kigyo`) — 1 Kígyó Irányítása, Szabályok és Getter/Setter (~45 perc)**
   - **Fogalmak:** 180°-os visszafordulás tiltása (`is_opposite_direction`), Pure Function (`GameRulesEngine.compute_next_world_state`), falütközés, `@property` Getter & validáló `@tick_rate_hz.setter` (`1..60 Hz`), `TerminalKeyboardAdapter` Context Manager.
3. **3. Előadás (`phase-3` / `phase-3-ket-kigyo-gyumolcs`) — 2. Kígyó, Véletlengenerálás és Növekedés (~45 perc)**
   - **Fogalmak:** Data-Driven `FRUIT_CATALOG` (`MappingProxyType`, `APPLE` +1, `GOLDEN_MELON` +3), `RandomNumberProvider` Protocol & DI (`SystemRandomAdapter` vs `FakeRandomNumberProvider`), `pending_growth`, head-swap tunneling védelem.
4. **4. Előadás (`phase-4` / `phase-4-teljes-jatek`) — Állapot-ellenőrzés, Manifest, Recorder és Clean Architecture (~45 perc)**
   - **Fogalmak:** `JsonRoomManifestLoader` + `InvalidRoomManifestException` (Exception Wrapping), `InputRecorderService` (Encapsulation), Composition Root (`game_cli_entrypoint.py`), valamint a különálló Data-Driven `promo/` szimulátor.

---

## Haladó Szoftvermérnöki Modulok Nehézségi Sorrendben (5–8. Előadás)

5. **5. Előadás (`phase-5` / `phase-5-theming-es-fsm`) — Data-Driven Theming & Táblázatvezérelt Véges Állapotgép (FSM) (~45 perc — Könnyű-Közepes)**
   - **Diff:** `git diff phase-4 phase-5`
   - **Új modulok:** `presentation/board_theme_catalog.py` (`BoardThemeSpec`, `BOARD_THEME_CATALOG`: `classic_ascii`, `neon_arcade`, `retro_matrix`), `domain/session_state_machine.py` (`SessionPhase`, `ALLOWED_PHASE_TRANSITIONS`, `SessionStateMachine`).
   - **Tanulság:** Hogyan cserélhető le a teljes vizuális megjelenítés (skin) és hogyan előzhetők meg az illegális állapotátmenetek (`MENU -> PAUSED`) egyetlen deklaratív átmenet-táblával, `if/elif` spagetti nélkül.

6. **6. Előadás (`phase-6` / `phase-6-strategy-bot-ai`) — Strategy Pattern & Open/Closed Principle (Cserélhető Bot AI) (~45 perc — Közepes)**
   - **Diff:** `git diff phase-5 phase-6`
   - **Új modul:** `domain/bot_steering_strategy.py` (`BotSteeringStrategy` Protocol, `GreedyFruitBotStrategy`, `CautiousSurvivalBotStrategy`, `BOT_STRATEGY_CATALOG`).
   - **Tanulság:** Míg a Data-Driven Config *adatot* cserél, addig a Strategy Pattern *viselkedést (algoritmust)* cserél futásidőben a `GameRulesEngine` egyetlen sorának módosítása nélkül (Open/Closed Principle).

7. **7. Előadás (`phase-7` / `phase-7-observer-event-bus`) — Domain Events & Observer Pattern (Pub-Sub Eseménybusz és Telemetria) (~45 perc — Közepes-Haladó)**
   - **Diff:** `git diff phase-6 phase-7`
   - **Új modulok:** `domain/game_events.py` (`FruitEatenEvent`, `MatchEndedEvent`, `detect_transition_events`), `application/game_event_bus.py` (`GameEventBus`, `MatchTelemetryCollector`).
   - **Tanulság:** Laza csatolás (*Loose Coupling*): a játékmotor nem tud a statisztikákról vagy az achievement jelvényekről (`P1_DINNYEVADASZ`), mégis valós időben értesíti a feliratkozókat.

8. **8. Előadás (`phase-8` / `phase-8-replay-es-invarians-teszt`, `main`) — Event Sourcing Replay & 500-Lépéses Invariáns Fuzz-Teszt (~45 perc — Haladó / Mesterfok)**
   - **Diff:** `git diff phase-7 phase-8`
   - **Új modulok:** `application/deterministic_replay_service.py` (`MatchReplaySnapshot`, `DeterministicReplayService`), `presentation/retro_arcade_sound_adapter.py` (`RetroArcadeSoundAdapter`, opcionális 8-bites hanghatások `GameEventBus` feliratkozóként, Windows `winsound.Beep`, más OS-en néma fallback), `tests/test_advanced_phases_and_invariants.py`.
   - **Tanulság:** Itt ér össze minden: a `Pure Function` + `Random Seed` + `InputRecord` lista lehetővé teszi egy teljes meccs JSON-ba mentését és 100%-ig azonos visszajátszását, az 500 valódi tick-en át futó invariáns-teszt pedig minden lépésben ellenőrzi a domain szabályokat (nem csökkenő kígyóhossz, legális gyümölcsmező, érvényes katalógustípus).

---

## Élő Demó és Ellenőrző Parancsok
```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
$env:PYTHONPATH="src"; python main.py --demo
$env:PYTHONPATH="src"; python main.py --demo --theme neon_arcade --p2-bot cautious
$env:PYTHONPATH="src"; python main.py --speed 6 --theme neon_arcade --p2-bot cautious --sound
$env:PYTHONPATH="src"; python main.py --demo --record meccs_replay.json
$env:PYTHONPATH="src"; python main.py --replay meccs_replay.json --theme neon_arcade
$env:PYTHONPATH="src"; python -m promo.run_promo_demo --fast
$env:PYTHONPATH="src"; python -m promo.run_promo_demo
```
