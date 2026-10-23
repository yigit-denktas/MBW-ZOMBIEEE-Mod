# SemVer and development plan

## Version contract

Historical source: ZOMBIEEE Beta **0.4** (2012). This does not determine remaster versions.

- **0.1.x:** repository, guarded installer, archive static doctor, diagnostic Lua bootstrap; not playable.
- **0.1.4:** Experimental City navmesh-derived guard posts, three isolated defender groups and compiled hold orders (runtime unverified).
- **0.1.5:** Opt-in five-map navmesh guard positions, server-only scene-scoped orders, and original-wave-driven survivor reinforcement (static verification only).
- **0.1.6:** Experimental native fall-back/regroup with hysteresis, state-aware wave diagnostics and guarded movement samples (offline validated only).
- **0.1.7:** AI-only differentiated original-asset loadouts, wave-based class rotation and gated solo-host assist, static verified only.
- **0.1.8:** Opt-in auditable private host commands, survivor-support difficulty and forensic combat/evidence matrix (offline prototype, WSE2 unverified).
- **0.2.0:** WSE2 startup + original City wave and weapons smoke-tested.
- **0.3.0:** allied survivor bots, survivor faction and class/loadout verified.
- **0.4.0:** authored City defence points, hold/rally/fallback orders, navigation tests.
- **0.5.0:** private-admin cheats and solo quality-of-life options.
- **0.6.0:** five original maps, measured stability and performance optimisation.
- **0.7.0:** local/Tailscale co-op with friends.
- **1.0.0:** repeatable playable solo/friends release and redistribution clearance.

Patch versions are bug fixes. New milestone versions are awarded only after acceptance evidence, not after creating placeholder source.

## Working order

1. Validate original RAR with 7-Zip; extract to a separate module directory and preserve input.
2. Launch under WSE2 1.1.5.4; examine parse errors, missing BRF/resources and Lua startup.
3. Start `multiplayer_iv` in City (`tbfc_invasion_4`); verify wave, weapons, supplies and round transitions.
4. Map original bot behaviour. Introduce server-authoritative **allied** bots, defend positions and class assignment without disrupting hostile zombies.
5. Add configurable defence/rally/supply positions with navmesh + LOS checks, regroup and retreat.
6. Add local/private-host admin controls (god mode, ammo, currency, ally spawn, wave controls), disabled for normal clients.
7. Profile mission triggers, WSE2 FPS/frame pacing, spawns and server simulation time; change only demonstrated bottlenecks.
8. Test Granny's House, Bridge, Shipyard, City, Abandoned Town; then LAN/Tailscale co-op.

No CI, no original assets in Git, no ZOMBIEEE2 dependency, no Bannerlord migration.

## Proposed next baseline (review only; not an adopted milestone update)

A separate Project Record Standard setup branch carries [the scoped proposal](../progress/overview.md) and [24 outcome leaves](../progress/ledger.json). It adds source-grounded zero-configuration Windows setup, external diagnostics and one-click solo hosting before an approved release, without retroactively changing the SemVer or completed status of the historical milestones above. Do not count compiled-script prototypes as passed gameplay gates. Owner approval and the pinned toolkit verification are still pending.
