# End-of-development diagnostic recorder (v0.1.8)

**No step-by-step game testing required.** Continue development and local static verification normally. After the final build is ready, play one private WSE2 session, exit the game, and run the collector once. It packages evidence for later analysis rather than making you troubleshoot each intermediate build.

## What is recorded

- Versioned ZDB1 events written by the Lua overlay to WSE2's existing engine log: startup, compiled trigger count, hook registration, invasion mission entry, host/client role, total agent count and optional survivor team-0 / zombie team-1 counts when WSE2 exposes the team getter, and a heartbeat every 15 seconds (maximum 480). The probe is read-only.
- Up to 25 existing engine logs from WSE2/Warband game and Documents folders, plus explicitly supplied custom logs. Up to 8 MiB per log: on larger logs, the first 256 KiB and final ~7.75 MiB are retained with an explicit truncation marker, preserving startup and crash context. Source filenames and modification times are recorded.
- OS version/architecture, Python version, remaster version, source archive SHA-256, WSE2 target, experimental defender count, and installed module file SHA-256 hashes (without distributing mod assets).
- Session metadata, extracted events.jsonl, SHA-256 manifest, and integrity verification that rejects altered ZIP entries.
- Best-effort redaction of credentials, email addresses, IP addresses, Steam IDs and user-home paths. No unredacted logs, memory dumps or automatic uploads.

**Privacy limitation:** player names, chat, unusual identifiers and sensitive scene names might survive. Inspect the ZIP before sharing. Raw logs remain on your computer and evidence bundles are never uploaded automatically.

## One command, only at the end

After installing the game and final remaster, close Warband and run from the repository root on Windows:

    .\tools\Collect-Diagnostics.ps1 -WarbandRoot 'C:\Program Files (x86)\Steam\steamapps\common\MountBlade Warband' -Session final-solo

Produces timestamped local files under evidence/: ZOMBIEEE-evidence-*.zip and ZOMBIEEE-report-*.md. It does not launch Warband, install CI or send data over the network. If WSE2 uses an unusual log location, add -AdditionalLogs @('C:\path\to\custom.log').

For subsequent investigations, all offline:

    py -3 tools\diagnostics.py verify .\evidence\some-evidence.zip
    py -3 tools\diagnostics.py analyze .\evidence\some-evidence.zip --report .\evidence\report.md
    py -3 tools\diagnostics.py compare .\evidence\first.zip .\evidence\second.zip

Pass comparison ZIP paths explicitly, in chronological order. Comparison reports recurring, new and resolved error codes across builds.

## Analyzer rule catalogue

| Code | Meaning |
| --- | --- |
| R001 | Missing BRF/resource; inspect archive CRC and referenced assets |
| R002 | Fatal exception or crash; inspect nearby native log lines |
| R003 | Compiled script/operation error |
| R004 | WSE2 Lua failure |
| R005 | Missing texture, sound or other media |
| R010 | No logs to diagnose |
| R011 | Lua bootstrap event absent |
| R012 | No invasion entry despite bootstrap event |
| R013 | Mission entered but heartbeat absent |
| R014 | Wrong trigger count (25 original, 26 with defenders, 27 with tactical positions, 29 with wave reinforcements, 31 with recovery) |
| R015 | Logs older than seven days, potentially unrelated |
| R016 | WSE2 Lua diagnostic hook failed to register |
| R017 | Installed module manifest missing; cannot correlate build and runtime |
| R018 | Experimental allied team absent across sampled server frames while zombies exist |

**Conservative interpretation:** errors are evidence; an error-free report is inconclusive, not proof that zombies, friendly bots, waves, weapons, or multiplayer work. Final gameplay verification is still required once the implementation is complete.

Local tests: python -m unittest discover -s tests -v. No CI. Original Beta 0.4 only; ZOMBIEEE2 excluded.

## Team-count limitations

The mission probe uses WSE2's documented agent iterator. If the optional native team getter is unavailable, team0/team1 are reported as -1, **not zero**. The analyzer records team-data availability and never diagnoses missing allies from unavailable metrics. When at least two server-side samples show team 0 empty while team 1 is populated, it flags a *candidate* ally-spawn issue (R018), not a proven cause. Bot combat competence, navigation and wave victory still require the final game session.

The guarded installer also stores `archive_crc_verified`, `original_mission_trigger_count` and `final_trigger_count`. The evidence pack includes only allowlisted build metadata plus SHA-256 hashes of installed module files, so a later report can distinguish an unknown archive from a modified installation. None of the mod assets are included.

## Scene overlay receipt

The v0.1.4 installer records `final_trigger_count=27` if `--city-guardposts` is active. Original City data still has 226 objects; a patched copy has 229. The existing module fingerprint captures the modified `mission_templates.txt`, while the unmodified original archive remains untouched. Read the [City defence overlay](CITY_DEFENSE.md) for source-derived entry coordinates and offline checks.

## v0.1.5 build provenance

The collector fingerprints `variables.txt` (including the optional reinforcement sentinel) and all five original `SceneObj/scn_tbfc_invasion_*.sco` scene files in addition to the compiled mission, troop data, and Lua bootstrap. It does **not** package original game assets. The actual `final_trigger_count` is recorded by the installer for 25/26/27/29 variants. At final runtime test, compare the installed build fingerprint with that manifest before assuming the wrong code is running.

## v0.1.8 tactical and movement observability

The recorder now tries to read wave_number, g_round_ended, zdr_last_reinforced_wave and zdr_defence_mode from WSE2's documented game.gvar interface. If a global is missing, it records -1: not available. It emits a bounded heartbeat every 15 seconds, plus wave_change and tactical_change events.

Optional agent_sample records only reserved AI survivor divisions (5–7), when WSE2 exposes the necessary operation getter functions: agent ID, group, current tactical mode and rounded game-world X/Y. It records at most 16 bots per heartbeat. **This position function may be unavailable without WSE2 Module System headers**; missing samples are reported as unknown, not as a false stuck-agent diagnosis.

New analyzer rules: R019 candidate stalled wave (>=9 heartbeats on one wave while zombies remain), R020 rapid fallback/regroup oscillation, R021 apparent failure to regroup despite healthy-looking team-0 counts, R022 unusually stationary defenders *after* a tactical state change. These are conservative heuristics, never proof of causality. Static hold-position behaviour without a new order should not generate R022.

The full experimental build receipt records final_trigger_count=31 plus the tactical low/high thresholds. Original assets, executable and the RAR are still excluded from Git and from diagnostic bundles. [Tactical recovery design](TACTICAL_RECOVERY.md).

## v0.1.8 native command and AI combat forensics

A locally authored minimal `overlay/lua/msfiles/header_operations.py` maps only read-only Warband native getters that our WSE2 Lua telemetry uses. The runtime attempts `combat_sample` (agent/group/wave/known weapon ID/ammo/kill count) and `command_exec` events from native command counter increments, up to 16 non-player reserved-group defenders every 15 seconds. No real player coordinates or names are required. Unavailable native operations are recorded as unknown.

New offline codes: **R023** candidate ammunition depletion, **R024** prolonged engagement with no observed defender kill increments, **R025** hotkey execution inconsistent with build receipt, **R026** missing AI combat observability. The final JSON and Markdown reports include an **acceptance evidence matrix** for engine startup, mission entry, zombie waves, allied agents, combat activity, fallback/regroup and private commands. Unknown does not mean failed or passed. An error-free log is not proof of playability. [Full forensic reference](FORENSIC_DIAGNOSTICS.md).


## Agent C: external flight recorder (development prototype)

**Status: offline prototype on `agent/c-flight-recorder`; Windows/WSE2 integration not verified.** The recorder runs as a separate Python process, observes a subprocess launched with `--` or a pre-existing PID with `--observe-pid`, and independently stores atomic, bounded evidence snapshots. No game memory injection, shell execution, external telemetry or background uploads. It does not replace the final WSE2 session.

Run from the repository root. The following commands use a **fake Python game**, not an actual Warband invocation:

~~~powershell
py -3 -m unittest discover -s tests -p 'test_flight_*.py' -v
py -3 -m telemetry.flight_recorder --output-root .\evidence\flight --session fake-city --timeout 10 -- py -3 -c "import sys; sys.exit(7)"
py -3 tools\diagnostics.py collect --flight-root .\evidence\flight\fake-city --output .\evidence\fake-city.zip --session fake-city
py -3 tools\diagnostics.py verify .\evidence\fake-city.zip
py -3 tools\diagnostics.py analyze .\evidence\fake-city.zip --report .\evidence\fake-city.md
~~~

A real integrated session should pass existing WSE2/Warband log paths using repeated `--log` arguments. For Agent B's future launcher, pass its **optional** private per-user `zombieee.session.v1` JSON receipt with `--launcher-receipt`; only allowlisted fields are reproduced. This is an interface prototype, **not** a claim that automatic City launch or WSE2 flags work.

- **Recorder storage:** `evidence/flight/<session_id>/recorder.json`, `events.jsonl`, redacted `logs/log_XX.txt` and `manifest.json`, atomically written with SHA-256 digests over the actual redacted bytes.
- **Collection:** `diagnostics.py collect --flight-root <completed-session-dir> ...` verifies all recorder entries first, refuses a modified source, then carries the scrubbed snapshots plus their process receipt into the existing self-checked evidence ZIP.
- **Log window:** the recorder starts at the log files' current end (not historical prior-session text), polls without modifying the game, stores at most 12 logs × 2 MiB each, limits event records to 2,048 and records truncation. A very long burst may omit the crash tail: this limitation must be resolved before declaring crash coverage production-grade.
- **Process evidence:** owned-child exit codes are observed; a merely watched PID has **unknown** exit code. Timeout and startup failure are recorded separately. Per-process CPU, memory and FPS are **unknown**, not fake values; wall-clock duration is measured.
- **Privacy:** common credentials, home paths, IPs, email addresses and Steam IDs are redacted best-effort. `verify` additionally reports counts for *potential* remaining sensitive strings, never the offending values. It **always requires manual privacy review before any ZIP is shared**, even when all automated counts are zero. SHA-256 verifies accidental modifications, not provenance or proof that logs are safe.
- **Forensic leads:** R027 means external recorder timed out; R028 means an owned child exited nonzero. Neither is an automatic verdict of a Warband crash. Actual WSE2 Lua and game-run acceptance checks retain the `unknown` state until observed.

Run the full offline suite with `py -3 -m unittest discover -s tests -v` before review. These test files do not require original mod or WSE2 assets, and there is **no CI**.

## Agent integration boundary

Agent B owns launcher and installer orchestration. Agent C owns this recorder and evidence processing, consumes B's optional local JSON session receipt without storing full paths, PIDs, command lines, chat or credentials in report outputs. Agent A owns the [provisional session contract](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/blob/agent/a-city-engine/handoffs/SESSION_CONTRACT.md) on its branch and must review any schema change. Only Agent A can declare a final WSE2 City result accepted based on objective runtime evidence, not these offline fixtures.
