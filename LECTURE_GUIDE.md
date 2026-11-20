# 3. Előadás — Második kígyó, véletlengenerálás, gyümölcsök és növekedés (~50 perc)

**Git fázis:** `phase-3` (`phase-3-ket-kigyo-gyumolcs`)  
**Változások a 2. előadáshoz képest:** `git diff phase-2 phase-3`

## Cél
Az egyjátékos kígyót valódi 2 fős (`WASD` + `IJKL`) játékká bővítjük: bevezetjük a gyümölcs-katalógust, a determinisztikusan tesztelhető véletlengenerálást, a több-lépéses növekedést és a két kígyó közötti ütközésvizsgálatot.

## Tanított fogalmak (~50 perc)
1. **Második kígyó & Head-Swap sarokeset (10 perc):** `player_two_snake` kompozíció (`WorldState`), `IJKL` billentyűzet-kiosztás (`TerminalKeyboardAdapter`), és az `is_head_swap_collision()` predikátum, amely megakadályozza, hogy két szemből érkező kígyó átsétáljon egymáson (`GameStatus.DRAW`).
2. **Data-Driven Catalog (`FRUIT_CATALOG`) (8 perc):** `FruitType` enum + `MappingProxyType` katalógus (`APPLE` `+1`, `GOLDEN_MELON` `+3`) a `domain/fruit_catalog.py` fájlban.
3. **Contract (`Protocol`), Dependency Injection & Mock (12 perc):** `RandomNumberProvider` szerződés (`domain_contracts.py`), valódi `SystemRandomAdapter` (`infrastructure/`), és `FakeRandomNumberProvider` mock a determinisztikus tesztekhez.
4. **Több-lépéses növekedés (`pending_growth`) (10 perc):** `GameRulesEngine.advance_snake_body()` — a `GOLDEN_MELON` `+3` növekedése 3 egymást követő tick alatt, faroklevágás kihagyásával valósul meg.
5. **Ütközésmentes spawn (`free_cells`) (10 perc):** `select_free_fruit_position()` `set`-alapú `O(1)` foglaltság-szűréssel — sosem tesz gyümölcsöt kígyóra, teli pályán tisztán `None`-t ad vissza.

## Élő demó parancsok
```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
$env:PYTHONPATH="src"; python main.py --demo
$env:PYTHONPATH="src"; python main.py --speed 6   # P1: WASD, P2: IJKL, Kilépés: Q
```
