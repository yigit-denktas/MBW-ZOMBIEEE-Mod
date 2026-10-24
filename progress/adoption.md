# Adoption plan — initial establishment (review draft)

**Selected workflow:** `establish-project-tracking`. There was no authoritative progress ledger in the target repository at 048564a526de9b36abd55874271c7b80f36e5cf5; README/ROADMAP/CHANGELOG and Issues #1–#6 are existing history and must be retained, not replaced by a fabricated tracker.

**Authority:** `progress/ledger.json` is a proposed source of future scoped work, with owner approval pending. Existing GitHub issue numbers/titles/comments remain stable and own their discussions/assignees. README progress region and tracker are derived, never issue writers. VERSION/CHANGELOG continue to own remaster SemVer/history. No changes to the game source, GitHub issues, CI workflows, merge permissions or Pages deployment are authorised by tracking installation.

**Source crosswalk:** #1 P0 engine → ENG-01..03; #2 P1 allies → AI-01/02, WAVE-01; #3 P2 maps → AI-03/MAP-01; #4 P3 QoL → ADMIN-01/PERF-01; #5 P4 attribution → LEGAL-01/REL-01; #6 final evidence → OBS-01/02 and QA-01/02. Each accounting leaf appears once even if an issue references more than one deliverable. All six original issue IDs remain as stable GitHub URLs.

**Proposed new scope (not approved):** Windows autodetection/install/desktop shortcut and one-click local mission startup; a crash-resistant external flight recorder. Future friend co-op and public hosting are explicitly deferred. The proposed denominator is **23 required leaves (+1 optional retained map expansion), 0 accepted Done**, and **5 milestones, 0 accepted**. Original repository had no comparable canonical fraction: **before = Not measured**, not 0%. Prototype code is recorded as `active`/review pending execution, not marked accepted.

**Brand/site:** target has no website, brand tokens or logo available in GitHub tree. The prepared preview will use provisional graphite/ember/bone colours inspired by zombie-horror game art, system fonts only, and a route under `site/index.html`; no logo rights or actual website existence claimed. Publication to Pages requires a separate owner-approved source/publishing review.

**Readiness:** current evidenced L0; L2 provisional desired for bounded reviewable work, L3 prior to runtime feature claims. Full ten-dimension assessment is private and central persistence is pending. No unattended merge/deploy promotion. R0 docs/read, R1 reversible setup in branch, R2 ordinary gameplay implementation for review, R3 trust/security requires explicit review, R4 destructive work proposal only.

**Rollback:** this entire migration lives in branch `project-record-setup-v041`. No existing main-source files are removed. Not merging the branch preserves 0.1.8 `main`; after any later merge, revert the adoption commit and leave existing README/ROADMAP/issue history intact. Do not publish or enable CI automatically.

**Checks pending:** verify actual release ZIP and official installer replay; run toolkit `check`, `pipeline`, README count parity and real keyboard/zoom/contrast browser review. Local structured source consistency alone does not certify WCAG conformance or a published tracker.

## Owner decision update 2026-10-23

First release City only; original map expansion leaf `ZOM-MAP-01` moved out of the v1.0 required denominator (23 required + 1 optional retained), without deleting its original evidence or ID. User authorises static GitHub Pages publication now. Prepare a separately committed `gh-pages` static snapshot and record deployment observation; do not publish private readiness assessment or game logs. GitHub Pages activation may still require settings permission. This change from proposed 24 to proposed 23 is explained as a scope boundary refinement before baseline approval, not progress.

**Publication observation:** https://yigit-denktas.github.io/MBW-ZOMBIEEE-Mod/ was retrieved successfully after pushing `gh-pages`; hosted JSON matched the City-first 23+1 scope. GitHub Pages is enabled, no CI. Browser interaction testing not completed; source kit ZIP still not independently downloaded/verified.

## Parallel delivery assignment (2026-10-23)

[Three-agent board](agent-handoff.md) and [machine-readable ownership](agent-allocation.json) divide all 24 retained work leaves (A 12, B 7, C 5). The final required `ZOM-QA-02` City test formerly incorrectly depended on optional five-map expansion; that dependency was removed. Two new issues #8/#9 cover B's installer/solo work without recreating original issues #1–#6. Branches based on unmodified `main@048564a`; no concurrent edits of shared paths and no CI.

## Supplemental discovered work update — 2026-10-24

Applied `adapt-project-tracking` → `govern-project-scope` → `update-project-progress` → `present-project-tracking` conventions. Before modifying the source, preserved [the raw original 24-item observation](snapshots/ledger-2026-10-23-original.json), original blob `c19e866f0e0acdf2d6cc5ee5cf0f20a2ae518140`. No stable original IDs, acceptance criteria, milestone gates, aliases, dependencies or original optional-scope status were removed or reassigned.

**Before → after:** retained work `24 → 39` (15 discovered support leaves); *required City-outcome progress* `0/23 → 0/23`, 0.0% unchanged; accepted milestones `0/5 → 0/5`; separately displayed discovered support work `not tracked → 11/15` narrowly completed (73.3%), four in review. New source IDs `ZOM-DISC-01..15` carry `workOrigin=discovered`, a work taxonomy, one existing `supportsOutcomeId`, supporting criterion/revision and `required=false` to prevent completing an original outcome twice. See [machine-readable scope change](scope-changes/2026-10-24-discovered-work.json).

**View:** existing dark graphite/ember/bone host tracker gains small accent `●`, accessible text “Discovered task,” Origin filter, separate 11/15 metric and evidence links. Original milestone/required-work denominator remains protected. GitHub Pages publication is a separate observed deployment from Git-source update. Live browser focus/screen-reader and full toolkit `check` still require a pinned local checkout; semantic source inspection alone is not those tests.

**Priority/review impact:** file/protocol and original archive identity may be source-verified while C current suite, B journaled installer and actual City WSE2 scene/wave evidence are outstanding. The first owner-authorized boot was announced on an older A/C pair and cannot certify newer fixes. No original assets, Windows private paths, game logs or user tokens entered public tracking data.

### Current live-engine amendment — 2026-10-24

After the first 15 supplemental leaves were recorded, B published a scoped **real dedicated-host boot** observation and four engine script errors. The preboot **39-item** state was preserved under [the second immutable snapshot](snapshots/ledger-2026-10-24-preboot.json); [the amendment](scope-changes/2026-10-24-live-incident-amendment.json) adds `ZOM-DISC-16..18` with explicit cause-unknown and latest-test-pending statuses. Retained leaves: **39 → 42**; discovered supporting work **11/15 (73.3%) → 11/18 (61.1%)**. Original City required outcomes **0/23 → 0/23**, accepted milestones **0/5 → 0/5**. The three extra leaves do not make B's host boot a completed invasion or double-credit existing ENG/OBS outcome IDs.

On the public tracker, the discovered dot/filter/progress figure remains data-derived and therefore follows the current JSON. Its new 11/18 fraction must not be combined with the owner-accepted release percentage. GitHub Pages branch content was updated, but a direct live HTTP/browser response for the newest revision was not independently available in this run.

### Branch unification, merged main and incident triage — 2026-10-24

Reviewed branches were merged into `main` at `4c56242` (merges `9eed34b` for #10, `0fe86a4` for #12, `4c56242` for #11) after green per-branch Windows suites and a merged-main suite of **340 OK / 4 skips**. The pre-change ledger is preserved at [the premerge snapshot](snapshots/ledger-2026-10-24-premerge.json), the post-change source at [the postmerge snapshot](snapshots/ledger-2026-10-24-postmerge.json), and the bridge in [the unification scope change](scope-changes/2026-10-24-unification-and-postmerge.json).

Accounting: retained work **42 → 46**; required City outcomes **0/23 → 0/23**; accepted milestones **0/5 → 0/5**; discovered supporting work **11/18 (61.1%) → 21/22 (95.5%)** because four unplanned items were added and three are narrowly complete. The remaining active discovered item is the observed Windows recorder file-replace race (`ZOM-DISC-22`). Completion of supporting items still grants no release credit and no gameplay evidence.

Live-session refinement: the historical candidate's client joined but observed `team1=0/wave=0`; trigger-14 faction errors were proven original/non-causal in source scope; the probe `mode` field was misread as game type (it is `zdr_defence_mode`); trigger-32 `Illegal lvalue` root cause was missing WSE2 msfiles operation metadata, fixed by C in `675188a`. Engine game type, round start, wave progression and AI combat remain **unobserved**. Public Pages content is refreshed with a byte-identical ledger; live-page/assistive verification of the new revision remains pending.

### Live bot-count, roster and respawn amendment — 2026-10-24

The merged-main candidate produced the first observed enemy wave (`wave=1`, `team1=41`, `wave_change`) after `set_bot_count 2 32`; the baseline had stayed `team1=0/wave=0`. Root cause is dedicated rotation bot configuration, not the build. Two further defects were observed: wave-1 generic bots are faction-default Crazed Civilian (not native Zombie troops), and after player death there was no respawn/new round (`team0=0`, `wave=0`).

Recorded as issues **#13** (City wave roster/completion/allies), **#14** (launcher/rotation team-2 bots and roster), **#15** (recorder atomic-replace race, `ZOM-DISC-22`) and **#16** (seal host ZDB1 stdout, `ZOM-DISC-24`); **#1** closes as superseded by #13. Ledger: retained work **46 → 48**; required City outcomes **0/23 → 0/23**; milestones **0/5 → 0/5**; discovered **22 → 24** (21 narrowly done, 3 active). Main tip `0eb9374` full suite **351 OK/4 skips**; A's rotation checker enforces the observed launcher commands. No gameplay/wave-completion acceptance is claimed.

### Bug-fix / diagnostics-hardening amendment — 2026-10-24

Owner asked to record the diagnostics upgrades as bug fixing, not the usual acceptance path. Main `42d4ec3` merges C telemetry v2 (`0393794` / `a29fabf`) and B sealing (`42d4ec3` / `d1011e2`): bounded per-team troop histogram + explicit observed lifecycle events, fail-closed receipt summary CLI, host-stdout sealing, atomic-replace read retry, validated rotation builder. Merged suite **380 OK/4 skips over 3 consecutive runs** (pre-fix flake 1/7, not a stability proof).

The five upgrades map to support leaves `ZOM-DISC-22..26` (22/25/26 done; 23/24 active pending live rotation/roster verification and a sealed ZDB1 attempt). Ledger: retained **48 → 50**; required City outcomes **0/23 → 0/23**; milestones **0/5 → 0/5**; discovered **24 → 26 (24 done, 2 active)**; `runtime_verified=false` throughout. Optional `ZOM-DISC-27` umbrella not added. No gameplay or release acceptance is claimed.

**Hands-off AI evidence + fixes (2026-10-24).** Main `24ed22f` (canonical build `a6b5fe9`) merges the hands-off defender/roster fixes, C's kill/troop accessor correction, F's one-command launcher (PR #19) and defender-squad rotation (PR #20), E's docs/provenance (PR #18) and A's firearm accuracy profile. D's sealed bundles show native Zombies 894..911, team-0 defenders 981..984 (bots_team0=4), both-team positions/engagement, sealed ZDB1 stdout, and a passed play_city lifecycle; wave 2+/completion and combat feel remain open. Accounting: retained **50→53**; required City outcomes **0/23**; milestones **0/5**; discovered **27→30** (29 done, 0 active, one optional five-map backlog, `runtime_verified=false`). Legal gate `ZOM-LEGAL-01` remains backlog: credits verified from the archived OP, permission owner-attested, redistribution not cleared. No gameplay or release acceptance.
