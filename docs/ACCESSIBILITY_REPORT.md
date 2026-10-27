# Pages accessibility audit — static scope

**This is not a WCAG conformance claim.** It records what a static audit of one
page at one revision can prove, what it cannot, and the exact remediation still
required. It grants no acceptance: `runtime_verified=false`, `acceptance=none`.
UNKNOWN is not PASS.

| Field | Value |
| --- | --- |
| Page | `site/index.html` (61,910 bytes, 459 lines) |
| Revision | `f766776` (`main`, "release: metadata sync for PKG-02 integration") |
| Package | branch `pkg/pages-a11y`; adds only this report and `tests/test_site_accessibility.py` |
| Standard mapped | WCAG 2.2 Level A/AA, <https://www.w3.org/TR/WCAG22/> |
| Date | 2026-10-27 |
| Auditor | Pages accessibility auditor (delegated agent) |
| Reviewer | **E** (independent review; no self-approval) |
| Method | static source parse (`html.parser`) + WCAG 2.x sRGB contrast arithmetic; **no browser or assistive-technology run in this package** |
| Site edits | none (read-only on `site/index.html` by instruction) |

## 1. Claim boundary

The audited artifact is the page source at `f766776`. Everything below labelled
**verified** is a fact about that source: element structure, attribute wiring,
and arithmetic over the colours the stylesheet declares. Nothing below is a
statement about what a person using NVDA, JAWS, VoiceOver, a magnifier, a
keyboard-only browser, or Windows high-contrast mode actually experiences. Those
remain UNKNOWN (section 3) and must not be read as passes.

Two claims are explicitly out of bounds for this package: no WCAG 2.2 A/AA
conformance claim, and no project acceptance. A later fix package must re-run
this audit after changing the page.

## 2. Verified by this package (static)

| # | Check | Method | Result | Evidence |
| --- | --- | --- | --- | --- |
| 1 | Document language | parse `<html>` attributes | PASS — `<html lang="en">`, single `<html>` | `site/index.html:2` |
| 2 | Skip link is first tab stop, target resolves inside `main` | walk body in document order, resolve `href` fragment | PASS — `<a class="skip" href="#main">` is the first focusable element; `#main` exists inside `main` | `site/index.html:79`, `:86` |
| 3 | Landmark and heading skeleton | count `header`/`main`/`footer`/`nav`, check document order and `h1` count | PASS — one banner, one main, one contentinfo, one labelled navigation, one `h1` ("Project Record") before `main` | `site/index.html:80-86`, `:153` |
| 4 | Accessible names on the map and its controls | accessible-name approximation over static markup | PASS — map is a named `group` with `aria-roledescription` and `aria-describedby` → existing help/status ids; dependency controls, legend and zoom groups are labelled; zoom in/out have distinct names; all buttons and all form controls have names | `site/index.html:97-101`, `:140-148` |
| 5 | ARIA id references resolve | resolve every `aria-labelledby`/`describedby`/`controls`/`owns`/`flowto` token | PASS at first paint — no dangling id references, no duplicate ids (54 ids) | whole document |
| 6 | Keyboard focusability | every interactive element is native or has non-positive `tabindex`; no fake control roles; no positive tabindex; no focusable content in `aria-hidden` subtrees | PASS — all controls are native `button`/`input`/`select`/`a`; the map scroller is a labelled `region` with `tabindex="0"`; the detail panel is `tabindex="-1"` and `selectItem(..., focus)` calls `d.focus()`; map cards are created as `<button>` with roving `tabIndex` (`n===target?0:-1`), so the map is one tab stop plus its controls | `site/index.html:100`, `:148`, `:189-206`, `:294`, `:298` |
| 7 | Declared key handling | source assertions on handlers | PASS (declarative only) — Arrow up/down/left/right, Home, End, Escape are handled for map cards; queue filters handle Left/Right; help text documents Tab/Enter/Escape/Arrows; reduced-motion query respected | `site/index.html:99`, `:347-365`, `:436`, `:223` |
| 8 | Live status regions exist from first paint | parse `role="status"` / `aria-live` | PASS — `#live-status`, `#dep-status`, `#dep-summary`, `#count`, `#queue-count` are `role="status"`; `#dep-zoom-level` is an `<output aria-live="polite">`; all values are `polite` | `site/index.html:87`, `:97`, `:101-102`, `:135`, `:146` |
| 9 | Declared text palette meets 4.5:1 | WCAG contrast formula over `:root` tokens and declared state colours (28 pairs) | PASS — range 4.95:1 (`#e67e22` on pressed chip) to 16.13:1 (body text) | `site/index.html:8-27`, `:47-75` |
| 10 | Declared border/focus/state palette meets 3:1 | same formula (14 non-text pairs) | PASS for the border token, focus ring and all state edge colours; **not** a statement about the rendered map edges (A11Y-01) or card boundaries (A11Y-07) | `site/index.html:8-12`, `:47-57` |
| 11 | Explicit no-conformance statement | string assertions on page and report | PASS — "not a WCAG conformance claim" is visible text on the page; no positive conformance phrase anywhere; this report repeats it | `site/index.html:103` |
| 12 | No third-party script / no inline handlers | source scan | PASS — no `<script src=`, no `onclick`, single first-party script | `site/index.html:154-458` |

Supporting defaults that also verified structurally: `*:focus-visible` outlines
at 3 px with offset (`:10`), `prefers-reduced-motion` overrides (`:29`),
`prefers-reduced-motion` respected by programmatic scrolling (`:223`), 44 px
minimum target height for buttons/inputs (`:10`), and alt text on the only
`<img>` (`:121`).

## 3. UNKNOWN — not tested here

None of the rows below may be cited as a pass. Each names what would close it.

| Unknown | Why it stays UNKNOWN | What would close it |
| --- | --- | --- |
| NVDA speech | no screen-reader run; DOM structure cannot prove announcements, verbosity, or landmark naming in speech | NVDA 2025.x + Firefox/Chrome on Windows 11, recorded speech transcript per state (map focus, path change, queue filter, detail selection, empty result) |
| JAWS speech | same | JAWS 2026 + Chrome, same script |
| VoiceOver speech | same | VoiceOver (macOS 15/Safari or iOS 18), same script |
| Rendered-pixel contrast | the 42 contrast checks are arithmetic over declared colours; no screenshot sampling, no antialiasing, no opacity compositing on rendered pixels, no display/gamma variance | screenshot sampling of computed foreground/background per state (normal, hover, pressed, focused, path-focused, dimmed) at both DPRs, or a browser probe that reads final computed styles *and* composites known opacity |
| 200% text-only resize | no browser run; the existing browser suite covers 320 CSS-px reflow, which is a different axis (1.4.10) | Chrome/Firefox at 200% text-only zoom, checking clipping of the map controls, queue chips, stat cards and detail panel, plus text-spacing overrides (1.4.12) |
| Forced colours (Windows high contrast) | no emulation run; the stylesheet has **no** `@media (forced-colors: active)` rules at all (0 matches), and every surface is a hard-coded hex value with `color-scheme: dark`; path-focus and `aria-pressed` states are colour-only, so they are likely flattened or lost | Edge/Chrome with `forced-colors: active` emulation plus Windows HCM themes (e.g. High Contrast Black/White), checking that the selected/path states stay distinguishable through borders, patterns or text |
| Browser focus order and real key handling | this package asserts handlers, not behaviour | headless/real-browser run of the full tab sequence including the expanded map overlay, plus the existing `tests/test_site_dependency_map.py` browser suite (map keys, zoom, pan, 320 px reflow) on a host with Chrome/Edge; that suite skips — never passes — without a browser |
| Screen-reader announcement of the live regions | live regions exist and are polite, but announcement behaviour, duplicate announcements (A11Y-08) and the silent detail update (A11Y-02) need AT | AT runs above, capturing whether each status change is spoken once |
| Target size (2.5.8) | declared `min-height` values look compliant (44 px, 38 px, 34 px) but computed boxes need layout | measured bounding boxes in a browser at default and 200% zoom |
| Published `gh-pages` rendering | the published copy was not inspected; only `main`'s source at `f766776` was audited | re-run this audit against the deployed artifact after publication |

Also out of scope: light theme (the page declares only dark), print styles, RTL,
and JavaScript-disabled rendering.

## 4. Findings

| ID | Severity | Where | Summary |
| --- | --- | --- | --- |
| A11Y-01 | Major | `site/index.html:57` | Default dependency-graph edges render at **1.21:1**; even "Emphasize all links" reaches only 1.97:1 — below the 3:1 non-text threshold for the information that is the point of the view |
| A11Y-02 | Major | `site/index.html:148`, `:192` | Selecting a work item deletes `#detail-title`; the `complementary` landmark's `aria-labelledby` then points at nothing |
| A11Y-03 | Moderate | `site/index.html:147`, `:211` | Empty-filter message is a `<p>` appended directly inside `role="list"`, which requires `listitem` children |
| A11Y-04 | Moderate | `site/index.html:94`, `:451` | The whole milestone roadmap is a polite live region; five cards with several sentences each are inserted at load |
| A11Y-05 | Moderate | `site/index.html:33`, `:97`, `:412-413` | "Expand map" turns the map section into a `position:fixed; inset:0` overlay with no focus containment, and reports state with `aria-pressed` instead of `aria-expanded` |
| A11Y-06 | Minor | `site/index.html:79`, `:86` | Skip link says "Skip to roadmap" but lands on the start of `main` (live status + warning), and `#main` is not focusable (`tabindex="-1"` absent) |
| A11Y-07 | Minor / at-risk | `site/index.html:43`, `:47`, `:55` | Card boundary is not perceivable at 3:1: node fill vs map background 1.10:1, node border `#3c4658` 1.85:1, dashed column border `#3a4354` 1.87:1, de-emphasised node border `#2b323d` 1.36:1 |
| A11Y-08 | Minor | `site/index.html:97`, `:343-344` | Every zoom change is announced twice: `#dep-zoom-level` (live `<output>`) and `#dep-status` both update politely |
| A11Y-09 | Minor (evidence) | `site/index.html:110-113` | The inline contrast note disagrees with recomputation for 2 of its 7 pairs, and omits the opacity that A11Y-01 depends on |
| A11Y-10 | Minor (claim) | `progress/ledger.json` ZOM-DISC-102 | Card is `done` while its criterion demands "keyboard/screen-reader verified; non-text contrast tested" and its own note says screen-reader/pixel contrast UNKNOWN |

### A11Y-01 — graph edges are effectively invisible

`site/index.html:57` declares `.dep-edge{stroke:#687381;opacity:.18}`. The
declared pair `#687381` on `#151922` is 3.65:1, which is what the PKG-102 note at
`:110-112` reports — but the rendered stroke is composited at 18 % opacity:

| State | Declaration | Composited colour on `#151922` | Ratio |
| --- | --- | --- | --- |
| default | `opacity:.18` | `#242933` | **1.21:1** |
| `show-links` | `opacity:.55` | `#434a56` | **1.97:1** |
| `show-links` support edge | `#e67b70` @ `.6` | `#925451` | 3.02:1 (borderline) |
| `.dim` | `opacity:.05` | `#191e27` | **1.05:1** |
| path focused up | `#8fb8ff` @ `.95` | `#89b0f4` | 8.02:1 |
| path focused down | `#f0b46a` @ `.95` | `#e5ac66` | 8.73:1 |

Prerequisite lines are the essential graphical information in this view, so
1.4.11 applies in the default state, not only while focused. The focused-path
colours pass; the resting and emphasised states do not. This is arithmetic from
declared values, not a pixel measurement, but opacity over a solid background is
deterministic — the composite is the rendered colour for the stroke's core
pixels (antialiased edges are weaker still).

### A11Y-02 — detail landmark loses its accessible name on selection

`site/index.html:148`:

```html
<aside id="detail" class="detail" aria-labelledby="detail-title" tabindex="-1">
  <h3 id="detail-title">Select a work item</h3>
```

`selectItem` at `:192` does `d.replaceChildren();d.append(el('h3', ...))` — the
new heading has no `id`, so `aria-labelledby="detail-title"` resolves to no
element and the `complementary` landmark becomes unnamed after the first
selection. The visible heading is also no longer programmatically the region's
name. Static first paint is correct, which is why the id-reference check in
`tests/test_site_accessibility.py` passes; the defect only exists after
interaction, so it needs the browser/AT run that this package does not perform.

### A11Y-03 — empty result breaks the list contract

`site/index.html:147` declares `<div id="items" role="list" aria-label="Work items">`,
and `render()` at `:211` appends `el('p','No work matches those filters.')`
directly to it when the filter matches nothing. A `role="list"` must own
`listitem` children (ARIA 1.2 required owned elements). A screen reader may
announce the list as empty and skip the message, or announce a malformed list.

### A11Y-04 — the roadmap is one large live region

`site/index.html:94` declares `<div id="milestones" aria-live="polite"></div>`;
`:451` appends one `<section class="card">` per milestone — five cards, each with
a heading, a progress sentence and a goal sentence. A live region that is filled
at load is announced in most screen readers, so the page's first announcement
can be the entire roadmap. The page already has concise status text
(`#count`, `#queue-count`), so this region adds noise rather than information.

### A11Y-05 — expanded map is an uncontained overlay

`site/index.html:33` gives `.dep-section.expanded{position:fixed;inset:0;z-index:100;overflow:auto}`
and `:412` toggles that class on the section while disabling body scroll. DOM
order is unchanged, so Tab from the overlay's own controls continues into the
queue/work sections that are visually covered. Escape only closes the overlay
when focus is **not** on a `.dep-node` (`:413`); on a card, Escape clears path
focus instead — documented, but it means a keyboard user inside the overlay has
no way to close it without knowing to leave the map first. `#dep-expand` also
exposes `aria-pressed` (`:97`) although it discloses/hides a view; `aria-expanded`
is the state AT expects for a disclosure.

### A11Y-06 — skip link target is not focusable and the label is imprecise

`:79` says "Skip to roadmap" but `href="#main"` targets `:86`, whose first
children are the live-status block and the evidence-boundary warning; the
roadmap heading is further down. `#main` has no `tabindex="-1"`, so focus
handling on activation depends on the browser's fragment-navigation behaviour
(modern Chrome/Edge/Firefox move the sequential focus start point; older or
different AT/browser combinations may not move focus or announce the region).
Not reproduced in a browser here — recorded as a robustness gap, not a proven
failure.

### A11Y-07 — card boundaries below 3:1 (at risk)

Computed from declared colours: node fill `#1d222c` against map background
`#151922` is **1.10:1**; node border `#3c4658` is 1.85:1; column dashed border
`#3a4354` is 1.87:1 against the page background; the de-emphasised node border
`#2b323d` is 1.36:1. Each card is identified by its own text, and state is
repeated in text (`milestone · owner · queue`) and in `aria-label`, so this is
recorded as at-risk rather than a proven 1.4.11 failure: it becomes a failure if
the boundary is judged necessary to identify the control or its extent. The
4 px state edge itself passes (5.04:1 to 8.63:1).

### A11Y-08 — duplicate zoom announcements

`:97` has `<output id="dep-zoom-level" aria-live="polite">100%</output>` and
`:343-344` writes `#dep-status` ("Map zoom 80% of natural size.") on the same
action. Both are polite status channels, so a screen reader may speak both.

### A11Y-09 — inline contrast note is not reproducible

`:110-113` claims `#8fb8ff` on `#202a3a` = 6.36:1 (recomputed **7.20:1**) and
`#f0b46a` on `#2e2719` = 6.95:1 (recomputed **8.06:1**); the other five pairs
match exactly. Both errors understate contrast, so no compliance risk — but the
note is not reproducible from the palette and its edge ratio ignores `opacity`,
which is exactly the gap A11Y-01 exploits.

### A11Y-10 — tracker card overstates its evidence

`progress/ledger.json` ZOM-DISC-102 is `state:"done"` with
`completionBasis:"...accessibility scaffolding..."`, while its `criterion` is
"keyboard/screen-reader verified; non-text contrast tested" and its own `note`
ends "...screen-reader/pixel contrast UNKNOWN." Per the project rule that
UNKNOWN is not PASS, this card evidences scaffolding, not its stated criterion.
Not a page defect; it is a claim-hygiene finding for the owner and reviewer.

## 5. Exact remediation

Changes below are **proposals only** — this package is read-only on
`site/index.html`. Each is scoped to one finding.

- **A11Y-01** — `site/index.html:57`: delete `opacity:.18` from `.dep-edge` and
  replace opacity-driven emphasis with stroke tokens that pass on `#151922`:
  `stroke:#7b8798` (4.82:1) default; `.dep-map.show-links .dep-edge{stroke:#98a5b6}`
  (7.03:1); `.dep-edge.dim{stroke:#606d80}` (3.35:1); keep `.up`/`.down` as is
  (8.02:1 / 8.73:1). Then update the note at `:110-113` to the new values and
  extend `tests/test_site_dependency_map.py` (or a pixel probe) to sample the
  rendered stroke, so the claim is tied to a measurement.
- **A11Y-02** — `site/index.html:192`: keep the id on the rebuilt heading, e.g.
  `const heading=el('h3',it.id+' · '+it.title);heading.id='detail-title';d.append(heading);`
  (or move `aria-labelledby` to a stable wrapper id). Re-test selection, then
  close the panel and confirm the landmark name is still present.
- **A11Y-03** — `site/index.html:211`: render the empty message outside the
  list, e.g. a sibling `<p id="items-empty" class="meta" role="status" hidden>`
  whose text is set in `render()`; or, if it must stay inside, wrap it in
  `role="listitem"`. Keep the live-region text short.
- **A11Y-04** — `site/index.html:94`: remove `aria-live="polite"` from
  `#milestones`; rely on `#count` / `#queue-count` for status text.
- **A11Y-05** — `site/index.html:97`, `:412-413`: expose `aria-expanded` on
  `#dep-expand` (and keep the label change), move focus to the map on open and
  back to `#dep-expand` on close, set `inert` (or `aria-hidden` + `inert`) on the
  sibling sections, `<header>`, and `<footer>` while expanded, and handle Escape
  globally so the overlay can always be closed. Alternative, cheaper: keep the
  expanded map in flow (drop `position:fixed; inset:0`).
- **A11Y-06** — `site/index.html:79`, `:86`: either add `tabindex="-1"` to
  `<main id="main">` so the fragment always receives focus, or point the skip
  link at `#roadmap-heading` (with `tabindex="-1"` on that heading) and keep the
  "Skip to roadmap" label accurate.
- **A11Y-07** — `site/index.html:43`, `:47`, `:55`: raise `.dep-node`
  `border-color` to `#606d80` (3.35:1 vs map, 3.03:1 vs node fill) and the
  `.dep-column` dashed border to `#606d80`; either raise the unrelated-node
  border to the same value or document that de-emphasised cards are identified
  by text only.
- **A11Y-08** — `site/index.html:97`: drop `aria-live` from `#dep-zoom-level`
  (leave the `<output>` as a visual readout) and keep the single announcement in
  `#dep-status`; do not do the reverse and remove the status sentence, because
  the percentage alone lacks context.
- **A11Y-09** — replace the hand-written ratios at `:110-113` with values
  generated from the audit matrix in `tests/test_site_accessibility.py`, and state
  that they are declared-colour arithmetic, not rendered pixels.
- **A11Y-10** — keep ZOM-DISC-102 `done` for the scaffolding, but amend its
  `criterion` to "accessibility scaffolding verified by static checks;
  screen-reader and rendered-pixel contrast UNKNOWN", or return it to `review`.
  Do not cite it as an accessibility pass.

## 6. Evidence and reproduction

Command (from the package worktree, `f766776` + this package):

```powershell
python -m unittest discover -s tests -p "test_site_accessibility.py" -v
```

Result: **23 tests, OK** (see the run log in the package hand-off). The suite is
offline and standard-library only; it never writes to `site/` and never starts a
browser, so it is safe on restricted hosts.

Package contents (`git diff --stat main` on `pkg/pages-a11y`): only
`tests/test_site_accessibility.py` and `docs/ACCESSIBILITY_REPORT.md`. No page
edit, no merge, no publish, no acceptance.

## 7. Reviewer checklist (E)

1. Confirm `git diff --stat main` lists exactly the two files above and no
   `site/` change.
2. Run the command in section 6 in the package worktree; confirm OK.
3. Confirm the UNKNOWN rows were not read as passes: no screen reader was run,
   no pixel was sampled, no 200% resize or forced-colours emulation happened.
4. Spot-check A11Y-01 (`:57`), A11Y-02 (`:148`, `:192`) and A11Y-04 (`:94`,
   `:451`) against the cited lines; each is reproducible from source alone.
5. Decide whether A11Y-01/02/03/04/05 need a follow-up site-fix package — they
   cannot be fixed under this branch's read-only rule, and A11Y-01/02 are the two
   that should block a "site is accessible" statement.
6. Confirm no merge, publish or acceptance happened in this package, and that
   `runtime_verified=false` / `acceptance=none` remain.

## 8. Scope and exclusions

- One page (`site/index.html`) at one revision (`f766776`); the published
  `gh-pages` copy was not inspected.
- One theme (dark, `color-scheme: dark`); no light theme exists to test.
- JavaScript-enabled load with a populated ledger (126 items, 5 milestones);
  the error path (`Tracker data unavailable`) was not audited.
- Excluded: launcher/desktop UI, release gate, ledger content correctness, and
  the browser-only checks that `tests/test_site_dependency_map.py` owns
  (map geometry, zoom/pan, 320 px reflow) — that suite skips rather than passes
  when Playwright/Chrome is unavailable.
