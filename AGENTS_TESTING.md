# AGENTS_TESTING.md

Load for tests, builds, release verification, or any "is this green?" claim.

## Order
1. Targeted tests for the package.
2. Full suite: `python -m unittest discover -s tests -q`.
3. Release gate: `python -m launcher.release_gate`.
4. Project record: `python -m project_record check/build/readme`.
5. Browser check for site/graph changes (headless Chrome, DOM text).
6. Lane check for runtime changes (quick lane first, then full).

## Non-negotiables
- A green test is not acceptance.
- Do not weaken tests to make a branch pass; fix the code or mark the test branch-conditional with an expiry.
- Metadata sync changes source revision; run the gate after it, not before.
- Gate must fail closed. Escaped Windows paths, UNC, mixed separators, and placeholder paths need fixtures.
- Browser-only claims require a real DOM check, not just `node --check`.
- Runtime evidence needs sealed bundle, manifest, and revision; if absent, report UNKNOWN.
- If a merged branch reds the suite, revert to the last green tag before further work.

## Test classes
- Unit/integration offline tests.
- Launcher plan/config safety tests.
- Telemetry parser/summary fixtures.
- Runtime lane JSON (join, heartbeats, adaptive, crash, screenshots; hits UNKNOWN).
- Site/graph DOM accessibility check.

## Common failure record
Mass-merging all branches produced 102 errors because function signatures/constants conflicted. The fix is package-by-package integration plus full-suite green at every merge.
