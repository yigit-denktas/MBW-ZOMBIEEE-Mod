# AGENTS.md — ZOMBIEEE Remaster

Read this file once per session. Then load **only** the role file that matches your assignment. Do not preload every role file; that is context clutter.

## Core rules (everyone)

1. `main` is the only code branch; `gh-pages` is publication-only. One package branch at a time, deleted after integration.
2. Work in small packages: **target → tests → build → review → integrate**. No mass merges.
3. Builders do not review peers or self-approve. Fixed reviewers: `review-b2` and `E`. Merge only after reviewer sign-off.
4. Never claim acceptance. `runtime_verified=false` and `acceptance=none` stay until an owner accepts evidence.
5. Evidence beats narrative: revision, command, artifact, result, gap. UNKNOWN is not PASS.
6. Raw gameplay captures stay private. Public output is derived-only unless owner + legal clearance.
7. Before deleting any branch/worktree, freeze it as an `archive/` tag and record it in `archive/`.
8. When creating or editing a skill, read `.agents/skills/writing-skills/SKILL.md` first.
9. Project tracking is required; see [`AGENTS_TRACKER.md`](AGENTS_TRACKER.md). Small fixes get cards too.

## Role routing

| Assignment | Read only |
|---|---|
| Lead / coordinator / operator | [`AGENTS_LEAD.md`](AGENTS_LEAD.md) + [`AGENTS_TESTING.md`](AGENTS_TESTING.md) + [`AGENTS_TRACKER.md`](AGENTS_TRACKER.md) |
| AI, combat, orders, stance, fire behavior | [`AGENTS_AI_COMBAT.md`](AGENTS_AI_COMBAT.md) |
| Probe, telemetry, summaries, evidence analysis | [`AGENTS_TELEMETRY.md`](AGENTS_TELEMETRY.md) |
| Runtime harness, game installs, sealed runs, lanes | [`AGENTS_RUNTIME.md`](AGENTS_RUNTIME.md) |
| Launcher, installer, release gate, Pages publishing | [`AGENTS_RELEASE.md`](AGENTS_RELEASE.md) |
| Assets, licences, cosmetics, icons, reticles | [`AGENTS_ASSETS.md`](AGENTS_ASSETS.md) + [`AGENTS_ENVIRONMENT.md`](AGENTS_ENVIRONMENT.md) |
| Environment/world/map design | [`AGENTS_ENVIRONMENT.md`](AGENTS_ENVIRONMENT.md) |
| Engine/combat-AI research and citations | [`AGENTS_RESEARCH.md`](AGENTS_RESEARCH.md) |
| Legal, IP, claims, licence clearance | [`AGENTS_LEGAL.md`](AGENTS_LEGAL.md) |
| Independent review / acceptance gate | [`AGENTS_REVIEW.md`](AGENTS_REVIEW.md) |
| Tests, builds, checks, release verification | [`AGENTS_TESTING.md`](AGENTS_TESTING.md) |

If your task crosses two domains, read the second file only for that task, then unload.

## Shared failure memory

The paid-for lessons live in domain files and in `.agents/skills/*-*/SKILL.md`. Before repeating a known class of work, read the matching skill. Do not rediscover the same failure.

## Project-record core

The authoritative tracker is `progress/ledger.json`; projections are derived. Preserve snapshots, keep stable IDs, distinguish done from accepted, and record scope changes. Full procedure: [`AGENTS_TRACKER.md`](AGENTS_TRACKER.md). The installed project-record block is preserved there.
