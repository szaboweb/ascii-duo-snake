# 1. Előadás — Alapok, Adattípusok és Statikus Szoba (`phase-1`)

> **Időtartam:** ~45 perc  
> **Git branch / tag:** `phase-1-alapok` / `phase-1`  
> **Cél:** Felépíteni a játék tiszta adatmodelljét (`domain/`) és kirajzolni egyetlen statikus szobát 1 kígyóval (`presentation/`), még mozgás, billentyűzet és véletlenszám nélkül.

---

## 1. Óravázlat és időbeosztás (~45 perc)

| Idősáv | Téma | Érintett fájl |
| :--- | :--- | :--- |
| **00–05 perc** | Miért választjuk szét az adatot (`domain/`) és a kirajzolást (`presentation/`)? | `src/ascii_duo_snake/` szerkezet |
| **05–13 perc** | Zárt értékkészletek: `Enum` nyers stringek helyett (`PlayerId`, `Direction`, `GameStatus`) | `domain/game_enums.py` |
| **13–22 perc** | Value Object, Immutability (`frozen=True`) és `+` operátor túlterhelése (`__add__`) | `domain/grid_point_value.py` |
| **22–30 perc** | Entity vs. Value Object, `tuple` test és csak olvasható `@property` getterek (`head`, `length`) | `domain/snake_entity.py` |
| **30–36 perc** | Single Source of Truth (`WorldState`) és Kompozíció (*HAS-A* kapcsolat) | `domain/world_state.py` |
| **36–42 perc** | Állapotmentes ASCII megjelenítő: `format_board_frame() -> str` vs. `print()` | `presentation/ascii_board_renderer.py` |
| **42–45 perc** | Belépési pont (`game_cli_entrypoint.py`) és első 3 headless unit teszt lefuttatása | `tests/test_snake_game_rules_and_engine.py` |

---

## 2. Kulcsfogalmak az előadáshoz

1. **Enum (`game_enums.py`):** Megakadályozza a csendes elgépeléseket (`"Up"` vs. `"up"`). A típusellenőrző és az IDE azonnal segít.
2. **Value Object & Operator (`grid_point_value.py`):** A `GridPoint(x, y)` megváltoztathatatlan (`frozen=True`), érték szerint egyenlő (`==`), és a `__add__` operátorral olvashatóan összeadható: `GridPoint(5, 7) + GridPoint(1, -2)`.
3. **Entity & Read-Only Getter (`snake_entity.py`):** A `SnakeEntity` rendelkezik azonosítóval (`player_id`) és `@property` getterekkel (`head`, `length`). A `body` mező szándékosan `tuple`, nem `list`, hogy kívülről ne lehessen módosítani.
4. **SSOT & Kompozíció (`world_state.py`):** A `WorldState` az egyetlen igazságforrás — tartalmazza a szoba méretét és a `player_one_snake` objektumot.
5. **Tesztelhető megjelenítés (`ascii_board_renderer.py`):** A `format_board_frame(world_state)` tiszta stringet ad vissza, így képernyő nélkül is ellenőrizhető unit teszttel.

---

## 3. Futtatás és ellenőrzés órán

```powershell
# 1. Statikus szoba kirajzolása (1 képkocka)
python main.py

# 2. Headless unit tesztek futtatása
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
```

---

## 4. Következő lépés (2. előadás)

A következő fázisban (`git checkout phase-2`) életre keltjük a kígyót: jön a `WASD` irányítás, a 180 fokos visszafordulás tiltása, a fal-/önütközés és a validált `@tick_rate_hz.setter`.
