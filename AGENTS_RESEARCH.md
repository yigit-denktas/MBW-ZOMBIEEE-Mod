# AGENTS_RESEARCH.md — engine / combat-AI research book

Load this file only for engine, AI, combat-AI, formation, orders, stance, or cross-engine research tasks. Combat implementation guidance lives in [`AGENTS_AI_COMBAT.md`](AGENTS_AI_COMBAT.md); testing lives in [`AGENTS_TESTING.md`](AGENTS_TESTING.md). Project authority remains [`AGENTS.md`](AGENTS.md).

**Status:** research guidance, not acceptance evidence. This file does not authorize code, builds, installs, game launches, publication or acceptance. Research deliverables are docs; runtime claims need a sealed D bundle and fixed-reviewer PASS.

## Scope

- **In scope:** Warband/WSE2 engine behavior, mission triggers, orders/divisions, AI limits, Bannerlord comparison, community/technical sources, feasibility translation for A/C/D task owners.
- **Out of scope:** implementing triggers/tools, installing builds, telemetry collection, asset/licence clearance, release metadata, ledger acceptance. Route those to the owning role.
- **Rule:** builders do not review each other. H submits docs to `review-b2` or `E`; the author never self-approves.

## Procedures

1. **Intake.** Read `AGENTS.md`, this file, `docs/REVIEW_POLICY.md`, and the prior research docs that touch the question. State the research question and the non-claims in the first paragraph.
2. **Collect sources.** Build a source table before writing findings: URL or repo path, source tier, exact version/commit or capture date, what it proves, and its limits. Record inaccessible sources (403/paywall/Cloudflare) instead of pretending they were read.
3. **Evidence per claim.** Separate *fact* (source-attributed), *design proposal* (ours), and *unverified* (not established). Never let an inference inherit the authority of its source.
4. **Draft.** Use the section spine: status/non-claims → source table → findings → feasibility tags → handoff/experiments. Keep op names and short signatures; never paste engine code or assets.
5. **Review handoff.** Submit doc path + branch/SHA + source list + known gaps to a fixed reviewer (`review-b2` or `E`). Reviewer status is PASS/BLOCKED/UNKNOWN; UNKNOWN is not PASS. Patch only the findings the reviewer requires.
6. **Close.** Report paths, SHA, review status and residual UNKNOWNs to Lead. No acceptance language in the doc or the report.

## Assumptions (verify before relying on them)

1. **Declarations are not semantics.** A header comment or API name proves a signature, not how the engine interprets the value.
2. **`add_visitors_to_current_scene`'s 5th argument in MP is the leader/owner player id**, not a formation group. Passing 5..7 is a type error; `0`/`-1` sentinel semantics are unverified. Read the Native MP call site, not only the header.
3. **`agent_get_group` is not a division** in the MP path; it is leader/owner identity. Division adoption and order reach remain unproven; orders address class/division 0..9.
4. **No public target setter / focus-fire API** in the reviewed surface. "Assist", "priority" and "focus" are responsibilities/placement, not enforceable targeting.
5. **No faction-specific AI.** Rhodok-like behavior is emergent from troop data + composition-based tactic + hold/formation orders; do not invent hidden routines.
6. **Community sources drift.** Native-derived mirrors, wikis, threads and mod files have dates, versions and edits. Pin a commit/capture; treat line-level facts as source-attributed.
7. **Licence boundary.** Do not copy engine/game code, assets or decompiled logic; cite facts and API names only.

## Evidence and gates

| Source tier | Use | Gate |
| --- | --- | --- |
| Official publisher docs / generated API | Public contract/surface facts | URL + version + observed date |
| Public module-system headers | Opcode ids, signatures, constants | Repo + commit; signature only |
| Native-derived module source (community mirror) | Call sites, scripted behavior, argument use | Repo + commit + file:line; note mirror lineage |
| Community analysis/wiki/forum | Design precedent, player/engine observations | URL + date/capture; label community, not engine proof |
| Mod source/README (Bannerlord/Warband) | How others implement class/formation/target logic | Repo + commit/date; no code import |
| Our sealed project evidence | What our build actually did | Bundle + revision; D owns the seal |

**Gates before handoff:** source table exists; each claim has a tier and a label; versions/commits/dates pinned; no copied code/assets; feasibility tags present; fixed-reviewer PASS; `runtime_verified=false`/`acceptance=none` preserved.

## Common failures (with the fix)

1. **Header vs call site.** The `add_visitors_to_current_scene` header names `<group_no>`; the Native MP path passes a **leader/owner player id**. A build locked the false invariant and passed 5..7; review-b2 found it live. Fix: cite the call site and state the operand domain.
2. **Unverified sentinel.** `-1`, `0`, `9`, "no leader" and similar values get treated as facts. Fix: leave them **unverified** until observed; write "unverified" in the claim, not only the footnote.
3. **External citation accuracy.** URLs move, dates are wrong, a thread is cited through another doc, Wayback captures differ. Fix: re-fetch or explicitly say "second-hand"; record the capture date and the inaccessible source.
4. **Getter convention echo.** `agent_get_group` returned the agent id as the group (26/28/29/31; later 8..15 aggregates; latest seal `-1`). Fix: verify a getter's calling convention against a known value before drawing semantics.
5. **Version drift.** 2015 headers vs 1.174, Bannerlord v1.3.14 vs v1.4.7 pages, mod source forks. Fix: pin version/commit and note which build the claim applies to.
6. **Copied code/assets.** Pasting script bodies, decompiled logic, textures or data. Fix: cite file:line and paraphrase; link-only for community code.
7. **Acceptance language.** "works", "proven", "fixed" in a research doc. Fix: use PASS/FAIL/UNKNOWN for observations and "design proposal" for recommendations.

## Handoff / review

Hand off: doc path(s) + branch/SHA; research question; source table summary; claims still UNKNOWN; review status; no install/build/launch request. Review is by `review-b2` or `E` only; builders do not evaluate peers and do not self-approve. Reviewer result is PASS/BLOCKED/UNKNOWN with exact evidence. Lead owns merge/integration; merge is not acceptance.

## File map

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | project authority and role routing |
| `AGENTS_RESEARCH.md` | this research book |
| `AGENTS_AI_COMBAT.md` | combat implementation/evidence guidance |
| `docs/REVIEW_POLICY.md` | fixed reviewers and PASS/BLOCKED/UNKNOWN rules |
| `.agents/skills/writing-skills/SKILL.md` | required process for creating/editing skills |
| `.agents/skills/engine-source-citation/SKILL.md` | source-citation discipline skill |
| `reference/WARBAND_ENGINE_AI_RESEARCH.md` | Warband engine/order/trigger/AI limits |
| `reference/BANNERLORD_AI_ENGINE_RESEARCH.md` | Bannerlord engine/formation-AI comparison |
| `reference/SURVIVOR_CLASS_MATRIX.md` | class matrix and feasibility tags |
| `reference/RHODOK_CROSSBOW_STANCE_RESEARCH.md` | stance/screen/assist/post/swarm research |
| `reference/WARBAND_AI_MODDING.md`, `WARBAND_AI_COMMUNITY_SOURCES.md` | Warband AI community source pack |
| `reference/CITY_*.md`, `CITY_MAP_DEFENSE_DESIGN.md` | City-specific static/design evidence |
| `docs/ENGINE.md`, `docs/DIAGNOSTICS.md`, `docs/COMBAT_BALANCE.md` | engine/runtime/build context |
| `handoffs/` | lane handoffs and session contracts |
| `local/session/` | private sealed evidence (not public) |
| `progress/ledger.json`, `progress/live-status.json` | tracking state (research does not edit) |

## Checklist

- [ ] Research question and non-claims stated
- [ ] Source table with tiers, versions/commits and dates
- [ ] Call-site evidence for behavior claims (not header names)
- [ ] Sentinels/getter conventions marked verified or unverified
- [ ] Feasibility tags applied (F-now / F-build / B-engine / B-unproven)
- [ ] No code/assets/decompiled logic copied; no acceptance language
- [ ] Submitted to review-b2 or E; PASS/BLOCKED/UNKNOWN recorded
- [ ] Paths/SHA/residual UNKNOWNs reported to Lead
