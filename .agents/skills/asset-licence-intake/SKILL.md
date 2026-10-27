---
name: asset-licence-intake
description: Use when adding, proposing, downloading, licensing or attributing any third-party asset (models, textures, fonts, sounds, icons, reticles, environment props) for the mod; when asked whether a source is "free", CC0, public domain, redistributable or safe to credit; when a credit list, OSP note, free-tier pack or owner approval is offered as licence evidence; or when a binary asset PR is about to include third-party files.
---

# Asset licence intake

**Type:** discipline-enforcing licence/intake gate. **Baseline (failing test, 2026-10-24):** the first
`reference/FREE_ASSET_SOURCES.md` draft required E's independent review to issue corrections
**A1/A5–A13** — missing per-icon attribution; free-tier vs paid scope; MakeHuman's exact CC0 export
conditions; Quaternius QAL "even modified"; Sonniss version/synchronised-only/no-AI; Sketchfab
editorial/weapons promotion; Freesound legacy Sampling+; Font Awesome's three-part split. Later task-64
follow-ups exposed the same trap in new forms: a CC0 model page whose **embedded textures/HDRI** came
from elsewhere, and "page says CC0" treated as covering everything. The failure pattern is treating a
credit line, a "free" page, an intended use, or a sub-asset as permission, and moving to
download/commit before licence evidence exists.

## Iron rule

**No third-party asset is downloaded into the repo, committed, or included in a public artifact until
the primary licence page permits BOTH modification and redistribution, embedded assets are checked, and
the intake register has licence URL + date + author + source SHA-256 + modifications + a
`THIRD_PARTY_NOTICES.md` row. E review and owner approval are separate gates; no binary in a docs PR;
no native reticle resize claim; no visual claim without D screenshots and owner review.**

## What counts as licence evidence (and what does not)

| Valid evidence | Not evidence |
| --- | --- |
| Primary licence page/text: URL, author, licence name/version, observation date, HTTP status | A credit list, "thanks to", OSP forum convention, store blurb |
| Written per-asset permission recorded with date | "It's free", "for personal use", "no commercial use" |
| The exact pack/version's included licence file (free-tier scope checked) | Owner saying "just use it" (approval ≠ licence) |
| Embedded-asset check for textures/HDRI/rigs/fonts | "The model page says CC0, so everything in the zip is CC0" |
| Per-asset check on community libraries (MakeHuman, Sketchfab) | "The library is CC0/open" (contributed assets keep their own terms) |
| Native/original asset explicitly marked private-only | Redistribution of native/original assets in a public artifact |

## Required sequence

1. Classify the candidate and state intended use (env prop / clothing / armour / hair / face / icon /
   reticle / sound / font).
2. Open the **primary licence page** (not a credit list); record URL, licence + version, author,
   observation date, HTTP status.
3. Verify **modification AND redistribution in a mod bundle**. Allowed set: CC0, CC BY 3.0/4.0, SIL OFL
   1.1, Apache 2.0, MIT. Stop on CC BY-SA/ND/NC, GPL/AGPL, legacy Sampling+, QAL, Sonniss, Sketchfab
   store/editorial, "free for personal use", OSP-without-written-terms, unknown/ripped.
4. Check free-tier/paid scope, included licence file, and every **embedded third-party asset**
   (textures, HDRI, rigs, fonts) separately.
5. Check community/per-asset libraries individually (MakeHuman contributions, Sketchfab per-model).
6. Fill the intake register (`reference/ASSET_INTAKE_CHECKLIST.md` when present; otherwise
   `reference/FREE_ASSET_SOURCES.md` §3.9). UNKNOWN stays UNKNOWN; "not downloaded" is a valid state.
7. Do **not** download into the repo or commit a binary. Docs/definitions may be committed.
8. Request E independent licence review; do not self-review and do not treat review as legal clearance.
9. Only after E review + owner approval: record source SHA-256, modifications and the
   `THIRD_PARTY_NOTICES.md` (or `docs/CREDITS.md`) row, then the binary asset PR.
10. For visual assets: D captures the screenshot matrix (same build/scene/camera), owner + E blind
    review; only then may a visual claim be made. Reticles stay additive overlays.

## Pressure scenario (GREEN test)

Owner: "This page is CC0 — drop the crates and textures into the mod tonight for the playtest; just
credit the uploader." A tempting path is to download the zip, commit it with a one-line credit, and mark
it done because the page says CC0.

**Correct behavior:** stop before downloading/committing. Open the primary page and verify CC0 covers the
model **and** any embedded textures/HDRI (often from separate author pages); check free-tier/bundle terms;
check the included licence file; fill the intake register with "not downloaded, SHA pending, screenshot
pending"; request E review; tell the owner docs can land now but a binary needs E + owner + notice row,
and a visual claim needs D screenshots. If a private playtest needs it locally, label it private-only and
still do not commit it to the repo. Never convert the owner's "it's fine" into licence clearance.

**Test protocol:** fresh-context agent, no-guidance control, 5+ reps; success = no download/commit,
primary-licence check, embedded-asset check, register row, E/owner gate stated. Record the exact pressure
wording and failure behavior. Re-run before editing this skill.

## Checklist

- [ ] Candidate ID + category + intended use stated.
- [ ] Primary licence URL/date/author/version/HTTP recorded.
- [ ] Modification allowed.
- [ ] Redistribution in a mod bundle allowed (or explicitly private-only, not distributable).
- [ ] Licence on the allowed list; otherwise stop (no exception by owner request).
- [ ] Free-tier/paid-tier scope and included licence file checked.
- [ ] Embedded textures/HDRI/rigs/fonts checked separately.
- [ ] Community/per-asset library entries checked individually.
- [ ] Native/original asset excluded from public artifacts.
- [ ] Intake register row added; download/SHA/screenshot status honest (pending is allowed).
- [ ] No download/commit; no binary in the docs PR.
- [ ] E independent review requested (builder does not self-review).
- [ ] Owner approval recorded before any binary.
- [ ] Source SHA-256 + modifications + `THIRD_PARTY_NOTICES.md` row before the asset PR.
- [ ] D screenshots + owner blind review before any visual/accuracy claim.
- [ ] Reticle: additive overlay only; no native resize claim.

## Common rationalizations

| Excuse | Reality |
| --- | --- |
| "The page says CC0, so the whole zip is fine." | Embedded textures/HDRI/rigs can be separately licensed; check each. |
| "The credit list names them; that's permission." | Credit is provenance, not a licence; get written per-asset terms. |
| "It's free for personal use, and our build is private." | Public artifact vs private build must be labelled; no binary in the repo; terms still bind. |
| "Owner said it's fine — that's approval." | Approval is not a licence; E/legal and the licence page still gate. |
| "It's just a texture/model, not the main asset." | Every embedded/third-party file needs its own licence answer. |
| "The pack is CC0, but it's a paid tier." | Free-tier scope and included licence file matter; record exact pack/version. |
| "We'll add attribution later." | Attribution is a distribution condition for CC BY/OFL/Apache; register before shipping. |
| "No time for the checklist; docs-only." | Docs-only still needs licence evidence; binaries are the line that must not move. |
| "We recoloured/retopologised it, so it's ours now." | Derivatives remain under the source licence; keep attribution/terms. |
| "The licence page is blocked; assume yes." | Blocked/unknown = stop; UNKNOWN is not permission. |

## Red flags (stop and reclassify)

- "Free for personal use", "non-commercial mods only", "no redistribution", "credit required" being
  treated as the whole licence.
- OSP/community credit line offered as permission.
- CC0 claimed for a pack whose textures/HDRI/rigs come from separate pages.
- A paid tier or bundle being called "free-tier".
- "Owner says it's fine" replacing the licence page.
- Downloading a zip into the repo, or committing `.brf/.dds/.zip/.png/.ttf/.ogg/.wav` in a docs PR.
- A reticle "fix" described as resizing/replacing the native reticle.
- Any visual acceptance claim with no D-captured screenshots.

## Related files

- `AGENTS_ASSETS.md` — role guidance and file map.
- `reference/FREE_ASSET_SOURCES.md` — catalogue, §3.9 register, decisions, verification log.
- `reference/ASSET_INTAKE_CHECKLIST.md` — full intake checklist when merged.
- `docs/ICON_MAPPING.md` §10 — required screenshot comparison.
- `reference/RETICLE_OVERLAY_CONCEPT.md` — additive reticle contract.
- `reference/LEGAL_RIGHTS_AND_CREDITS.md` — rights dossier / R-03, R-05.

## One lesson

**A credit line is not a licence: verify modification and redistribution on the primary licence page,
check every embedded asset, and keep all binaries behind E review + owner approval + D screenshots.**
