# End-of-development diagnostic recorder (v0.1.3)

**No step-by-step game testing required.** Continue development and local static verification normally. After the final build is ready, play one private WSE2 session, exit the game, and run the collector once. It packages evidence for later analysis rather than making you troubleshoot each intermediate build.

## What is recorded

- Versioned ZDB1 events written by the Lua overlay to WSE2's existing engine log: startup, compiled trigger count, hook registration, invasion mission entry, host/client role, total agent count when supported, and a heartbeat every 15 seconds (maximum 480). The probe is read-only.
- Up to 25 existing engine logs from WSE2/Warband game and Documents folders, plus explicitly supplied custom logs. Last 8 MiB per log; source filenames, modification times and truncation are recorded.
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
| R014 | Wrong trigger count (25 original, 26 with experimental defenders) |
| R015 | Logs older than seven days, potentially unrelated |
| R016 | WSE2 Lua diagnostic hook failed to register |

**Conservative interpretation:** errors are evidence; an error-free report is inconclusive, not proof that zombies, friendly bots, waves, weapons, or multiplayer work. Final gameplay verification is still required once the implementation is complete.

Local tests: python -m unittest discover -s tests -v. No CI. Original Beta 0.4 only; ZOMBIEEE2 excluded.
