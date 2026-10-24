# GitHub and tracker publishing — review proposal

**Current facts (2026-10-23):** repository public, GitHub Pages disabled, no website, no GitHub releases, no open PRs before this setup branch, six open GitHub issues. User explicitly requested **no CI** for this project; do not create workflows as an incidental tracking install.

**Prepared, not applied:** the source-to-GitHub crosswalk is in `progress/issue-mapping.json`. Reuse Issues #1–#6; do not close, relabel, duplicate or overwrite discussions. New launcher/installer work should get separate issue drafts only after owner confirms which leaves are required. GitHub Projects board/milestones/labels are *not* created. The static tracker in `site/index.html` is a local preview, not a deployed website.

**Publishing candidate:** owner may opt into GitHub Pages later, sourcing a reviewed read-only public record. If approved, a separate build will mirror validated public JSON beside the site and publish from a dedicated branch or Pages source permitted by repository policy. Never fetch GitHub credentials from the browser or write back to issues from the tracker.

**Preview now:** `python -m http.server 8080` from the repository root, then `http://localhost:8080/site/`. The site fetches `../progress/ledger.json`; opening the HTML directly by file:// may fail fetch. The same source drives the proposed README counts. In future publishing, copy the public projection to a deterministic site path and check that nothing private is included.

**Accessibility gates pending:** test keyboard-only, visible focus, search/filter screen-reader labeling, 390 CSS px, 200%/400% zoom, contrast, reduced motion, semantic headings and contrast of actual rendered elements. Source-only checks are not a complete WCAG 2.2 review.

**Before publish or merge:** verify the release ZIP actual SHA-256 (currently release metadata only), replay the official kit installer, run official `project_record check` and `pipeline`, validate actual fractions and GitHub issue mappings, review dark/light styling, and obtain owner approval for baseline/Pages.

## Owner-approved publishing decision 2026-10-23

Publish the interactive **public-only tracker now** from branch `gh-pages` at repository root, without CI, without adding action credentials, and without merging the toolkit PR first. Public source is a manually copied review snapshot from proposed scoped ledger. Owner has authorized the publication, not declared runtime gameplay verified. A commit to `gh-pages` is staged separately from GitHub Pages enablement and observed URL health. If hosting settings cannot be edited by the connected app, document the exact remaining GitHub Settings → Pages action and do not claim live deployment.

## Observed live static publication (2026-10-23)

- URL: https://yigit-denktas.github.io/MBW-ZOMBIEEE-Mod/
- GitHub Pages publication branch `gh-pages` commit: `3466b7c329b7bf94185b00aabf6ff283de9e86c0`; later HTML title-only update `cb2870f2a49e6785ede1a0374574e230465c6fd0`.
- Public GET HTML and JSON both succeeded independently, repository API reports `has_pages=true`. Hosted JSON parsed to 23 required leaves, 1 deferred optional leaf and 5 milestones, with 0 accepted outcome gates.
- Public branch contains only `index.html`, `.nojekyll`, `progress/ledger.json` and a short public `README.md`. No agent assessment details, private logs, game assets, credentials or CI.
- Page JavaScript syntax and static semantic/focus/responsive markers checked. Real browser click/keyboard and screen-reader tests remain **unverified** due browser-testing wallet limit. Do not claim WCAG certification.
- This is a **manual Pages snapshot**; new changes on `project-record-setup-v041` will not appear until a reviewed copy is committed to `gh-pages`. Owner explicitly requested immediate publication.

## Three-agent allocation refresh

Public `gh-pages` JSON is a reviewed snapshot of `progress/ledger.json`. The current refresh adds per-leaf implementation ownership (A/B/C) and removes the City release's incorrect dependency on optional five-map work; acceptance stays 0/23. The static view must offer an agent filter and must not expose private assessment data or engine logs. Agent A is the only publisher/ledger editor.

## Publication refresh after branch unification — 2026-10-24

Public `gh-pages` content was refreshed from the canonical tracker: `progress/ledger.json` is copied byte-identically to `gh-pages/progress/ledger.json`, and `index.html` carries the updated source line (merged main `4c56242`). The published branch contains only `index.html`, `.nojekyll`, `progress/ledger.json` and a short public `README.md`; no agent assessment details, private logs, assets, credentials or CI. Interactive browser/assistive verification of the refreshed revision remains pending. The public discovered fraction (21/22 bounded supporting work) must not be combined with the 0/23 required City-release measure.

## Publication refresh after live bot-count observation — 2026-10-24

Public `gh-pages` content was refreshed from the canonical tracker: ledger copied byte-identically, page source line updated to main `0eb9374` and the observed first enemy wave with open roster/respawn defects. The public views must show that one observed wave is not wave completion or gameplay acceptance; required City outcomes remain 0/23 and milestones 0/5, discovered support is 21/24 bounded work. No assets, logs, private paths or credentials are published. Interactive browser/assistive verification of the refreshed revision remains pending.

## Publication refresh after telemetry-v2 bug-fix pass — 2026-10-24

Public `gh-pages` content was refreshed from the canonical tracker for main `42d4ec3`: byte-identical ledger, updated page source line naming the bug-fix/diagnostics-hardening pass (`ZOM-DISC-22..26`), merged suite 380 OK/4 skips over three clean runs, and the retained caveats (pre-fix flake observed once in seven runs; no gameplay/wave acceptance; required City outcomes 0/23, milestones 0/5). No assets, logs, private paths or credentials are published. Interactive browser/assistive verification of the refreshed revision remains pending.
