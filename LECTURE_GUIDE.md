# 4. Előadás — Állapot-ellenőrzés, Manifest, Recorder és Teljes Architektúra (~45 perc)

**Git fázis:** `phase-4` (`phase-4-teljes-jatek`, `main`)  
**Változások a 3. előadáshoz képest:** `git diff phase-3 phase-4`

## Cél
A játékot robusztus, élesben is bővíthető alkalmazássá fejezzük be: külső JSON pályaleíróval (Manifest), szigorú invariáns-ellenőrzéssel, saját domain kivétellel, visszajátszható bemenet-rögzítővel és tiszta Composition Root összedrótozással.

## Tanított fogalmak (~45 perc)
1. **Manifest & Deserialization (10 perc):** `assets/room_manifest.json` és a `RoomManifestLoader` szerződés (`domain_contracts.py`) + `JsonRoomManifestLoader` (`infrastructure/json_room_manifest_loader.py`).
2. **Domain Exception & Exception Wrapping (10 perc):** `InvalidRoomManifestException` (`domain_exceptions.py`) — az alacsony szintű `OSError`, `JSONDecodeError`, `KeyError`, `TypeError` hibák becsomagolása és a pályainvariánsok ellenőrzése (falon lévő spawn, ütköző kezdőpont, érvénytelen méret/időzítés).
3. **Encapsulation & Recorder (`InputRecorderService`) (10 perc):** Privát `_input_history` + csak olvasható `history` getter (`tuple[RecordedInput, ...]`), valamint a `GameLoopController.steer_player_snake()` biztonsági sorrendje (érvénytelen `player_id` -> `ValueError` rögzítés ELŐTT).
4. **Composition Root & Elnevezési Konvenciók (15 perc):** `game_cli_entrypoint.py` teljes DI összedrótozása (`--demo`, `--speed`, `--manifest`), [`NAMING_CONVENTION.md`](NAMING_CONVENTION.md) áttekintése, valamint az automatikus promóciós demó (`promo/run_promo_demo.py`).

## Élő demó parancsok
```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
$env:PYTHONPATH="src"; python main.py --demo
$env:PYTHONPATH="src"; python main.py --speed 6
$env:PYTHONPATH="src"; python promo/run_promo_demo.py --fast
```
