# 2. Előadás — Egy kígyó folyamatos mozgása és irányítása (~50 perc)

**Git fázis:** `phase-2` (`phase-2-egy-kigyo`)  
**Változások az 1. előadáshoz képest:** `git diff phase-1 phase-2`

## Cél
Az 1. előadás statikus modelljét életre keltjük: 1 kígyó folyamatosan halad, `WASD`-vel irányítható, nem tud 180°-ban önmagába fordulni, és falba ütközve véget ér a játék.

## Tanított fogalmak (~50 perc)
1. **Deklaratív lookup táblák (10 perc):** `OPPOSITE_DIRECTIONS` (`snake_entity.py`) és `DIRECTION_DELTAS` (`game_rules_engine.py`) hosszú `if/elif` láncok helyett.
2. **Pure Function (10 perc):** `GameRulesEngine.compute_next_world_state()` — régi `WorldState` → új `WorldState` (0 `print`, 0 mellékhatás).
3. **Application réteg + Getter & Setter (15 perc):** `GameLoopController` (`@property current_state`, `@property tick_rate_hz` + `@tick_rate_hz.setter` 1..60 Hz validációval).
4. **Context Manager & Game Loop (15 perc):** `with TerminalKeyboardAdapter():` (`__enter__`/`__exit__`) és a klasszikus `Input → Update → Render → Sleep` ciklus.

## Élő demó parancsok
```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
$env:PYTHONPATH="src"; python main.py --demo
$env:PYTHONPATH="src"; python main.py --speed 6   # P1: WASD, Kilépés: Q
```
