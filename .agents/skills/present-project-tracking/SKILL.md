---
name: present-project-tracking
description: Use when project progress needs README graphics, interactive roadmap or work views, GitHub Pages integration, branded percentages, scope links, or interaction/accessibility verification.
---

# Present project tracking

Share meanings, calculations and interaction outcomes. Let the project keep its typography, colours, imagery, composition, routes and site technology.

Read project instructions and actual brand/site sources, then the pinned toolkit's `standards/PRESENTATION.md`, `standards/ACCESSIBILITY.md` and `standards/AUTOMATION.md`. Visually inspect the existing README/site before choosing the integration. A generic dashboard is a reference, not a required skin.

Set `presentation.renderer: host` for an existing site. Build normalized record/history/delivery data and connect its existing components or optional `mountExplorer(root, record, options)` and `mountDelivery(root, record, options)`. Inspect their actual API and scoped styles before mounting. Inherit host typography and approved semantic colour roles; preserve navigation, URLs, font policy and global styles.

| View | Required reader outcome |
| --- | --- |
| Overview | Purpose, what works, named fractions/percentages, observation/coverage, active outcome and next gate. |
| Roadmap | Milestone outcome/horizon, supporting work, acceptance gates, dependencies and next action. |
| Work | Stable IDs, filters, equivalent readable list/map, nearby selected-item criterion/state/owner/dependencies/proof and source edit link. |
| History/delivery | Scope/state effects, changes, candidate readiness, actual publications and observed deployments kept distinct. |
| README | Compact brand-owned graphic plus equivalent text/table, scope/evidence links and the same metrics/source as Pages. |

Fit these roles to existing routes. Preserve selection through deep links, reload and Back. Touch selection gives immediate visible feedback without hover; native controls, clear targets and focus restoration support keyboard use. Honour reduced motion. Long titles reflow; avoid hidden content and unnecessary nested scrolling. Empty denominators say Not measured; errors and stale/partial observations are visible.

Preview a marked README update from the toolkit root:

```sh
PYTHONPATH=src python3 -m project_record readme --file /path/to/project/README.md --module /path/to/build/loomglass/README-module.md
```

Apply with `--write` only under the project’s writer policy; a generator-owned README changes through its generator. Keep real progress/image URLs and meaningful graphic alternative text. Preserve outside-region bytes.

Use **verify-project-accessibility** for a WCAG audit or accessibility remediation.

Review the actual public projection before integrating into the existing deployment workflow. Test branded contrast, desktop/390px reflow, 200% text zoom, themes, touch selection, keyboard traversal/activation, focus, readable-list equivalence and linked state. Record tested revision/environment and screenshots. Actual screen-reader output is a separate observed test: semantic inspection or keyboard success leaves it pending.

Handoff integration paths, brand sources, named metrics, public review, interaction results, unresolved gates, source identity, rollback and next owner/action. Publish only under task authorization; a local preview establishes no deployment.

Common mistakes: recolouring one universal shell; editing percentages by hand; using an image as the only explanation; reporting unrun accessibility checks as passed.
