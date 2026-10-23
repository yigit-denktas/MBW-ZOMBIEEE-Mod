# Adoption plan — initial establishment (review draft)

**Selected workflow:** `establish-project-tracking`. There was no authoritative progress ledger in the target repository at 048564a526de9b36abd55874271c7b80f36e5cf5; README/ROADMAP/CHANGELOG and Issues #1–#6 are existing history and must be retained, not replaced by a fabricated tracker.

**Authority:** `progress/ledger.json` is a proposed source of future scoped work, with owner approval pending. Existing GitHub issue numbers/titles/comments remain stable and own their discussions/assignees. README progress region and tracker are derived, never issue writers. VERSION/CHANGELOG continue to own remaster SemVer/history. No changes to the game source, GitHub issues, CI workflows, merge permissions or Pages deployment are authorised by tracking installation.

**Source crosswalk:** #1 P0 engine → ENG-01..03; #2 P1 allies → AI-01/02, WAVE-01; #3 P2 maps → AI-03/MAP-01; #4 P3 QoL → ADMIN-01/PERF-01; #5 P4 attribution → LEGAL-01/REL-01; #6 final evidence → OBS-01/02 and QA-01/02. Each accounting leaf appears once even if an issue references more than one deliverable. All six original issue IDs remain as stable GitHub URLs.

**Proposed new scope (not approved):** Windows autodetection/install/desktop shortcut and one-click local mission startup; a crash-resistant external flight recorder. Future friend co-op and public hosting are explicitly deferred. The proposed denominator is **24 required leaves, 0 accepted Done**, and **5 milestones, 0 accepted**. Original repository had no comparable canonical fraction: **before = Not measured**, not 0%. Prototype code is recorded as `active`/review pending execution, not marked accepted.

**Brand/site:** target has no website, brand tokens or logo available in GitHub tree. The prepared preview will use provisional graphite/ember/bone colours inspired by zombie-horror game art, system fonts only, and a route under `site/index.html`; no logo rights or actual website existence claimed. Publication to Pages requires a separate owner-approved source/publishing review.

**Readiness:** current evidenced L0; L2 provisional desired for bounded reviewable work, L3 prior to runtime feature claims. Full ten-dimension assessment is private and central persistence is pending. No unattended merge/deploy promotion. R0 docs/read, R1 reversible setup in branch, R2 ordinary gameplay implementation for review, R3 trust/security requires explicit review, R4 destructive work proposal only.

**Rollback:** this entire migration lives in branch `project-record-setup-v041`. No existing main-source files are removed. Not merging the branch preserves 0.1.8 `main`; after any later merge, revert the adoption commit and leave existing README/ROADMAP/issue history intact. Do not publish or enable CI automatically.

**Checks pending:** verify actual release ZIP and official installer replay; run toolkit `check`, `pipeline`, README count parity and real keyboard/zoom/contrast browser review. Local structured source consistency alone does not certify WCAG conformance or a published tracker.
