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
