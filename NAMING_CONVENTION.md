# Elnevezési Konvenciók (`NAMING_CONVENTION.md`)

> **Alapszabály:** Minden fájlnév, osztálynév, függvénynév és változónév **első pillantásra elárulja a pontos szerepét** — kommentek és találgatás nélkül.

Ez a dokumentum rögzíti az `ascii_duo_snake` repó teljes, Clean Architecture alapú elnevezési szabályrendszerét, konkrét példákkal a kódbázisból.

---

## 1. Fájlnevek (`snake_case` + szerep/réteg utótag)

A fájlnév ne általános gyűjtőnév legyen (`utils.py`, `helpers.py`, `rules.py`), hanem konkrétan nevezze meg a tartalmát és architekturális szerepét:

| Réteg | Szabály / Minta | Konkrét fájlok a repóban |
| :--- | :--- | :--- |
| **Domain** | `<fogalom>_<szerep>.py` | `game_enums.py`, `domain_exceptions.py`, `grid_point_value.py`, `fruit_catalog.py`, `snake_entity.py`, `world_state.py`, `domain_contracts.py`, `game_rules_engine.py` |
| **Application** | `<feladat>_<service\|controller>.py` | `input_recorder_service.py`, `game_loop_controller.py` |
| **Infrastructure** | `<technologia>_<szerep>_<loader\|adapter>.py` | `json_room_manifest_loader.py`, `system_random_adapter.py` |
| **Presentation** | `<felulet>_<szerep>_<renderer\|adapter>.py` | `ascii_board_renderer.py`, `terminal_keyboard_adapter.py` |
| **Composition Root** | `<terulet>_cli_entrypoint.py` | `game_cli_entrypoint.py` |
| **Tesztek** | `test_<tesztelt_terulet>.py` | `test_snake_game_rules_and_engine.py` |

---

## 2. Osztálynevek (`PascalCase` + szerep utótag)

Az osztálynév utótagja jelzi az architekturális mintát (Pattern):

| Szerep / Minta | Utótag | Példák a repóból |
| :--- | :--- | :--- |
| **Enum** | *(nincs kötelező utótag)* | `PlayerId`, `Direction`, `GameStatus`, `FruitType` |
| **Value Object / Spec** | `*Point`, `*Spec`, `*Record` | `GridPoint`, `FruitSpec`, `InputRecord` |
| **Entity** | `*Entity` | `SnakeEntity` |
| **Immutable State (SSOT)** | `*State` | `WorldState` |
| **Domain Exception** | `*Exception` | `InvalidRoomManifestException` |
| **Contract (Protocol)** | `*Loader`, `*Provider` | `RoomManifestLoader`, `RandomNumberProvider` |
| **Stateless Rules Engine** | `*Engine` | `GameRulesEngine` |
| **Application Service / Controller** | `*Service`, `*Controller` | `InputRecorderService`, `GameLoopController` |
| **Infrastructure Implementation** | `*Loader`, `*Adapter` | `JsonRoomManifestLoader`, `SystemRandomAdapter` |
| **Presentation Component** | `*Renderer`, `*Adapter` | `AsciiBoardRenderer`, `TerminalKeyboardAdapter` |
| **Teszt Mock** | `Fake*` | `FakeRandomNumberProvider` |

---

## 3. Függvények és metódusok (`snake_case`, ige-első szándék szerint)

A metódus kezdőigéje azonnal elárulja, hogy **tiszta lekérdezésről**, **tiszta számításról** vagy **állapotmódosító/I/O műveletről** van-e szó:

### A) Tiszta predikátumok (`is_`, `has_`, `can_`) — 0 mellékhatás, mindig `bool`
- `is_within_room_bounds(cell_position, room_width, room_height)`
- `has_snake_crashed(head_position, own_snake, opponent_snake, room_width, room_height)`
- `is_head_swap_collision(player_one_next_head, player_two_next_head, ...)`
- `is_opposite_direction(current_direction, target_direction)`

### B) Tiszta számítások és építők (`compute_`, `advance_`, `select_`, `format_`, `build_`) — 0 mellékhatás
- `compute_next_world_state(world_state, delta_seconds, random_provider) -> WorldState`
- `advance_snake_body(snake, next_head_position, eaten_growth_amount) -> SnakeEntity`
- `select_free_fruit_position(room_width, room_height, player_one_snake, player_two_snake, random_provider) -> GridPoint | None`
- `format_board_frame(world_state) -> str`
- `build_default_manifest_path() -> Path`

### C) Parancsok és I/O akciók (`steer_`, `advance_`, `record_`, `render_`, `poll_`, `load_`, `run_`)
- `steer_player_snake(player_id, target_direction)`
- `advance_simulation_tick(delta_seconds)`
- `record_player_input(tick, player_id, target_direction)`
- `render_board_frame(world_state, clear_screen=True)`
- `poll_keyboard_commands()`
- `load_initial_world_state(manifest_path)`
- `run_demo_session(controller, board_renderer, step_count=12)`
- `run_interactive_session(controller, board_renderer)`

---

## 4. Változók és paraméterek (`snake_case`, ZÉRÓ rejtélyes rövidítés)

A rövidítések spórolnak 5 karaktert íráskor, de órákat rabolnak olvasáskor. Minden paraméter és lokális változó teljes, egyértelmű angol szavakból áll (mértékegységgel, ahol releváns, pl. `_seconds`, `_hz`):

| Kerülendő rövidítés | Kötelező beszédes név | Hol használjuk? |
| :--- | :--- | :--- |
| `dt` | `delta_seconds` | `GameRulesEngine`, `GameLoopController`, `game_cli_entrypoint` |
| `rng` | `random_provider` | `GameRulesEngine`, `GameLoopController`, tesztek |
| `p1`, `p2` | `player_one_snake`, `player_two_snake` | `WorldState`, `GameRulesEngine`, `AsciiBoardRenderer` |
| `p1_next`, `p2_next` | `player_one_next_head`, `player_two_next_head` | `GameRulesEngine` |
| `new_dir` | `target_direction` | `SnakeEntity`, `GameLoopController`, `InputRecorderService` |
| `pos` | `cell_position` / `spawn_position` | `GameRulesEngine`, `JsonRoomManifestLoader`, `AsciiBoardRenderer` |
| `w`, `h` | `room_width`, `room_height` | `WorldState`, `GameRulesEngine`, `JsonRoomManifestLoader` |
| `ch` | `pressed_character` | `TerminalKeyboardAdapter` |
| `fd` | `stdin_file_descriptor` | `TerminalKeyboardAdapter` |
| `exc` | `json_error` / `schema_error` | `JsonRoomManifestLoader` |
| `val` | `selected_value` | `FakeRandomNumberProvider` |

---

## 5. Konstansok (`UPPER_SNAKE_CASE`)

A modulszintű, futásidőben megváltoztathatatlan (`MappingProxyType` / `tuple`) konstansok mindig `UPPER_SNAKE_CASE` formátumúak:

- `FRUIT_CATALOG` (`domain/fruit_catalog.py`)
- `OPPOSITE_DIRECTIONS` (`domain/snake_entity.py`)
- `DIRECTION_DELTAS` (`domain/game_rules_engine.py`)
- `AVAILABLE_FRUIT_TYPES` (`domain/game_rules_engine.py`)
- `KEYBOARD_BINDINGS` (`presentation/terminal_keyboard_adapter.py`)

---

## 6. Privát tagok (`_` előtag) és `@property` Getter/Setter szabály

- **Privát példányváltozók:** egyetlen aláhúzással (`_`) kezdődnek, és kívülről közvetlenül nem módosíthatók:
  - `_world_state`, `_random_provider`, `_tick_rate_hz` (`GameLoopController`)
  - `_input_history` (`InputRecorderService`)
  - `_random_generator` (`SystemRandomAdapter`)
  - `_stdin_file_descriptor`, `_saved_terminal_settings` (`TerminalKeyboardAdapter`)
- **Publikus olvasási felület (`@property`):** főnév-alapú, tiszta getterek (`head`, `length`, `current_state`, `tick_rate_hz`, `history`), validált módosításnál a hozzá tartozó `@<nev>.setter` párral (`@tick_rate_hz.setter`).
