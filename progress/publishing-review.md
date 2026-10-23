# GitHub and tracker publishing — review proposal

**Current facts (2026-10-23):** repository public, GitHub Pages disabled, no website, no GitHub releases, no open PRs before this setup branch, six open GitHub issues. User explicitly requested **no CI** for this project; do not create workflows as an incidental tracking install.

**Prepared, not applied:** the source-to-GitHub crosswalk is in `progress/issue-mapping.json`. Reuse Issues #1–#6; do not close, relabel, duplicate or overwrite discussions. New launcher/installer work should get separate issue drafts only after owner confirms which leaves are required. GitHub Projects board/milestones/labels are *not* created. The static tracker in `site/index.html` is a local preview, not a deployed website.

**Publishing candidate:** owner may opt into GitHub Pages later, sourcing a reviewed read-only public record. If approved, a separate build will mirror validated public JSON beside the site and publish from a dedicated branch or Pages source permitted by repository policy. Never fetch GitHub credentials from the browser or write back to issues from the tracker.

**Preview now:** `python -m http.server 8080` from the repository root, then `http://localhost:8080/site/`. The site fetches `../progress/ledger.json`; opening the HTML directly by file:// may fail fetch. The same source drives the proposed README counts. In future publishing, copy the public projection to a deterministic site path and check that nothing private is included.

**Accessibility gates pending:** test keyboard-only, visible focus, search/filter screen-reader labeling, 390 CSS px, 200%/400% zoom, contrast, reduced motion, semantic headings and contrast of actual rendered elements. Source-only checks are not a complete WCAG 2.2 review.

**Before publish or merge:** verify the release ZIP actual SHA-256 (currently release metadata only), replay the official kit installer, run official `project_record check` and `pipeline`, validate actual fractions and GitHub issue mappings, review dark/light styling, and obtain owner approval for baseline/Pages.
