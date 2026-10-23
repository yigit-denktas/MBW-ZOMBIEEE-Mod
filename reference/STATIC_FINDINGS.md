# Source archive findings — Beta 0.4 (static, unverified in engine)

**Inspected:** `ZOMBIEEEBeta04.rar` (2012). SHA-256: `9be100ff41ce6f8ebadd4aa27377f70f402883fab271999a8cab8cc1da001d1e`. This document captures static archive observations, **not** gameplay results.

## Inventory

- 1,086 archive entries (1,068 regular files), 167,493,071 compressed bytes, approximately 375,675,811 uncompressed bytes.
- 32 BRF resource files, 287 DDS textures, 541 SCO files, 42 text tables; also audio and translations.
- Compiled Warband tables: 50 mission templates, 571 scripts, 981 troops, 684 item entries, 560 scene records, 1,085 scene-prop records.
- No original `module_*.py` Python Module System source in the archive.
- Mission ID: `mst_multiplayer_iv` (`multiplayer_iv`); 64 entry-point declarations and 25 trigger blocks. One 0.05-second trigger is worth profiling, **not** proven slow.
- BRF resources referenced by `module.ini`: 30, all found by the static inspection. The archive decoder reported errors on 99 members, mainly textures; re-test with 7-Zip.

## Invasion maps

| ID | Display name | Scene file size | Confidence |
|---|---|---:|---|
| `tbfc_invasion_1` | Granny's House | 385,119 B | nontrivial scene, untested |
| `tbfc_invasion_2` | Bridge | 98,575 B | nontrivial scene, untested |
| `tbfc_invasion_3` | Shipyard | 532,339 B | nontrivial scene, untested |
| `tbfc_invasion_4` | City | 115,408 B | nontrivial scene, untested |
| `tbfc_invasion_5` | Abandoned Town | 366,573 B | nontrivial scene, untested |
| `tbfc_invasion_6` | placeholder | 1,337 B | incomplete |
| `tbfc_invasion_7`–`9` | incomplete | missing | no scene files |

## Classes and zombie troops

- Survivor classes: Commando (`trp_swadian_crossbowman_multiplayer`), Sniper (`trp_swadian_sniper_multiplayer`), Lumberjack (`trp_swadian_infantry_multiplayer`), Scout (`trp_swadian_man_at_arms_multiplayer`).
- `trp_invader1_multiplayer_ai` through `trp_invader8_multiplayer_ai`: Zombie, Tough, Fast, Cop, Steroid, Mutated, Witchy and a second Mutated definition.
- Existing bot-management scripts and a survivor AI troop reference are present. **No successful allied defender gameplay has been established.**

## Firearms and props

23 modern weapon records, including Glock 22, SIG P229, M500 Magnum, USP, Browning Cynergy, Mossberg 500/930, Remington 700, M14, Barrett M82, M249, FAMAS, AK-47, SCAR-L, MP5/MP5K/MP7, P90, Mk12 SPR, M16A2 and Uzi. Props include barricades, exploding barrels, medical supplies, buildings and modern vehicles.

These observations justify a reconstruction approach, not a wholesale remake. Test the original gameplay before editing the compiled mission logic. **Never substitute ZOMBIEEE2 content.**
