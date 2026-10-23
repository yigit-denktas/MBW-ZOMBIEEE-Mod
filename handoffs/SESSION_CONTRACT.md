# Agent integration contract — ZOMBIEEE City-first v0

**Owner:** Agent A. **Status:** provisional interface; no runtime compatibility claim. **Baseline:** `main@048564a526de9b36abd55874271c7b80f36e5cf5`. Agent B and Agent C consume this contract but must not edit this file on their branches without proposing a change to Agent A.

## Data flow

```text
Agent B: discover Warband + WSE2 + original 0.4 archive (READ ONLY)
    -> Agent A: tools/build.py --archive <owned RAR> --out <new module dir> [explicit opt-in flags]
    -> Agent B: launch private City host and client (after engine route is observed)
    -> Agent C: independent flight recorder watches process and WSE2/game logs
    -> Agent C: tools/diagnostics.py collect/verify/analyze
    -> Agent A: source-provenance and game/AI root-cause analysis
```

## Existing implementation interfaces (read first, do not reinterpret as verified)

- Original archive identity CLI (Agent A): `python -3 tools/archive_audit.py --archive <RAR> --json`. This verifies RAR4 magic, historical size, SHA-256 without extraction. Append `--verify-crc` to run 7-Zip `t` for all members; `identity_ok:true` with `crc_status:not_checked` is **not** a validated extraction. It reports no raw Windows paths. Agent B should consume this instead of creating a duplicate archive verifier.
- Builder: `python -3 tools/build.py --archive <archive.rar> --out <WarbandRoot>/Modules/ZOMBIEEE_Remaster`. Pass explicit experimental flags only after artifact checks; the default preserves 25 original invasion triggers. `tools/build.py` owns RAR identity/CRC and staging; wrap via subprocess rather than reimplement.
- Static checks: `python -3 tools/doctor.py --module <module>`, `python -3 tools/preflight.py --module <module> --json`. Neither establishes playable WSE2 gameplay.
- Installed receipt: `Modules/ZOMBIEEE_Remaster/ZOMBIEEE_REMASTER.json`. It includes exact source archive digest and `runtime_verified:false`. The launcher may read it; must not flip the flag based on static success.
- City-first experimental build: `--experimental-defenders 4 --city-guardposts --wave-reinforcements --tactical-recovery` is now accepted by the builder without `--all-map-defenses`. Initial spawns, wave top-ups and tactical fallback all contain City scene conditions. Receipt field `experimental_map_scope` is `city-only` (legacy full-map build retains `all-original-maps`). Agent B must preserve those flags for private City launch; Agent C should include the map scope and original session scene name in diagnosis.
- Original City scene: `tbfc_invasion_4`, invasion mission `multiplayer_iv`, internal `mst_multiplayer_iv`. Verify correct CLI/config tokens on a real WSE2 host before automatic launch.
- Existing diagnostic CLI: `python -3 tools/diagnostics.py collect --game-root <WarbandRoot> --module <ModuleDir> --output <unique.zip> --session <identifier>`, then `verify <zip>`, `analyze <zip> --report <out.md>`. Agent C owns this program.
- Existing Lua events: line prefix `ZDB1|event|key=value|...` with `version`; Agent C owns `overlay/lua/main.lua`. Missing operations must remain unknown, not `0`.

## Proposed local session receipt for B -> C (not public telemetry)

File location: a new per-user local directory chosen by launcher; **not** inside Git and never uploaded automatically. JSON envelope:

```json
{
  "schema": "zombieee.session.v1",
  "session_id": "solo-20261023-example",
  "mode": "private-local-city",
  "city": "tbfc_invasion_4",
  "mission": "multiplayer_iv",
  "build_manifest_sha256": null,
  "wse2_version": null,
  "start_utc": null,
  "end_utc": null,
  "host_pid": null,
  "client_pid": null,
  "host_exit_code": null,
  "outcome": "unknown",
  "evidence_bundle": null
}
```

`null` means **not observed**. Do not put user account names, chat, IP addresses, tokens, absolute installation paths, unredacted logs, or the original RAR in a public artifact. Private implementation may retain a protected local path field only where necessary to launch processes. `outcome` remains `unknown` until logged evidence and user review support a claim. Exit codes must be actual, never invented. Agent C may extend the schema by additive, versioned fields after consulting Agent B.

## File ownership / anti-collision

- **A** owns `tools/build.py`, compiled-game patches, engine/static integrity tooling and `docs/ENGINE.md`.
- **B** owns `launcher/**`, `installer/**`, Windows discovery fixtures and launcher docs; may invoke but not edit A's builder or C's logger.
- **C** owns `telemetry/**`, `tools/diagnostics.py`, `overlay/lua/**`, telemetry rules and their tests; may consume launcher receipt but not edit B's code or A's builder.
- Only Agent A edits `progress/**` and `gh-pages` after source review. Each agent commits to its own `agent/{a,b,c}-*` branch, opens a draft PR against `main`, and reports deterministic local test commands and outcomes. No CI.

## Integration order

1. **G0 offline:** A builds source archive/mission preflight checks; B publishes mock-tested discovery+dry-run; C proves external recorder survives a simulated crash and redacts private data. These may proceed in parallel.
2. **G1 engine:** A verifies original WSE2 City startup/wave on licensed game under one planned integrated Windows run. B's real host CLI and C's game-specific collectors are gated until that evidence.
3. **G2 solo release:** B's private one-click City launch, A's survivor/zombie gameplay, C's forensic evidence and all licensing/rollback gates are proven, then owner accepts the release.

**Never** require repeated user playtests for each change. Accumulate offline unit and fixture evidence; reserve real gameplay verification for the consolidated final candidate. Static tests are not engine evidence.

## Authoritative recorder lifecycle v1

Agent A has chosen **B-owned game children with C's passive pre-launched recorder**, not simultaneous startup or C launching a second game process. The canonical marker schema is `zombieee.recorder-ready.v1` (hyphen); B must verify the recorder's live owned process handle, session/attempt/start identities and durable log offsets before launching any engine child. Afterward, B sends locally authenticated HMAC attach/stop controls; C captures bounded crash evidence and stops after B's game children exit. Full message sequence, security requirements and negative tests: [RECORDER_LIFECYCLE_V1.md](RECORDER_LIFECYCLE_V1.md). This interface is **offline provisional**; actual WSE2 private binding, engine readiness, City join and game launch are not verified.

Agent A's read-only City static checker: `python -3 tools/city_acceptance.py --original <owned original Beta 0.4 module> --module <new City-only module> --json`. Reports only source/scene/native trigger structural acceptance; it does not claim a successful Warband/WSE2 launch. Agent B should require a positive check before offering Play Solo, but must not mark runtime game compatibility from it.
