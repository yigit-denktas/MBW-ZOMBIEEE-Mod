# Development handoff

Remote: https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod (user-selected, **public**).
Main branch. Original archive/Warband executables excluded.

1. Verify 7-Zip integrity of the supplied `ZOMBIEEEBeta04.rar` on Windows, then run local installer and `doctor.py`.
2. Install WSE2 1.1.5.4 and attempt mission startup, City survival wave and weapons; save logs.
3. If load fails, classify exact resource/table/parser failure and make small reversible fixes.
4. Map `mst_multiplayer_iv` triggers plus troop team assignment; reconstruct only necessary logic.
5. Add server-authoritative allied defenders and map hold/rally locations, then admin cheats.
6. Update SemVer and CHANGELOG **only after demonstrable milestones**.

No CI. Run local Python unit tests and manual engine checks. No ZOMBIEEE2 assets or code. Do not claim runtime playability before a Windows game session.
