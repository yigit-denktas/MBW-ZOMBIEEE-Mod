# Agent B: offline Windows bootstrap

Spec: GitHub issues #8 and #9, plus `progress/agent-allocation.json` on
`project-record-setup-v041`. Base: main `048564a` (v0.1.8).

Implement natively in this branch. No CI, game assets, executable execution,
installer writes, firewall changes or acceptance claims. Agent A retains README,
build integration and the final session contract; Agent C retains diagnostics.

1. Add `launcher/discovery.py` and `tests/test_windows_discovery.py`.
   `discover(steam_roots, custom_paths, known_roots)` returns JSON-compatible
   candidates, provenance, unknown versions, ambiguity and blockers. Read Steam
   library/app manifests and bounded local WSE2 layouts; validate PE headers
   without executing files. Tests first: spaces, multiple/legacy libraries,
   corrupt manifests, missing/invalid EXEs, nested WSE2, duplicate paths,
   inaccessible paths and a no-write snapshot.
2. Add `installer/manifest.py` and `tests/test_windows_manifest.py`.
   `plan_install(game_root, archive, transaction_id)` produces a dry-run JSON
   manifest, argv for the existing builder and same-volume stage/backup paths.
   Tests first: no destination writes, existing install backup, unsafe paths,
   missing inputs. Document the journal/rename/recovery strategy; execution
   remains gated, including repair/update/uninstall.
3. Add `launcher/solo.py` and `tests/test_windows_solo.py`.
   Pure state machine emits lifecycle actions; a fake harness tests recorder,
   host, readiness, client, shutdown, failure, timeout and retry. Both listen
   and dedicated routes remain simulations. Restrict endpoint to loopback,
   City `tbfc_invasion_4`, mission `multiplayer_iv`. No invented engine flags.
4. Write `docs/WINDOWS_BOOTSTRAP.md` and `handoffs/AGENT_B.md` with CLI,
   schema, build/recorder interface proposals, evidence and remaining gates.
   Run all local unittest tests, check the diff, commit and open a draft PR.

Review focus: stale manifests never imply a found game; PE presence never
proves ownership/version/runtime compatibility; junctions cannot escape bounded
search; no-write discovery/planning; cleanup retains failed processes until
exit confirmation and prevents retry while an old process remains.

No release ledger leaves become accepted from these offline tests.
