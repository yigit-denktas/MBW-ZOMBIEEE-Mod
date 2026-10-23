# ZOMBIEEE Remaster — project overview (review draft)

**Purpose.** Make original 2012 ZOMBIEEE Beta 0.4 playable as a **one-click private solo** experience on Windows 11 using the user's licensed Mount & Blade: Warband and compatible WSE2. Restore City first (four other maps deferred), zombie waves, firearms and friendly survivor AI. Deliver a local diagnostic flight recorder and a safe repairable installation.

**Evidence as of 2026-10-23.** Repository v0.1.8 at [048564a526de9b36abd55874271c7b80f36e5cf5](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/tree/048564a526de9b36abd55874271c7b80f36e5cf5) includes experimental compiled mission patches, Lua telemetry, Python analyzers and manual CLI build instructions. None has been demonstrated in WSE2 running actual gameplay. The project has six open issues, no open PRs, one branch `main` observed before this review branch, no GitHub release and no published Pages/website. The proposed tracker is therefore **0/23 accepted required work leaves** and **0/5 accepted milestones**; these are *pending final-outcome criteria*, not source-code completion.

**Intended users/outcome.** Primary: a single local player who double-clicks a desktop launcher and joins a private wave mission with bot allies, without manually managing a server. Later: optional private friends play, explicitly **deferred** outside required solo baseline.

**Scope proposed for owner review.** Five work packages: tracking and evidence; runtime + diagnostic baseline; Windows installer and automatic local host; survivor AI/combat/wave/maps/performance; final integrated QA/legal release. All 24 retained accounting leaves: 23 required for initial City release and one optional deferred map expansion have one primary milestone. The 2012 source archive and third-party binaries are never published as part of this record kit. Public multiplayer, cloud telemetry, co-op, and a separate web presence are deferred.

**Acceptance authority.** Owner approves scope, gameplay gates, redistribution decisions and releases. GitHub issues own discussion and assignments. This proposed ledger owns scoped leaf criteria once accepted; generated README, tracker and percentages remain read-only views. Work already in the repo is **not** retroactively accepted from a commit or test count.

**Readiness, not completion.** Provisional current readiness: **L0** (clean Windows bootstrap not demonstrated); suggested target **L2** for reviewable agent work, **L3** before claiming engine-verifiable feature readiness, both pending owner selection. Task limits: R0 read/draft, R1 reversible review-branch changes, R2 ordinary behavior in review PR with owner merge, R3 security/installer trust by explicit approval, R4 privileged/destructive work proposal only. These do not grant extra merge or deployment authority. Detailed private assessment: `ZOMBIEEE_project_readiness_private_2026-10-23.json`, pending owner-designated central assessment store; only this non-sensitive reference is public.

**Open decisions.** (1) Exact release boundary for solo v1.0 versus optional co-op; (2) accepted success gate and test duration; (3) delegated task risks, central readiness store and target level; (4) licence/download method for WSE2 and original 0.4; (5) visual brand if a ZOMBIEEE logo/palette already exists outside the repo.

**Next action.** Owner review proposed scope and delegation, then independently verify the downloaded v0.4.1 ZIP checksum, replay official skill installer and CLI checks, and approve the tracker source/Pages route before publication.

## Owner decisions — 2026-10-23

- **Release scope:** First playable version needs the original **City** map only. Remaining four original invasion maps are preserved as deferred work under stable leaf `ZOM-MAP-01`, outside v1.0 required denominator.
- **Delegation:** Owner authorises substantial implementation and project operation, including publishing the public tracker now. This grants task-specific operational permission but **does not demonstrate** L1–L5 engineering readiness or justify turning off branch/security safeguards. No CI requested.
- **Publishing:** Owner explicitly wants an interactive static tracker on GitHub Pages immediately. Public JSON and UI only; detailed agent assessment and game logs remain private. Page source must be confirmed by observed live HTTP response.
- **Open:** Exact readiness assessment central private store and any non-City version horizon remain undecided. We can proceed with City-first engineering meanwhile.

**Public tracker observed live (2026-10-23):** https://yigit-denktas.github.io/MBW-ZOMBIEEE-Mod/ — City-first 0/23 required leaves (not accepted) / 0/5 milestones. Static hosted HTML and JSON served; actual interactive click-through and native assistive-technology tests not completed.

## Coordination update 2026-10-23

Three implementation lanes were created from v0.1.8 `main`, with [stable ownership and critical path](agent-handoff.md). Agent A coordinates engine/integration (12 leaves including the optional deferred map), B owns Windows/solo installation (7), C owns telemetry/forensics/QA evidence (5). Six original issues remain; #8/#9 were added for B's new work. The required City release no longer depends on optional `ZOM-MAP-01`. This is delegation/preparation, not game acceptance.

## Integration review status — 2026-10-23

Agent B opened [PR #11](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/11) (discovery, inert install plan and simulated host), with **B-reported** 97/127 tests passed, 30 asset skips. Agent C opened [PR #12](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/pull/12) (crash recorder and forensic report), with code/tests committed but tests explicitly not executed. Agent A reviewed both; startup-recorder ordering, reliable crash tail, symlink safety and test execution remain blocking. No PR merged and no City gameplay acceptance awarded. See [coordination board](agent-handoff.md).

## Discovered work reconciliation — 2026-10-24

**Owner request:** record implementation work absent from the initial proposal with a small dot in the tracker. The 2026-10-23 original [24-leaf snapshot](snapshots/ledger-2026-10-23-original.json) is preserved unchanged and remains the historical reference.

The scoped source now retains **24 original leaves** (23 required City-release outcomes, 1 optional/deferred five-map item), plus **15 discovered supporting leaves** (11 narrowly source/fixture complete, 4 awaiting newest-revision test/review). The discovered items are tagged `workOrigin: discovered`, classified into bug fixes, hardening, source assurance, forensic incident work, integration verification, investigation and governance, and linked by `supportsOutcomeId`. They are **supplemental/non-additive**: `0/23` original required outcome acceptance and `0/5` milestone acceptance remain intact; `11/15` applies **only** to bounded discovered tasks and is not a playable-game claim. Full [before/after scope bridge](scope-changes/2026-10-24-discovered-work.json).

Key work now reflected: original Invasion mode-7 mismatch, across-round reinforcement key, connected/clear City guard posts, compiled post-control byte integrity, verified original patch-chain replay, Windows CRLF regression, official WSE2 dedicated-host component restoration, B/C signed recorder fake-process integration, PID/recovery hardening, C sanitized check-count correction, C round-source provenance, A native round-lifecycle audit, A false-green server mission evidence fix, City incident interpretation and version-pinned acceptance gates. Historical live Windows **boot announcement** used older A/C versions and had no completed result posted at reconciliation time.

**Decision boundary:** this authorizes recording and displaying the discovered tasks, not merging draft PRs, accepting WSE2 gameplay, changing the 23-outcome required scope, or turning implementation into owner-approved baseline. The full release remains unaccepted.

### First observed WSE2 host incident — 2026-10-24 amendment

B has now reported an **actual, owner-authorized** WSE2 1.1.5.4 dedicated host boot from City-only module built using A `141a792`, with C `e455354` passive recorder ready/attached. B observed the host's UDP listener at `127.0.0.1:7240` (not a public UDP bind) and log selecting `tbfc_invasion_4` / `multiplayer_iv`. B also recorded **four `SCRIPT ERROR: Invalid Faction ID: -1`** at original mission template trigger 14, opcode 502. Source attribution and gameplay effects remain unknown. Player join, waves, ally combat, round restarts, final recorder sealing and durable rollback remain open.

This caused **three further discovered tasks** (`ZOM-DISC-16..18`): source-owned faction-ID incident triage (A), bounded noncausal R030/CITY-I08 classification (C), and strict rejection of malformed JSON telemetry identifiers (C). Supporting progress changes **11/15 → 11/18 (61.1%)** because the denominator expanded, not because completed work regressed. Overall retained work becomes **42 = 24 original + 18 discovered**. The original required City-outcome fraction remains **0/23**, and milestones **0/5**. See [new incident scope bridge](scope-changes/2026-10-24-live-incident-amendment.json) and [initial discovery bridge](scope-changes/2026-10-24-discovered-work.json). Neither real host boot nor source test proves City waves or a playable game.
