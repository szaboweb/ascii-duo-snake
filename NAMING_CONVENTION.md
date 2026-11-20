# Elnevezési Konvenciók (`NAMING_CONVENTION.md`)

> **Alapszabály:** Minden fájlnév, osztálynév, függvénynév és változónév **első pillantásra elárulja a pontos szerepét** — kommentek és találgatás nélkül.

Ez a dokumentum rögzíti az `ascii_duo_snake` repó teljes (1–8. fázisú), Clean Architecture alapú elnevezési szabályrendszerét, valós példákkal a kódbázisból.

---

## 1. Fájlnevek (`snake_case` + szerep/réteg utótag)

A fájlnév ne általános gyűjtőnév legyen (`utils.py`, `helpers.py`, `rules.py`), hanem konkrétan nevezze meg a tartalmát és architekturális szerepét:

| Réteg | Szabály / Minta | Konkrét fájlok a repóban |
| :--- | :--- | :--- |
| **Domain** | `<fogalom>_<szerep>.py` | `game_enums.py`, `domain_exceptions.py`, `grid_point_value.py`, `fruit_catalog.py`, `snake_entity.py`, `world_state.py`, `domain_contracts.py`, `game_rules_engine.py`, `session_state_machine.py`, `bot_steering_strategy.py`, `game_events.py` |
| **Application** | `<feladat>_<service\|controller\|bus>.py` | `input_recorder_service.py`, `game_loop_controller.py`, `game_event_bus.py`, `deterministic_replay_service.py` |
| **Infrastructure** | `<technologia>_<szerep>_<loader\|adapter>.py` | `json_room_manifest_loader.py`, `system_random_adapter.py` |
| **Presentation** | `<felulet>_<szerep>_<renderer\|catalog\|adapter>.py` | `ascii_board_renderer.py`, `board_theme_catalog.py`, `retro_arcade_sound_adapter.py`, `terminal_keyboard_adapter.py` |
| **Composition Root** | `<terulet>_cli_entrypoint.py` | `game_cli_entrypoint.py` |
| **Promo (`promo/`)** | `promo_<szerep>.py` / `run_promo_<cel>.py` | `promo_config_loader.py`, `promo_storyboard.py`, `run_promo_demo.py` |
| **Tesztek (`tests/`)** | `test_<tesztelt_terulet>.py` | `test_snake_game_rules_and_engine.py`, `test_promo_config_loader.py`, `test_advanced_phases_and_invariants.py` |

---

## 2. Osztálynevek (`PascalCase` + szerep utótag)

Az osztálynév utótagja jelzi az architekturális mintát (Pattern):

| Szerep / Minta | Utótag | Példák a repóból |
| :--- | :--- | :--- |
| **Enum** | *(nincs kötelező utótag)* | `PlayerId`, `Direction`, `GameStatus`, `FruitType`, `SessionPhase` |
| **Value Object / Spec / Event / Snapshot** | `*Point`, `*Spec`, `*Record`, `*Event`, `*Snapshot` | `GridPoint`, `FruitSpec`, `BoardThemeSpec`, `InputRecord`, `FruitEatenEvent`, `MatchEndedEvent`, `MatchReplaySnapshot` |
| **Entity** | `*Entity` | `SnakeEntity` |
| **Immutable State (SSOT)** | `*State` | `WorldState` |
| **Domain Exception** | `*Exception` | `InvalidRoomManifestException`, `InvalidPhaseTransitionException` |
| **Contract (Protocol)** | `*Loader`, `*Provider`, `*Strategy` | `RoomManifestLoader`, `RandomNumberProvider`, `BotSteeringStrategy` |
| **State Machine & Strategy** | `*StateMachine`, `*Strategy` | `SessionStateMachine`, `GreedyFruitBotStrategy`, `CautiousSurvivalBotStrategy` |
| **Stateless Rules Engine** | `*Engine` | `GameRulesEngine` |
| **Application Service / Controller / Bus / Collector** | `*Service`, `*Controller`, `*Bus`, `*Collector` | `InputRecorderService`, `GameLoopController`, `GameEventBus`, `MatchTelemetryCollector`, `DeterministicReplayService` |
| **Infrastructure Implementation** | `*Loader`, `*Adapter` | `JsonRoomManifestLoader`, `SystemRandomAdapter` |
| **Presentation Component** | `*Renderer`, `*Adapter` | `AsciiBoardRenderer`, `TerminalKeyboardAdapter`, `RetroArcadeSoundAdapter` |
| **Teszt Mock** | `Fake*` | `FakeRandomNumberProvider` |

---

## 3. Függvények és metódusok (`snake_case`, ige-első szándék szerint)

A metódus kezdőigéje azonnal elárulja, hogy **tiszta lekérdezésről**, **tiszta számításról** vagy **állapotmódosító/I/O műveletről** van-e szó:

### A) Tiszta predikátumok (`is_`, `has_`, `can_`) — 0 mellékhatás, mindig `bool`
- `is_within_room_bounds(cell_position, room_width, room_height)`
- `has_snake_crashed(head_position, own_snake, opponent_snake, room_width, room_height)`
- `is_head_swap_collision(player_one_next_head, player_two_next_head, ...)`
- `is_opposite_direction(current_direction, target_direction)`
- `can_transition_to(target_phase)`
- `is_cell_safe_for_bot(target_point, world_state)`

### B) Tiszta számítások, generátorok, kiválasztók és szerializálók (`compute_`, `advance_`, `select_`, `detect_`, `iter_`, `format_`, `build_`, `parse_`, `serialize_`, `deserialize_`) — 0 mellékhatás
- `compute_next_world_state(world_state, delta_seconds, random_provider) -> WorldState`
- `compute_manhattan_distance(first_point, second_point) -> int`
- `advance_snake_body(snake, next_head_position, eaten_growth_amount) -> SnakeEntity`
- `select_free_fruit_position(room_width, room_height, player_one_snake, player_two_snake, random_provider) -> GridPoint | None`
- `select_board_theme(theme_id) -> BoardThemeSpec`
- `select_bot_strategy(strategy_id) -> BotSteeringStrategy`
- `detect_transition_events(previous_state, next_state) -> tuple[GameDomainEvent, ...]`
- `iter_replay_states(initial_world_state, snapshot, random_provider_factory) -> Iterator[WorldState]`
- `format_board_frame(world_state) -> str`
- `build_default_manifest_path() -> Path`
- `parse_manifest_text(raw_json_text) -> WorldState`
- `serialize_replay_to_json(snapshot) -> str`
- `deserialize_replay_from_json(raw_json) -> MatchReplaySnapshot`

### C) Parancsok, állapotátmenetek és I/O akciók (`steer_`, `advance_`, `transition_`, `subscribe_`, `publish_`, `on_`, `replay_`, `play_`, `record_`, `render_`, `poll_`, `load_`, `run_`)
- `steer_player_snake(player_id, target_direction)`
- `advance_simulation_tick(delta_seconds)`
- `transition_to(target_phase)`
- `subscribe_listener(listener)`
- `publish_event(event)`
- `on_domain_event(event)`
- `replay_match_deterministically(initial_world_state, snapshot, random_provider_factory)`
- `play_tone(frequency_hz, duration_ms)`
- `record_player_input(tick, player_id, target_direction)`
- `render_board_frame(world_state, clear_screen=True)`
- `poll_keyboard_commands()`
- `load_initial_world_state(manifest_path)`
- `run_demo_session(controller, board_renderer, step_count=12, player_two_bot_strategy=None)`
- `run_interactive_session(controller, board_renderer, player_two_bot_strategy=None)`

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
- `DIRECTION_DELTAS`, `AVAILABLE_FRUIT_TYPES` (`domain/game_rules_engine.py`)
- `ALLOWED_PHASE_TRANSITIONS` (`domain/session_state_machine.py`)
- `CANDIDATE_DIRECTIONS`, `BOT_STRATEGY_CATALOG` (`domain/bot_steering_strategy.py`)
- `DEFAULT_BOARD_THEME`, `BOARD_THEME_CATALOG` (`presentation/board_theme_catalog.py`)
- `FRUIT_SOUND_MELODIES`, `MATCH_ENDED_MELODY`, `SCENE_TRANSITION_MELODY`, `STEP_TICK_TONE` (`presentation/retro_arcade_sound_adapter.py`)
- `KEYBOARD_BINDINGS` (`presentation/terminal_keyboard_adapter.py`)

---

## 6. Privát tagok (`_` előtag) és `@property` Getter/Setter szabály

- **Privát példányváltozók:** egyetlen aláhúzással (`_`) kezdődnek, és kívülről közvetlenül nem módosíthatók:
  - `_world_state`, `_random_provider`, `_tick_rate_hz` (`GameLoopController`)
  - `_input_history` (`InputRecorderService`)
  - `_current_phase`, `_transition_history` (`SessionStateMachine`)
  - `_listeners`, `_published_events` (`GameEventBus`)
  - `_fruits_by_player`, `_unlocked_badges`, `_final_status` (`MatchTelemetryCollector`)
  - `_enabled`, `_tone_emitter` (`RetroArcadeSoundAdapter`)
  - `_random_generator` (`SystemRandomAdapter`)
  - `_stdin_file_descriptor`, `_saved_terminal_settings` (`TerminalKeyboardAdapter`)
- **Publikus olvasási felület (`@property`):** főnév-alapú, tiszta getterek (`head`, `length`, `current_state`, `tick_rate_hz`, `history`, `current_phase`, `transition_history`, `published_events`, `unlocked_badges`, `enabled`), validált módosításnál a hozzá tartozó `@<nev>.setter` párral (`@tick_rate_hz.setter`).
