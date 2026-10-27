# Legal, licence and public-claim rules (AGENTS_LEGAL)

**Status:** project policy for agents working in this repository. This is **not legal
advice, not a legal opinion and not redistribution clearance**. The owner and a qualified
reviewer decide publication and licensing; agents produce evidence and bounded claims.

Read this file with the root [`AGENTS.md`](AGENTS.md). `AGENTS.md` remains the project
tracking/authority baseline; **this file does not replace or edit it**. Read the fixed-review
policy in `docs/REVIEW_POLICY.md` and the legal authorities listed below before making a
public, release, asset, screenshot, attribution or "cleared" claim.

## 1. Scope

This policy applies to every artifact an agent prepares or reviews, including:

- docs, README/Pages copy, CHANGELOG/release notes, PR descriptions and review records;
- public asset lists, icon maps, credits/attribution and `THIRD_PARTY_NOTICES.md`;
- replay galleries, screenshots, GIF/PNG/video captures and heatmap/SVG panels;
- telemetry summaries, evidence bundles, tables and dashboards that quote game content;
- package/build/receipt claims and any statement that something is "safe", "cleared",
  "accepted", "validated", "fixed", "legal" or "ready to publish".

The default stance is **evidence first, publish last**. A missing right is not a licence;
a missing test is not a pass; an absent field is `unknown`, not zero.

## 2. Authority and assumptions

Read authority in this order:

1. Owner instructions and repository policy in `AGENTS.md`, this file and
   `docs/REVIEW_POLICY.md`.
2. [`docs/PROVENANCE.md`](docs/PROVENANCE.md) — original authorship, permission basis and
   the private/local asset boundary (§3.4 and §4 are the operative limits).
3. [`reference/LEGAL_RIGHTS_AND_CREDITS.md`](reference/LEGAL_RIGHTS_AND_CREDITS.md) — rights
   matrix, open risks, attribution minima and ZOM-LEGAL-01/M4 mapping.
4. [`reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md`](reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md)
   — independent corrections to earlier licence/release claims.
5. Per-asset evidence in [`reference/FREE_ASSET_SOURCES.md`](reference/FREE_ASSET_SOURCES.md),
   [`docs/ICON_MAPPING.md`](docs/ICON_MAPPING.md) and
   [`configs/ui_icon_map.json`](configs/ui_icon_map.json).
6. Executable gates: [`launcher/release_gate.py`](launcher/release_gate.py) (privacy,
   personal paths, secrets, traceability) and the relevant project tests.

Assumptions that must stay explicit:

- The original ZOMBIEEE archive and all extracted/built original game content are **private,
  owner-supplied inputs**, not redistributable project assets.
- Warband/WSE2 binaries, native UI/item/font/sound assets and original scene/mission data
  have **no recorded redistribution right** for this project.
- "Free to download", "for the community", CC0 on a landing page, or a credits line do **not**
  by themselves establish a redistribution right for every file in a pack.
- Third-party embedded content (textures, HDRIs, fonts, sounds, community contributions) has
  its own terms; the containing pack's headline licence does not automatically cover it.
- Screenshots, frames, logs and bundles are **local evidence** until explicitly cleared;
  derived data may be publishable when it contains no native art/UI and no personal data.
- No agent may self-review its own build, or review a peer builder's work as if that were
  independent review; the fixed-reviewer model is in `docs/REVIEW_POLICY.md`.
- An observed check is not acceptance; a merge is not publication; publication is not a
  legal clearance.

## 3. Evidence classes and required record

Every licence/claim assertion needs a record that a second reviewer can follow. Use one of:

| Class | Meaning | Minimum record |
| --- | --- | --- |
| **Project-authored** | Written by this project, no third-party asset copied | Path, author/owner, date, scope; no external grant implied |
| **Licence-cleared candidate** | Exact source page + licence/permission read for the item | Source URL, page/API observation date, author, licence name/version, attribution, modifications, download/SHA status |
| **Native / third-party game asset** | TaleWorlds, original ZOMBIEEE, OSP or other third-party content | Rights-holder, source, permission state; default **do not bundle** |
| **Derived data** | Project-authored numbers/geometry computed from sealed evidence | Input bundle id/SHA, transformation, artifact path, privacy check; no native art/UI |
| **External reference** | Literature, community post, upstream repo or documentation | URL, retrieval date, what it establishes and what it does **not** establish |
| **Unknown** | No adequate evidence | State `UNKNOWN`/`BLOCKED`; never fabricate a licence or a zero |

Golden rule: **no claim without the record**. A page title, a search hit or an AI summary is
not licence evidence. Preserve the source URL and observation date; do not paste personal
paths, account data, tokens or full third-party binaries into committed docs.

## 4. Procedures

### 4.1 Classify before drafting

Name the artifact type (code/docs, 3D/2D asset, font/sound, native capture, derived visual,
telemetry table, external quote) and the rights holder. If you cannot name the rights
holder, you cannot make a licence claim.

### 4.2 Assemble the evidence packet

- Exact source URL(s) and page/API read date.
- Author/rights-holder and licence name/version (or "no recorded right").
- What the licence permits: modify, redistribute, attribution, share-alike, non-commercial,
  no-derivatives, embedded-content caveats.
- Download state and SHA-256 if a file was obtained; `not downloaded` is a valid state.
- The specific files actually used — not just the bundle/collection name.
- Any required notice/attribution text and the intended placement.
- For captures: build/probe SHA, map/scene, spectator/overview state, frame provenance and
  written-permission status.

### 4.3 Apply the publication gate

A public artifact may include only:

1. project-authored material covered by the project's own publication decision;
2. third-party material with a recorded licence/permission **for that exact item** and
   complete attribution/notices;
3. derived numeric/vector analysis with no native art/UI, no personal data and an explicit
   `derived` caption.

It may **not** include raw gameplay frames, native screenshots, extracted models/textures,
sounds, fonts, compiled mission data or original scene assets merely because they were
downscaled, cropped, HUD-name-stripped, credited, or labeled "no ownership claim".

Before a binary/asset PR, require owner approval, fixed-reviewer clearance, a
`THIRD_PARTY_NOTICES.md` row and the required screenshots/tests. Until then, text/definitions
only.

### 4.4 Write bounded claim wording

Use the strongest wording the evidence supports, never stronger:

| Evidence state | Allowed wording | Forbidden wording |
| --- | --- | --- |
| Observed in a sealed run | "observed in run X, probe/build Y" | "fixed", "working", "accepted" |
| Derived from sealed samples | "derived descriptive data; no visual validation" | "proves", "validates behaviour", "tactical result" |
| Licence page read | "licence page read on DATE; asset not downloaded" | "cleared", "safe", "free to redistribute" |
| No evidence | "UNKNOWN" / "gap" | "zero", "none", "not present" |
| Review pass for a bounded scope | "PASS for scope X; no acceptance" | "approved", "legal clearance", "ready to publish" |

Do not use "fair use", "commentary exception", "public domain" or "no ownership claim" as a
substitute for a permission record. Do not claim endorsement by TaleWorlds, the original
ZOMBIEEE team, WSE2 authors or asset sites.

### 4.5 Review and handoff

- The **builder** assembles the evidence packet and states `PASS`/`BLOCKED`/`UNKNOWN` only
  for its own implementation facts; it does not self-review.
- The **fixed reviewer** checks sources, regex/gates, fixtures, wording and privacy; returns
  `PASS`, `BLOCKED` or `UNKNOWN` with exact findings and no merge authority.
- **Lead/owner** decides merge/publication. A reviewer PASS is not acceptance.
- Record artifact path, source/date, exclusions, gate/test evidence, reviewer verdict and the
  next owner/action. Use `<temp>`/relative placeholders in committed docs — never absolute
  user paths.

## 5. Common failures to catch

| Failure | Bad pattern | Required correction |
| --- | --- | --- |
| **IP overclaim** | "CC0 pack, so every file is cleared"; "free to download"; "public domain" from a search hit | Name the exact item and its own licence; treat embedded textures/HDRI/community assets separately; otherwise `UNKNOWN`/`BLOCKED` |
| **Raw captures** | Publish a gameplay GIF/PNG because it is downscaled, HUD-name-stripped, credited or labeled "no ownership claim" | Keep raw captures private; publish derived occupancy/flow data with no native art/UI, or obtain written permission first |
| **Licence evidence** | Page title/SHA-pending/landing-page statement treated as a download entitlement | Record URL + date + author + licence + exact files + download/SHA state; per-asset checks for embedded content |
| **Acceptance wording** | "validated", "fixed", "legal", "approved", "ready" after tests or a merge | State observed evidence and scope; use `PASS for bounded scope`, `UNKNOWN`, `BLOCKED`; leave acceptance/publication to owner |
| **Privacy/provenance** | Absolute user paths, screenshots/logs with account data, mixed build/probe SHA between A/B sides | Relative/private placeholders; scrub paths/serials; label every run's build/probe/formation/parameter |
| **Builder self-review** | Builder marks its own branch PASS or asks a peer builder to "approve" | Route to fixed reviewer; builder keeps building; no self/peer acceptance |
| **Gate bypass** | Allowlisting a whole directory to hide a new leak; ignoring a failing test due "known" blockers | Exact justified exemptions; update tests to expect only named blockers; keep real gate failing closed |

## 6. Evidence and gates

- **Privacy/secret gate:** `launcher/release_gate.py`; failures include
  `no_personal_local_paths`, `no_obvious_secrets`, `traceability_head_revision`.
- **Release/traceability gate:** same gate plus `VERSION`, `CHANGELOG`, release traceability
  and ancestry checks; a clean metadata check is not gameplay acceptance.
- **Asset/UI gates:** `docs/ICON_MAPPING.md` §4.6/§10, `reference/FREE_ASSET_SOURCES.md`
  §3.7–§3.9, `configs/ui_icon_map.json` (`screenshotValidation`, `revision`,
  `task64Review`, attribution rules).
- **Notices:** create `THIRD_PARTY_NOTICES.md` from the icon/asset register before the first
  binary asset PR; include author, source URL, licence/version, date and changes.
- **Public Pages:** derived-only replay/heatmap content; no raw clips; preserve
  attribution/no-IP/takedown wording and the pending A/B gate.
- **Original-source closure:** per-asset provenance/permission matrix for issue #5; do not
  treat a credits line as a blanket licence.

## 7. Handoff template

```text
Artifact: <path(s)>
Rights class: project-authored | licence-cleared candidate | native/third-party | derived | external reference | unknown
Source evidence: <URL(s), page/API read date, author, licence/version, download/SHA state>
Exclusions/caveats: <embedded assets, native captures, personal data, unverified fields>
Changes/attribution: <what was modified; notice text/placement>
Gate evidence: <tests, privacy scan, probe/build SHA, reviewer verdict>
Status: PASS for scope <...> | BLOCKED (<reason>) | UNKNOWN (<gap>)
Next action/owner: <Lead/owner/fixed reviewer; no acceptance claimed>
```

## 8. File map

| Path | Use |
| --- | --- |
| `AGENTS.md` | Project tracking/authority baseline; do not edit for this policy |
| `AGENTS_LEGAL.md` | This legal/claims addendum |
| `.agents/skills/legal-claims-and-licences/SKILL.md` | One-skill guard against legal/claim mistakes |
| `docs/PROVENANCE.md` | Original authorship, owner attestation, §3.4 authorization limits, §4 local asset/screenshot boundary |
| `reference/LEGAL_RIGHTS_AND_CREDITS.md` | Rights matrix, open risks, attribution/notices, ZOM-LEGAL-01 |
| `reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md` | Independent licence/release corrections |
| `reference/FREE_ASSET_SOURCES.md` | Candidate asset catalogue, §3.7–§3.9 evidence register and embedded-asset caveats |
| `docs/ICON_MAPPING.md` / `configs/ui_icon_map.json` | Icon/reticle licences, native boundaries, screenshot/attribution gates |
| `launcher/release_gate.py` | Privacy/secret/traceability gate (real checkout may be blocked by known path/head debt) |
| `THIRD_PARTY_NOTICES.md` | Required generated attribution register before first binary asset PR (may be absent now) |
| `site/` | Public Pages; derived-only gallery wording, no raw captures |
| `progress/ledger.json` | Tracking data, not legal authority or acceptance |

## 9. Minimum checklist

- [ ] Rights holder and exact artifact identified; no bundle-level blanket assumption.
- [ ] Source URL/date/author/licence and download/SHA state recorded; embedded content checked.
- [ ] No native/raw capture in the public artifact; derived data has no native art/UI/personal data.
- [ ] Attribution/notices and modifications recorded; `THIRD_PARTY_NOTICES.md` gate respected.
- [ ] Wording uses observed/UNKNOWN/BLOCKED/PASS-for-scope; no acceptance or legal-clearance claim.
- [ ] Fixed reviewer (not builder) returned PASS/BLOCKED/UNKNOWN with evidence.
- [ ] Lead/owner retains merge/publication decision; no self-review, no silent allowlist.
- [ ] Privacy scan/paths checked; committed docs use relative/private placeholders.

**One-line lesson:** evidence defines the claim; if the exact permission is missing, publish
derived data or nothing — never a raw capture and never an acceptance/legal claim.
