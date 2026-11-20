# ASCII Duo Snake — Programozást Oktató Clean Architecture Repó (Python)

Ez a repó egy **kétszemélyes, terminálban futó (ASCII/TUI) Snake játék**, amely **0 külső függőséggel** (csak Python 3.11+ standard könyvtárral) mutatja be a tiszta szoftverfejlesztés alapelveit, rétegeit és programozási mintáit 8 egymásra épülő előadási fázisban.

> **A cél nem a leglátványosabb játék**, hanem az, hogy minden kulcsfogalom — *Domain, Contract, State, Enum, Value Object, Operator, Pure Function, Exception, Getter/Setter, Encapsulation, Recorder, DI, Catalog, Manifest, Context Manager, Mock, Theming Catalog, Table-Driven FSM, Strategy Pattern / OCP, Domain Events, Pub-Sub Event Bus, Deterministic Replay, Property-Based Invariant Test* — önálló, 20–250 soros alkalmazásmodulokban (`src/`) legyen tanulmányozható.
>
> **Elnevezési szabályok és oktatói tematika:** Lásd a **[`NAMING_CONVENTION.md`](NAMING_CONVENTION.md)** és a **[`LECTURE_GUIDE.md`](LECTURE_GUIDE.md)** fájlokat.

---

## 1. Architektúra: A 4 réteg és a Függőségi Szabály

A program a **Clean Architecture (Tiszta Architektúra)** elvét követi. A legfontosabb szabály a **Dependency Rule (Függőségi Szabály)**: a nyilak **mindig befelé** mutatnak — a belső `domain/` réteg **semmit nem tud** arról, hogy terminálban fut-e a játék, szól-e a hangszóró, vagy JSON fájlból érkezik-e a pálya és a visszajátszás.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  COMPOSITION ROOT:  game_cli_entrypoint.py / main.py  (Összedrótozás: DI)    │
└──────────────┬──────────────────────────────┬────────────────────────┬───────┘
               ▼                              ▼                        ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐ ┌────────────────────────────┐
│  4. PRESENTATION (TUI/Audio) │ │  3. INFRASTRUCTURE (I/O)     │ │  2. APPLICATION            │
│  - ascii_board_renderer.py   │ │  - json_room_manifest_loader │ │  - game_loop_controller.py │
│  - board_theme_catalog.py    │ │  - system_random_adapter.py  │ │  - input_recorder_service  │
│  - retro_arcade_sound_adapter│ └──────────────┬───────────────┘ │  - game_event_bus.py       │
│  - terminal_keyboard_adapter │                │                 │  - deterministic_replay_   │
└──────────────┬───────────────┘                │                 │    service.py              │
               │                                │                 └──────────────┬─────────────┘
               └────────────────────────────────┼────────────────────────────────┘
                                                ▼
               ┌────────────────────────────────────────────────────────────┐
               │  1. DOMAIN (Tiszta szabályok: 0 UI, 0 I/O, 0 rng)          │
               │  game_enums, domain_exceptions, grid_point_value,          │
               │  fruit_catalog, snake_entity, world_state,                 │
               │  domain_contracts (Protocol), game_rules_engine,           │
               │  session_state_machine, bot_steering_strategy, game_events │
               └────────────────────────────────────────────────────────────┘
```

**Miért jó ez?**
- Ha terminál helyett más grafikus felületet szeretnél, **csak a `presentation/` mappát kell kicserélned**.
- Ha tesztelni akarod az ütközést, a bot AI-t, az eseménybuszt vagy a visszajátszást, a `domain/` és az `application/` **képernyő, billentyűzet és valódi óra nélkül**, ezredmásodpercek alatt futtatható.

---

## 2. Hogyan kel életre egyetlen képkocka? (Adatfolyam)

Minden időlépés (**tick**) ugyanazon a tiszta körforgáson (Game Loop) megy végig:

1. **Bemenet (`presentation/terminal_keyboard_adapter.py` + `domain/bot_steering_strategy.py`):** A `TerminalKeyboardAdapter.poll_keyboard_commands()` nem-blokkoló módon kiolvassa a billentyűket (`w` -> `(PlayerId.P1, Direction.UP)`), vagy `--p2-bot` esetén a választott `BotSteeringStrategy` dönt a `P2` következő irányáról.
2. **Vezérlés és naplózás (`application/game_loop_controller.py` + `input_recorder_service.py`):** A `GameLoopController.steer_player_snake()` elmenti az irányváltást az `InputRecorderService.record_player_input()` metódussal, majd elkészíti az új irányba fordított `SnakeEntity`-t.
3. **Szabályok és események (`domain/game_rules_engine.py` + `domain/game_events.py` + `application/game_event_bus.py`):** A `GameLoopController.advance_simulation_tick(delta_seconds)` lefuttatja a tiszta `GameRulesEngine.compute_next_world_state(...)` számítást, a `detect_transition_events()` kinyeri a `FruitEatenEvent` / `MatchEndedEvent` eseményeket, a `GameEventBus` pedig értesíti a feliratkozókat (`MatchTelemetryCollector`, `RetroArcadeSoundAdapter`).
4. **Megjelenítés (`presentation/ascii_board_renderer.py` + `presentation/board_theme_catalog.py`):** Az `AsciiBoardRenderer.render_board_frame(controller.current_state)` a választott `BoardThemeSpec` (`classic_ascii`, `neon_arcade`, `retro_matrix`) karaktereivel rajzolja ki az aktuális `WorldState` állapotot.

---

## 3. Programozási alapelvek és fogalomtérkép

| Fogalom / Alapelv | Hol találod? | Mit jelent a gyakorlatban? |
| :--- | :--- | :--- |
| **Elnevezési Konvenciók** | [`NAMING_CONVENTION.md`](NAMING_CONVENTION.md) | Egységes fájlnév-, osztály-, ige-első függvény- és rövidítésmentes változó-elnevezési szabályok. |
| **Manifest & Literal** | `assets/room_manifest.json` | A pálya mérete, kezdőpontjai és a 3 mp-es gyümölcsidőzítés kódmódosítás nélkül, deklaratív JSON-ból paraméterezhető. |
| **Enum** | `domain/game_enums.py` | Zárt értékkészlet (`PlayerId`, `Direction`, `GameStatus`, `FruitType`). Megelőzi a nyers stringek elgépelését. |
| **Domain Exception** | `domain/domain_exceptions.py` | Saját, beszédes kivétel (`InvalidRoomManifestException`) hibás pályák célzott elkapásához. |
| **Value Object & Operator** | `domain/grid_point_value.py` | `GridPoint(x, y)` megváltoztathatatlan koordináta saját `+` (`__add__`) és `==` operátorral. |
| **Catalog (Data-Driven SSOT)** | `domain/fruit_catalog.py` | Csak olvasható (`MappingProxyType`) gyümölcstár (`APPLE`, `GOLDEN_MELON`). |
| **Entity, Stat, Method** | `domain/snake_entity.py` | `SnakeEntity` egyedi `player_id`-val, `fruits_eaten` számlálóval és tiszta `change_direction()` metódussal. |
| **Immutable State (SSOT)** | `domain/world_state.py` | A teljes világ egyetlen `frozen=True` `WorldState` objektumban él. |
| **Contract (Interface / DIP)** | `domain/domain_contracts.py` | `typing.Protocol` szerződések (`RoomManifestLoader`, `RandomNumberProvider`). |
| **Pure Function & Predicates** | `domain/game_rules_engine.py` | `GameRulesEngine.compute_next_world_state()` és mellékhatásmentes predikátumai. |
| **Data-Driven Theming** | `presentation/board_theme_catalog.py` | `BoardThemeSpec` és `BOARD_THEME_CATALOG` (`classic_ascii`, `neon_arcade`, `retro_matrix`), kiválasztás a `select_board_theme()` függvénnyel. |
| **Table-Driven FSM** | `domain/session_state_machine.py` | `SessionPhase`, `ALLOWED_PHASE_TRANSITIONS`, `SessionStateMachine` és `InvalidPhaseTransitionException` az illegális állapotátmenetek tiltására. |
| **Strategy Pattern & OCP** | `domain/bot_steering_strategy.py` | `BotSteeringStrategy` Protocol, `GreedyFruitBotStrategy`, `CautiousSurvivalBotStrategy` és `BOT_STRATEGY_CATALOG` a szabálymotor átírása nélküli AI-cseréhez. |
| **Domain Events** | `domain/game_events.py` | `FruitEatenEvent`, `MatchEndedEvent` megváltoztathatatlan események és tiszta `detect_transition_events()` átmenet-felismerés. |
| **Observer / Pub-Sub Event Bus** | `application/game_event_bus.py`, `presentation/retro_arcade_sound_adapter.py` | `GameEventBus`, `MatchTelemetryCollector` (statisztika és jelvények) és `RetroArcadeSoundAdapter` (eseményre megszólaló 8-bites hangadapter). |
| **Deterministic Replay** | `application/deterministic_replay_service.py` | `MatchReplaySnapshot` és `DeterministicReplayService`: teljes meccs JSON szerializálása és bitre/tickre azonos visszajátszása. |
| **Encapsulation & Recorder** | `application/input_recorder_service.py` | Privát `_input_history` lista + csak olvasható `history` getter (`tuple`). |
| **Getter & Setter** | `application/game_loop_controller.py` | `@property` (`current_state`, `tick_rate_hz`) és `@tick_rate_hz.setter` (`1.0..60.0 Hz` validációval). |
| **Dependency Injection (DI)** | `application/game_loop_controller.py`, `game_cli_entrypoint.py` | Kívülről beadott függőségek (`RandomNumberProvider`, `InputRecorderService`, `GameEventBus`). |
| **Deserialization & Wrapping** | `infrastructure/json_room_manifest_loader.py` | JSON fájl vagy nyers szöveg (`parse_manifest_text`) validált átalakítása `WorldState`-té. |
| **Stateless Presentation & Context Manager** | `presentation/ascii_board_renderer.py`, `terminal_keyboard_adapter.py` | Tesztelhető `format_board_frame()` és POSIX terminál módot visszaállító `with TerminalKeyboardAdapter():`. |
| **Unit, CLI & Invariáns Fuzz-Teszt** | `tests/test_snake_game_rules_and_engine.py`, `tests/test_advanced_phases_and_invariants.py`, `tests/test_promo_config_loader.py` | `FakeRandomNumberProvider` unit tesztek, `--record`/`--replay` CLI regresszió és 500 valódi tick-en át ellenőrzött domain invariáns-teszt. |

---

## 4. Programozási logikák a motorháztető alatt

### A) Miért nem változtatjuk meg a régi objektumokat? (Immutability + `replace()`)
Minden domain értékobjektum `frozen=True`, a módosítások pedig `dataclasses.replace(world_state, ...)` hívással **új pillanatképet** készítenek. Így a `detect_transition_events(previous_state, next_state)` és a `DeterministicReplayService` mellékhatás nélkül képes összehasonlítani és visszajátszani az állapotokat.

### B) Több-lépéses növekedés (`pending_growth`)
A `GOLDEN_MELON` `growth_amount = 3` értékű. A `GameRulesEngine.advance_snake_body()` a többletet a `snake.pending_growth` mezőbe teszi el, majd a következő tickekben nem vágja le a farkat, amíg `pending_growth > 0`.

### C) Ütközésvizsgálat és a „fej-helycsere” (*head-swap / tunneling*) sarokeset
Két egymással szemben haladó kígyó közvetlen helycseréjét (`P1: (5,5)->(6,5)` és `P2: (6,5)->(5,5)`) a `GameRulesEngine.is_head_swap_collision(...)` tiszta predikátum külön kiszűri (`GameStatus.DRAW`).

### D) Garantáltan ütközésmentes gyümölcs-elhelyezés (`free_cells`)
A `GameRulesEngine.select_free_fruit_position()` `set`-be gyűjti a két kígyó összes testpontját (`O(1)` ellenőrzés), kiszűri a szabad belső mezőket, és ezekből sorsol a beadott `RandomNumberProvider` segítségével (üres lista esetén `None`-t ad vissza).

### E) 180 fokos visszafordulás tiltása lookup táblával és tiszta predikátummal
A `snake_entity.py` deklaratív `OPPOSITE_DIRECTIONS` szótárat és `is_opposite_direction()` predikátumot használ `if/elif` lánc helyett.

---

## 5. Gyakorlati tanulófeladatok (Próbáld ki!)

1. **Új gyümölcs hozzáadása (Data-Driven tervezés):**
   Adj hozzá egy `BERRY` (`symbol="+"`, `growth_amount=2`) elemet a `domain/game_enums.py` és `domain/fruit_catalog.py` fájlokban — a szabálymotor és a megjelenítő módosítás nélkül kezelni fogja.
2. **Új pálya készítése kódírás nélkül (Manifest):**
   Hozz létre egy `assets/small_arena.json` fájlt `14x12`-es mérettel és `1.5` mp-es gyümölcsidőzítéssel, majd indítsd így:
   `$env:PYTHONPATH="src"; python main.py --manifest assets/small_arena.json`
3. **Új Bot AI stratégia hozzáadása (Strategy Pattern / OCP):**
   Implementálj egy új stratégiát (például `RandomSafeBotStrategy`) a `domain/bot_steering_strategy.py` modulban, regisztráld a `BOT_STRATEGY_CATALOG` szótárban, és futtasd a játékot a `GameRulesEngine` átírása nélkül `--p2-bot` kapcsolóval.
4. **Saját tábla-téma hozzáadása (Data-Driven Theming):**
   Vegyél fel egy új `BoardThemeSpec` bejegyzést a `presentation/board_theme_catalog.py` `BOARD_THEME_CATALOG` szótárába, majd indítsd el vele a demót `--theme <uj_nev>` kapcsolóval.

---

## 6. Futtatás és tesztelés

```powershell
# 1. Összes unit, promo-konfig és 500-tick invariáns teszt futtatása
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v

# 2. Alap nem-interaktív demó
$env:PYTHONPATH="src"; python main.py --demo

# 3. Demó Neon Arcade témával, óvatos P2 bottal és rögzített random maggal
$env:PYTHONPATH="src"; python main.py --demo --theme neon_arcade --p2-bot cautious --seed 42

# 4. Interaktív 2 fős vagy bot-elleni játék (--sound: Windows-on winsound.Beep, más OS-en néma marad)
$env:PYTHONPATH="src"; python main.py --speed 6 --theme retro_matrix --p2-bot greedy --sound

# 5. Egyedi pálya, bemenet-rögzítés JSON fájlba és determinisztikus visszajátszás
$env:PYTHONPATH="src"; python main.py --manifest assets/room_manifest.json --demo --record replay.json
$env:PYTHONPATH="src"; python main.py --replay replay.json --theme neon_arcade
```

---

## 7. 8 Előadási Fázis (Git branch & tag navigáció)

A repó 8 önálló, tanítási és nehézségi sorrendben felépített fázisra van bontva — mindegyik külön branch-en és tag-en futtatható, részletes tematikájuk a [`LECTURE_GUIDE.md`](LECTURE_GUIDE.md) fájlban található:

| Fázis | Tag / Branch | Fő téma (~45 perc) | Diff megtekintése |
| :--- | :--- | :--- | :--- |
| **1. előadás** | `phase-1` / `phase-1-alapok` | Alapok, `Enum`, `GridPoint`, `WorldState` és statikus szoba | `git checkout phase-1` |
| **2. előadás** | `phase-2` / `phase-2-egy-kigyo` | 1 kígyó irányítása (`WASD`), tiszta szabálymotor, getter/setter | `git diff phase-1 phase-2` |
| **3. előadás** | `phase-3` / `phase-3-ket-kigyo-gyumolcs` | 2. kígyó (`IJKL`), `FRUIT_CATALOG`, DI, Mock, `pending_growth`, `head-swap` | `git diff phase-2 phase-3` |
| **4. előadás** | `phase-4` / `phase-4-teljes-jatek` | Állapot-ellenőrzés, JSON Manifest, `InvalidRoomManifestException`, `InputRecorderService` | `git diff phase-3 phase-4` |
| **5. előadás** | `phase-5` / `phase-5-theming-es-fsm` | Data-Driven Theming (`BOARD_THEME_CATALOG`) és Táblázatvezérelt FSM (`SessionStateMachine`) | `git diff phase-4 phase-5` |
| **6. előadás** | `phase-6` / `phase-6-strategy-bot-ai` | Strategy Pattern & OCP: cserélhető bot AI (`greedy`, `cautious`) | `git diff phase-5 phase-6` |
| **7. előadás** | `phase-7` / `phase-7-observer-event-bus` | Domain Events (`FruitEatenEvent`, `MatchEndedEvent`), `GameEventBus` és `MatchTelemetryCollector` | `git diff phase-6 phase-7` |
| **8. előadás** | `phase-8` / `phase-8-replay-es-invarians-teszt` (`main`) | `DeterministicReplayService`, `RetroArcadeSoundAdapter`, teljes CLI bekötés és 500 tick-es invariáns-teszt | `git diff phase-7 phase-8` |

```powershell
# Ugrás bármelyik előadási fázisra (pl. 5. előadás):
git checkout phase-5
# Visszatérés a teljes projektre:
git checkout main
```

---

## 8. Automatikus Promóciós Demó (`promo/`)

A `promo/` csomag egy **0 külső függőséges, adatvezérelt (Data-Driven) és valódi játékmotort futtató terminál-bemutatót** tartalmaz (teljesen elkülönítve a `src/` rétegektől), amely **8 koreografált jelenetben** mutatja be mind a 8 előadás kulcsfogalmait:

> **Fontos futtatási szabály:** A bemutatót **modulként (`python -m promo.run_promo_demo`)** kell indítani a projekt gyökérkönyvtárából (`PYTHONPATH="src"` mellett), mert így a Python közvetlenül megtalálja a `promo` csomagot és a `src/` modulokat mindenféle `sys.path.insert` kerülőút nélkül (ne közvetlenül a `promo/run_promo_demo.py` fájlnévvel indítsd). A `--mute` kapcsolóval a 8-bites hanghatások letilthatók.

```powershell
# Normál, animált bemutató (előadáshoz / kivetítőre):
$env:PYTHONPATH="src"; python -m promo.run_promo_demo

# Gyors előnézet (0 mp késleltetés, képernyőtörlés és hang nélkül):
$env:PYTHONPATH="src"; python -m promo.run_promo_demo --fast

# Folyamatos konferencia- / kivetítő-hurok (kilépés: Ctrl+C):
$env:PYTHONPATH="src"; python -m promo.run_promo_demo --loop

# Néma módú lejátszás animációval (8-bites hanghatások nélkül):
$env:PYTHONPATH="src"; python -m promo.run_promo_demo --mute

# Saját JSON forgatókönyv futtatása kódmódosítás nélkül:
$env:PYTHONPATH="src"; python -m promo.run_promo_demo --config promo/promo_storyboard_config.json --fast
```
