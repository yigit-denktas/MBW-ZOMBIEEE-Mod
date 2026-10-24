# Consolidation and work-package plan (2026-10-24)

## Baseline
- `main` = `df94067` (consolidated save point, tag `save/0.3.0-beta.1-consolidated-2026-10-24`)
- 634 tests OK, release gate 0, runtime_verified=false, acceptance none.
- Do not mass-merge branches again. One package at a time: **target → tests → build → review → integrate**.

## Archive policy
Every pre-consolidation branch tip is frozen as an annotated tag under `archive/2026-10-24/`. Tags preserve paid work even after branches are deleted. Manifest: `archive/2026-10-24/branches.json`. No archive tag is acceptance.

## Branch policy
- Long-lived branches: `main` and `gh-pages` only.
- One short-lived branch per package: `pkg/<id>-<slug>`; delete after integration.
- Rebase/merge from current `main` immediately before work; never let a worktree drift.

## Scouting classification
- **Integrated in main:** C telemetry/probe/summary + spatial consumer; H Rhodok/Warband/matrix docs; G #52 asset/licence docs; replay comparison skeleton.
- **Reviewed, integration pending:** F gate/privacy fix #76 (`ccb6798`) — E + review-b2 PASS.
- **Blocked/deferred:** A nextplay packages (no-stacking, tree hash, headshot manifest); F parallel lanes (lane2 rollback/repair/uninstall); G asset batch2 (licence review); E crash triage docs; F fire-mode; F task73 plan; A formation/firepower/heatmap notes.
- **Superseded:** A p0-fix/ranged-fix (ancestors of nextplay); a-formation-p0 vs merged formation; duplicate heatmap notes.

## Granular packages
### PKG-01 Repository consolidation + archive (Lead)
Target: one green `main`, archive tags, archive manifest, no duplicate active branches.
Tests: 634+ suite OK, release gate 0, no personal paths, Pages 200.
Review: review-b2 read-only signoff. Acceptance: none; source save point.

### PKG-02 Integrate F gate/privacy fix #76 (F)
Target: escaped/mixed/UNC path detection on `main`; gate fail-closed; no false clean.
Tests: `test_windows_m2_gates` + `test_windows_release_traceability` 26 OK; full suite/gate.
Review: E + review-b2 PASS already; re-run after integration.

### PKG-03 A per-feature auditable packages (A)
Target: every manifest has `included[]`/`excluded[]`, documented `package_tree_sha256` algorithm + validator, no absolute paths, leader-id 0.
Tests: manifest validator + package hashes; reviewer re-check.
Acceptance: reviewer PASS; no gameplay acceptance.

### PKG-04 Early ranged engagement (A + C + D)
Target: forward line + order-scope fire, first shot <30 s, fired ratio >=0.4, no crash.
Tests: 3-min quick lane then 10-min; corrected summary caveats; lane JSON.
Review: E/review-b2. Acceptance: runtime only after owner review.

### PKG-05 Cosmetic-half zombie shields (A + D)
Target: half invaders practice shield, shield skill 0, no wooden shields; receipt proof; D screenshots.
Tests: shield policy gate + runtime screenshot. Review: reviewer + owner.

### PKG-06 Parallel-lane lifecycle (F)
Target: lane2 rollback/repair/uninstall lane-aware; lane/port/module pairing; concurrent WSE2 explicit UNKNOWN.
Tests: 44+ launcher tests, lane2 lifecycle test. Review: review-b2.

### PKG-07 Docs/assets integration (E/G)
Target: crash triage, asset batch2 docs, task73 plan into archive or docs; no binaries.
Tests: links/JSON/licence checks. Review: E/review-b2.

## Ordered execution
1. PKG-01 (finish green main + archive cleanup)
2. PKG-02 (gate fix integration)
3. PKG-03 (A packaging audit)
4. PKG-04 + PKG-05 in parallel after PKG-03 (same base, separate branches)
5. PKG-06
6. PKG-07
7. Ledger/Pages sync once per package; no acceptance inflation.

## Known limits
- No accepted user stories/milestones; 8/23 required done, 0/5 accepted.
- Runtime fire gate still FAIL; fire volume/early engagement unproven.
- Hit attribution unavailable.
- Concurrent WSE2 unverified.
- Raw gameplay/public assets remain private.
