# City readiness evidence: server and scene provenance gate

Agent A · 2026-10-24 · **static diagnostics correction**, not an observed WSE2 bug or gameplay fix.

## Source defect

Previous `tools/evidence_readiness.py::matrix_for_session` used:
- `types["mission_enter"] > 0` to report `invasion_mission_entered=observed`, even when the only marker belonged to a *client*, lacked a role or named a different mission.
- `server role` heartbeat without checking `template` before accepting team-1 zombie counts or two distinct `wave` values as invasion observations.
- No separately declared server-side **City scene** status. A mission template being loaded says nothing about which invasion map was selected.

This is a **false-positive evidence-classification risk**. It was discovered by reviewing current source during the wait for B's owner-authorized integrated boot, not diagnosed from a boot log. It could make an otherwise unsuccessful server-join attempt appear to satisfy some release checklist cells.

## Implemented A-only changes

1. Accept server-side invasion-entry **only** from an explicit `role=server` and `template=multiplayer_iv` or `mst_multiplayer_iv` marker. The WSE2 Lua getter can have either naming convention. Client/unknown role and foreign mission remain unknown.
2. Add independent `city_scene_observed`, accepted only for an explicit **server invasion mission-entry** marker whose `scene` is `tbfc_invasion_4` or `scn_tbfc_invasion_4`. This field is not currently in every older C/engine probe; **absence must remain `unknown`**, not evidence the map was wrong. A new City-scene status cannot be promoted from source/build intent.
3. Only accept zombie team-1 and wave marker counts from `role=server` **and a matching invasion `template`** heartbeat. Numeric fields with malformed values, bools or missing role are ignored.
4. Retain separate, narrow `engine_boot_event` status: a log's Lua boot marker may be client-only, so a Lua marker **does not prove the dedicated host booted**.
5. Keep existing combat, fallback and command sample interpretation unchanged; none establishes full playability by itself. A self-contained event list has no cryptographic engine-origin attestation—verification still needs B's owned process/socket identity and C's independent evidence review.

This is **not** a new requirement that B manufacture a `scene` marker. It is a conservative distinction: a missing scene measurement simply leaves that gate for direct runtime/manual observation.

## Executed evidence

Owned Beta 0.4 original RAR/module present locally. Linux Python 3.13.5.

```
python -m unittest discover -s tests -p 'test_evidence_readiness.py' -v
Ran 10 tests — OK

ZOMBIEEE_ORIGINAL_MODULE=<owned module> \
ZOMBIEEE_ORIGINAL_ARCHIVE=<owned archive> \
python -m unittest discover -s tests -q
Ran 149 tests — OK (0 failures, 0 skips)
```

Five new negative/positive test cases explicitly exercise client-only entry, unrelated server mission/heartbeat, server mission but missing City-scene getter, direct server City observation and malformed/unknown role data. The other previous 144 original-source tests remained passing. Original game assets, original 25 native triggers, remaster gameplay, B launcher and C HMAC/recorder wire are untouched.

## Next live-evidence interpretation

The owner-approved B attempt announced on PR #11 selected **older A `2643321`** and **older C `53c2f88`**. At the time of this source correction, B **has posted no completed actual boot result**. Do not transfer observations from that candidate to the current A revision, claim a successful private bind from a config, or infer that a client `mission_enter` proves a server-side City session. A's updated readiness classifier can be run later against privately verified event data once available. The [14-gate City release ledger](../docs/INTEGRATED_CITY_ACCEPTANCE_2026-10-24.md) remains authoritative.

No new user gameplay session is requested by this source-only correction.
