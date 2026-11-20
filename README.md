# ASCII Duo Snake — Programozást Oktató Clean Architecture Repó (Python)

Ez a repó egy **kétszemélyes, terminálban futó (ASCII/TUI) Snake játék**, amely **0 külső függőséggel** (csak Python 3.11+ standard könyvtárral) mutatja be a modern, tiszta szoftverfejlesztés alapelveit, rétegeit és tipikus programozási logikáit.

> **A cél nem a leglátványosabb játék**, hanem az, hogy minden kulcsfogalom — *Domain, Contract, State, Enum, Value Object, Operator, Pure Function, Exception, Getter/Setter, Encapsulation, Recorder, DI, Catalog, Manifest, Context Manager, Mock* — önálló, 20–210 soros, beszédes nevű fájlokban legyen tanulmányozható.
>
> **Elnevezési szabályok:** A teljes fájlnév-, osztály-, függvény- és változó-elnevezési útmutatót lásd itt: **[`NAMING_CONVENTION.md`](NAMING_CONVENTION.md)**.

---

## 1. Architektúra: A 4 réteg és a Függőségi Szabály

A program a **Clean Architecture (Tiszta Architektúra)** elvét követi. A legfontosabb szabály a **Dependency Rule (Függőségi Szabály)**: a nyilak **mindig befelé** mutatnak — a belső `domain/` réteg **semmit nem tud** arról, hogy terminálban fut-e a játék, vagy hogy a pálya JSON fájlból jött-e.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  COMPOSITION ROOT:  game_cli_entrypoint.py / main.py  (Összedrótozás: DI)    │
└──────────────┬──────────────────────────────┬────────────────────────┬───────┘
               ▼                              ▼                        ▼
┌──────────────────────────────┐ ┌──────────────────────────────┐ ┌───────────────────────────┐
│  4. PRESENTATION (TUI)       │ │  3. INFRASTRUCTURE (I/O)     │ │  2. APPLICATION           │
│  - ascii_board_renderer.py   │ │  - json_room_manifest_loader │ │  - game_loop_controller.py│
│  - terminal_keyboard_adapter │ │  - system_random_adapter.py  │ │  - input_recorder_service │
└──────────────┬───────────────┘ └──────────────┬───────────────┘ └─────────────┬─────────────┘
               │                                │                               │
               └────────────────────────────────┼───────────────────────────────┘
                                                ▼
               ┌────────────────────────────────────────────────────────────┐
               │  1. DOMAIN (Tiszta szabályok: 0 UI, 0 I/O, 0 rng)          │
               │  game_enums, domain_exceptions, grid_point_value,          │
               │  fruit_catalog, snake_entity, world_state,                 │
               │  domain_contracts (Protocol), game_rules_engine            │
               └────────────────────────────────────────────────────────────┘
```

**Miért jó ez?**
- Ha holnap terminál helyett Pygame vagy webes felületet akarsz, **csak a `presentation/` mappát kell kicserélned**.
- Ha tesztelni akarod az ütközést vagy a 3 másodperces gyümölcs-spawnolást, a `domain/` **képernyő, fájlrendszer és valódi időzítő nélkül**, ezredmásodpercek alatt futtatható.

---

## 2. Hogyan kel életre egyetlen képkocka? (Adatfolyam)

Minden időlépés (**tick**) ugyanazon a tiszta körforgáson (Game Loop) megy végig:

1. **Bemenet (`presentation/terminal_keyboard_adapter.py`):** A `TerminalKeyboardAdapter.poll_keyboard_commands()` nem-blokkoló módon kiolvassa a lenyomott billentyűket (pl. `w` -> `(PlayerId.P1, Direction.UP)`).
2. **Vezérlés és naplózás (`application/game_loop_controller.py` + `input_recorder_service.py`):** A `GameLoopController.steer_player_snake()` ellenőrzi a játékos-azonosítót, elmenti az eseményt az `InputRecorderService.record_player_input()` metódussal, majd elkészíti az új irányba fordított `SnakeEntity`-t.
3. **Szabályok lefuttatása (`domain/game_rules_engine.py`):** A `GameLoopController.advance_simulation_tick(delta_seconds)` meghívja a tiszta `GameRulesEngine.compute_next_world_state(world_state, delta_seconds, random_provider)` függvényt, amely kiszámítja az **új** `WorldState` pillanatképet (mozgás, evés, ütközés, 3 mp-es gyümölcs-időzítő).
4. **Megjelenítés (`presentation/ascii_board_renderer.py`):** Az `AsciiBoardRenderer.render_board_frame(controller.current_state)` csak kiolvassa a `WorldState`-et, és ASCII karakterekké (`#`, `1`, `o`, `2`, `x`, `@`, `*`) rajzolja.

---

## 3. Programozási alapelvek és fogalomtérkép

| Fogalom / Alapelv | Hol találod? | Mit jelent a gyakorlatban? |
| :--- | :--- | :--- |
| **Elnevezési Konvenciók** | [`NAMING_CONVENTION.md`](NAMING_CONVENTION.md) | Egységes fájlnév-, osztály-, ige-első függvény- és rövidítésmentes változó-elnevezési szabályok. |
| **Manifest & Literal** | `assets/room_manifest.json` | A pálya mérete, kezdőpontjai és a 3 mp-es gyümölcsidőzítés kódmódosítás nélkül, deklaratív JSON-ból paraméterezhető. |
| **Enum** | `domain/game_enums.py` | Zárt értékkészlet (`PlayerId`, `Direction`, `GameStatus`, `FruitType`). Megelőzi a nyers stringek elgépelését (`"Up"` vs `"up"`). |
| **Domain Exception** | `domain/domain_exceptions.py` | Saját, beszédes kivétel (`InvalidRoomManifestException`). A hívó célzottan elkaphatja a pályahibát anélkül, hogy más hibát elnyelne. |
| **Value Object & Operator** | `domain/grid_point_value.py` | `GridPoint(x, y)` megváltoztathatatlan koordináta saját `+` (`__add__`) és `==` operátorral: `head_position + direction_delta`. |
| **Catalog (Data-Driven SSOT)** | `domain/fruit_catalog.py` | Központi, csak olvasható (`MappingProxyType`) gyümölcstár (`APPLE`, `GOLDEN_MELON`). Új gyümölcshöz nem kell átírni a szabálymotort. |
| **Entity, Stat, Method** | `domain/snake_entity.py` | A `SnakeEntity` osztály egyedi `player_id`-val, statisztikával (`fruits_eaten`), saját metódussal (`change_direction`) és `tuple` testtel. |
| **Immutable State (SSOT)** | `domain/world_state.py` | A teljes világ egyetlen `frozen=True` `WorldState` objektumban él. Kompozícióval (`HAS-A`) tartalmazza a két kígyót (`player_one_snake`, `player_two_snake`). |
| **Contract (Interface / DIP)** | `domain/domain_contracts.py` | `typing.Protocol` szerződések (`RoomManifestLoader`, `RandomNumberProvider`). A Domain szabja meg az elvárást, nem a külvilág! |
| **Pure Function & Predicates** | `domain/game_rules_engine.py` | `GameRulesEngine.compute_next_world_state()` és predikátumai (`is_within_room_bounds`, `has_snake_crashed`, `is_head_swap_collision`) mellékhatásmentesek. |
| **Encapsulation & Recorder** | `application/input_recorder_service.py` | Privát `_input_history` lista + csak olvasható `history` getter (`tuple`), amellyel tick-re pontosan naplózható minden meccs. |
| **Getter & Setter** | `application/game_loop_controller.py` | `@property` (kiolvasás: `current_state`, `tick_rate_hz`) és `@tick_rate_hz.setter` (validált írás: csak `1.0..60.0 Hz` engedett). |
| **Dependency Injection (DI)** | `application/game_loop_controller.py`, `game_cli_entrypoint.py` | A `GameLoopController` kívülről, konstruktorban kapja a `RandomNumberProvider`-t és az `InputRecorderService`-t — élesben valódi, tesztben mock! |
| **Deserialization & Wrapping** | `infrastructure/json_room_manifest_loader.py` | A JSON beolvasás és minden alacsony szintű hiba (`KeyError`, `JSONDecodeError`) itt alakul validált `WorldState`-té vagy domain kivétellé. |
| **Stateless Presentation** | `presentation/ascii_board_renderer.py` | A `format_board_frame() -> str` tiszta formázás el van választva a `print()`-től, így maga a kirajzolás is tesztelhető. |
| **Context Manager** | `presentation/terminal_keyboard_adapter.py` | `with TerminalKeyboardAdapter():` (`__enter__`/`__exit__`) garantálja, hogy POSIX terminálon kilépéskor mindig visszaálljon az eredeti mód. |
| **Unit Test & Mock** | `tests/test_snake_game_rules_and_engine.py` | `FakeRandomNumberProvider` mockkal determinisztikus, ezredmásodperces headless tesztek ellenőrzik a szabályokat és a sarokeseteket. |

---

## 4. Programozási logikák a motorháztető alatt

### A) Miért nem változtatjuk meg a régi objektumokat? (Immutability + `replace()`)
Ha egy függvény helyben átírná a `snake.body` listát, nehéz lenne követni, hol és mikor változott meg az állapot (és nem lehetne visszanézni az előző tick-et). Ehelyett minden objektum `frozen=True`, a módosítások pedig a `dataclasses.replace(world_state, ...)` hívással **új pillanatképet** készítenek.

### B) Több-lépéses növekedés (`pending_growth`)
A `GOLDEN_MELON` `growth_amount = 3` értékű. Ha egyszerre 3 mezőt szúrnánk be egyetlen tick-ben, azok egymáson lennének. Ehelyett `GameRulesEngine.advance_snake_body()` elteszi a növekedési tartalékot a `snake.pending_growth` mezőbe:
- Ha `total_pending_growth > 0`: elöl hozzáadjuk az új fejet, **hátul nem vágjuk le a farkat**, és 1-gyel csökkentjük a tartalékot.
- Ha `total_pending_growth == 0`: elöl új fej, hátul `body[:-1]` (a farok előrelép).

### C) Ütközésvizsgálat és a „fej-helycsere” (*head-swap / tunneling*) sarokeset
Két 1 hosszú kígyó egymással szemben haladva (`P1: (5,5) -> (6,5)` és `P2: (6,5) -> (5,5)`) pusztán az új pozíciók összevetésével **átsétálna egymáson**. A `GameRulesEngine.is_head_swap_collision(...)` tiszta predikátum kifejezetten ezt a klasszikus rácsjáték-hibát zárja ki (`GameStatus.DRAW`).

### D) Garantáltan ütközésmentes gyümölcs-elhelyezés (`free_cells`)
Egy naiv megoldás addig sorsolna véletlen `(x, y)` pontokat, amíg üreset nem talál — teli pályán ez végtelen ciklusba eshet vagy kígyóra rakhatja a gyümölcsöt. A `GameRulesEngine.select_free_fruit_position()` ehelyett:
1. Egy `set`-be gyűjti az összes foglalt mezőt (`occupied_cells = set(player_one_snake.body) | set(player_two_snake.body)` — `O(1)` keresés).
2. Kiszűri a valóban szabad belső mezőket (`free_cells`).
3. Ha `free_cells` üres, tisztán `None`-t ad vissza; különben `random_provider.next_int(len(free_cells))` indexszel választ.

### E) 180 fokos visszafordulás tiltása lookup táblával és tiszta predikátummal
Négy hosszú `if/elif` feltétel helyett a `snake_entity.py` egy deklaratív `OPPOSITE_DIRECTIONS` szótárat és az `is_opposite_direction()` predikátumot használja:
```python
if is_opposite_direction(self.direction, target_direction):
    return self
```
Így a szabály 2 soros, könnyen olvasható és alacsony komplexitású marad.

---

## 5. Gyakorlati tanulófeladatok (Próbáld ki!)

1. **Új gyümölcs hozzáadása (Data-Driven tervezés):**
   Adj hozzá egy `BERRY` (`symbol="+"`, `growth_amount=2`) elemet! Megfigyelheted, hogy **csak 2 fájlt** kell módosítanod: `domain/game_enums.py` és `domain/fruit_catalog.py` — a szabálymotor és a megjelenítő automatikusan kezelni fogja.
2. **Új pálya készítése kódírás nélkül (Manifest):**
   Hozz létre egy `assets/small_arena.json` fájlt `14x12`-es mérettel és `1.5` mp-es gyümölcsidőzítéssel, majd indítsd így:
   `$env:PYTHONPATH="src"; python main.py --manifest assets/small_arena.json`
3. **Visszajátszó (Replay) készítése:**
   Írj egy függvényt, amely a `controller.input_recorder.history` naplót és ugyanazt a `seed`-et felhasználva újra lejátssza a meccset `GameRulesEngine.compute_next_world_state()` segítségével!

---

## 6. Futtatás és tesztelés

```powershell
# Opcionális: szerkeszthető telepítés egyszer (utána elég az `ascii-duo-snake` parancs is)
# pip install -e . --no-build-isolation

# 1. Headless unit és regressziós tesztek (ezredmásodpercek alatt lefut, képernyő nélkül)
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v

# 2. Gyors, determinisztikus nem-interaktív demó
$env:PYTHONPATH="src"; python main.py --demo

# 3. Interaktív 2 fős játék (P1: WASD, P2: IJKL, Kilépés: Q)
$env:PYTHONPATH="src"; python main.py --speed 6
```

---

## 7. 4 Előadási Fázis (Git branch & tag navigáció)

A repó 4 önálló, tanítási sorrendben felépített fázisra van bontva — minden előadás külön branch-en és tag-en futtatható, a hozzá tartozó `LECTURE_GUIDE.md` útmutatóval:

| Fázis | Tag / Branch | Téma (~45–50 perc) | Változások megtekintése |
| :--- | :--- | :--- | :--- |
| **1. előadás** | `phase-1` / `phase-1-alapok` | Alapok, adattípusok (`Enum`, `GridPoint`, `WorldState`) és statikus szoba | `git checkout phase-1` |
| **2. előadás** | `phase-2` / `phase-2-egy-kigyo` | 1 kígyó irányítása (`WASD`), tiszta szabálymotor, getter/setter | `git diff phase-1 phase-2` |
| **3. előadás** | `phase-3` / `phase-3-ket-kigyo-gyumolcs` | 2. kígyó (`IJKL`), gyümölcs-katalógus, DI, Mock, `pending_growth`, `head-swap` | `git diff phase-2 phase-3` |
| **4. előadás** | `phase-4` / `phase-4-teljes-jatek` (`main`) | Állapot-ellenőrzés, JSON Manifest, `InvalidRoomManifestException`, `InputRecorderService` | `git diff phase-3 phase-4` |

```powershell
# Ugrás bármelyik előadási fázisra (pl. 2. előadás):
git checkout phase-2
# Visszatérés a teljes projektre:
git checkout main
```

---

## 8. Automatikus Promóciós Demó (`promo/`)

A `promo/` mappa egy **0 külső függőséges, adatvezérelt (Data-Driven) és élő játékmotort futtató terminál-bemutatót** tartalmaz (teljesen elkülönítve a `src/` rétegektől), amely 4 koreografált jelenetben végigvezeti a 4 előadás kulcsfogalmait:

> **Data-Driven Config (Adatvezérelt programozás) a gyakorlatban:**
> A jelenetek címei, alcímei, kiemelései, időzítései, kezdő kígyópozíciói, gyümölcsei és szkriptelt lépései **nem a Python kódban vannak beégetve**, hanem a [`promo/promo_storyboard_config.json`](promo/promo_storyboard_config.json) fájlban élnek (amelyet a `promo/promo_config_loader.py` validál és alakít valódi Domain Enumokká). Hallgatóként nyugodtan átírhatsz bármilyen címet, sebességet vagy mozgás-sorozatot a JSON-ban **Python kód módosítása nélkül**, majd elindíthatod `--config` kapcsolóval!

```powershell
# Normál, animált bemutató (előadáshoz / kivetítőre):
$env:PYTHONPATH="src"; python promo/run_promo_demo.py

# Gyors, 1–2 mp-es előnézet (CI / ellenőrzéshez, képernyőtörlés nélkül):
$env:PYTHONPATH="src"; python promo/run_promo_demo.py --fast

# Folyamatos konferencia- / kivetítő-hurok (kilépés: Ctrl+C):
$env:PYTHONPATH="src"; python promo/run_promo_demo.py --loop

# Saját, átírt JSON forgatókönyv futtatása kódmódosítás nélkül:
$env:PYTHONPATH="src"; python promo/run_promo_demo.py --config promo/promo_storyboard_config.json --fast
```
