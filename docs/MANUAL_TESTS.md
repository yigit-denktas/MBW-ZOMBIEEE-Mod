# Manual engine acceptance tests (Windows; no CI)

Before diagnosing engine failure, run the **archival integrity** and **static preflight** checks separately. The extracted source archive is not distributed in this public repository.

```powershell
7z t "C:\Downloads\ZOMBIEEEBeta04.rar"
py -3 -m unittest discover -s tests -v
py -3 tools\build.py --archive "C:\Downloads\ZOMBIEEEBeta04.rar" --out "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster"
py -3 tools\doctor.py --module "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster"
py -3 tools\preflight.py --module "C:\Games\MountBlade Warband\Modules\ZOMBIEEE_Remaster" --json
```

Expect compiled invasion `mst_multiplayer_iv`: **64 entry points / 25 original triggers**, and **30/30 mod BRF resources**. A passing preflight does *not* prove sound/texture CRC integrity or engine runtime compatibility.

Next, use the *WSE2 1.1.5.4* Windows launcher with module `ZOMBIEEE_Remaster`. Preserve a copy of `rgl_log.txt`, WSE2 version and screenshot. Look for lines:

```text
[ZOMBIEEE Remaster 0.1.1] Lua bootstrap loaded
[ZOMBIEEE Remaster 0.1.1] compiled invasion trigger count: 25
[ZOMBIEEE Remaster 0.1.1] mission entry probe registered: ...
[ZOMBIEEE Remaster 0.1.1] invasion mission entered; template=...
```

The additional runtime trigger may make the WSE2-reported count **26** on some log timings. The count printed by the bootstrap runs before registering the probe.

| Test | Pass criteria |
|---|---|
| RAR archive | 7-Zip reports integrity OK without skipped or damaged entries |
| Fresh module | Build completes, doctor passes, preflight passes |
| Runtime startup | WSE2 launches with no fatal resource/parser error |
| Invasion | City `tbfc_invasion_4`, `multiplayer_iv`, complete one zombie wave |
| Survivor equipment | All four classes load and fire/reload |
| Interactions | Ammo, health boxes, explosive props work |
| Original bots | Record player/zombie bot side and actual behaviour |
| All five maps | Granny's House, Bridge, Shipyard, City, Abandoned Town |
| Stability | Ten successive waves and latency/frame-time readings |

No runtime rows have been independently verified. No public hosting or cheat controls until server authority is checked.
