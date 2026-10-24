---
name: verify-project-accessibility
description: Use when a project tracker, README graphic, interactive roadmap or GitHub Pages guide needs an accessibility audit, WCAG 2.2 review, keyboard or assistive-technology verification, or remediation before acceptance.
---

# Verify project accessibility

Audit the integrated project experience against WCAG 2.2 Level A and AA. Preserve its branding and source authority. Define the tested pages, complete interactions, revision, themes, environments and exclusions before making claims.

Read local instructions, the pinned toolkit's accessibility guide and the [W3C recommendation](https://www.w3.org/TR/WCAG22/). Use [the report template](references/report-template.json) for a criterion-by-criterion record. It starts every A/AA criterion as not-tested; confirm applicability against current W3C material. WCAG 2.2 removed 4.1.1. A green automated scan alone does not establish conformance.

| Surface | Required inspection |
| --- | --- |
| Meaning | Native names/roles/values, language, headings, landmarks, progress fractions and equivalent chart/table content. |
| Interaction | Keyboard/pointer operation, visible unobscured focus, original trigger or logical fallback after DOM changes, filters, empty results, dependencies, disclosures and deep links. |
| Visual access | Computed text contrast (4.5:1 normal, 3:1 large), relevant non-text/focus contrast (3:1), both themes, hover/selection, 320 CSS-pixel reflow, 200% text resize and text-spacing overrides. |
| Alternatives | Target size/spacing (24 CSS pixels or a documented AA exception), no drag-only action, reduced motion, forced colours and persistent concise status updates. |

Inspect the final CSS cascade: a superseded declaration is not a rendered defect. Test reusable defaults as well as branded overrides. Keep a live region mounted while updating its text. Check focus when the invoking item disappears, not only the normal open/close path. Label instrumented enlargement separately from native browser zoom.

Run available automated checks, then exercise actual pages and states manually. Record each check as passed, failed, not-tested or not-applicable, with method, expected/actual result, evidence, environment and reason. Reproduce a defect, make a focused fix, add a useful regression and retest the affected state plus shared-runtime checks. Record named browser and screen-reader versions for actual assistive-technology runs. Semantic DOM inspection cannot verify spoken announcements.

Example: open item A, filter it out, then close its inspector. Focus must reach a visible logical control and the next Tab must continue normally; the result count's live-region node must survive the update. Verify the behavior, not a source-code string.

Package the audit, fixes, regression results and unresolved coverage. Update the authoritative ledger once and regenerate README/Pages. Apply explicit owner authorization already supplied: conditional acceptance takes effect after its conditions are evidenced. If the owner changes an exit criterion, preserve its previous meaning and record the amendment and remaining verification limits. Owner acceptance of a scoped audit never becomes a passed screen-reader test or a universal WCAG conformance claim.

Handoff outcome, tested identity, criteria/results, fixed findings, unavailable checks, acceptance basis and next action. Common mistakes: reporting plans as tests, counting unknowns as passes, dropping scope to reach 100%, replacing the brand, or ignoring existing authorization.
