# Assets, licences, cosmetics, icons, reticles

**Status:** project guidance, not acceptance evidence. This file is the shared operating note for
third-party asset sourcing, intake, attribution and the cosmetics/icon/reticle layer. It does not
authorize installs, builds, game launches, downloads or public claims. Licence clearance is E/owner
work; visual acceptance needs D screenshots and owner review.

## Scope

Covers weapons, clothing/armour, character/cosmetic meshes, faces/hairstyles, environment/cover props,
UI icons, reticles/overlays, fonts, textures and sounds: licence verification, attribution, intake
evidence, adopt/adapt/avoid decisions and the definitions-only icon contract. It does not cover
environment/map layout (see `AGENTS_ENVIRONMENT.md`), combat behavior (`AGENTS_AI_COMBAT.md`),
telemetry (`AGENTS_TELEMETRY.md`), or legal clearance (`AGENTS_LEGAL.md`).

## Assumptions (verify before relying on them)

1. **Native/original assets are private-only.** Original ZOMBIEEE, OSP and Warband content has no
   recorded redistribution right; a public/clean-room artifact needs licence-cleared replacements or
   omission (`reference/LEGAL_RIGHTS_AND_CREDITS.md`, R-03/R-05). The private/local build may reference
   installed assets but must never capture them into the repo or evidence bundles.
2. **A credit line is not a licence.** OSP credits, "thanks to X" and author names are provenance, not
   permission. Written per-asset terms are required.
3. **A "free" page is not automatically redistributable.** Several popular sources allow use in a
   product but forbid distributing the assets as assets; an unpacked Warband module is an asset
   collection. Custom licences (Quaternius QAL, Sonniss EULA, Sketchfab store) are treated as unsuitable
   for a bundle unless owner + legal review says otherwise.
4. **Free-tier scope matters.** CC0 free tiers can be commercial/no-attribution, but paid tiers and
   bundled third-party content may have different terms; record the exact pack/version and check its
   included licence file.
5. **Embedded assets are separate.** A CC0 model page can contain textures/HDRI/rigs from other pages
   (seen with an OGA crate/barrel upload); their licences must be checked independently.
6. **Community libraries are per-asset.** MakeHuman core source/data has AGPL/CC0-export conditions, but
   user-contributed clothes/hair/skins keep their own author licences. Check each asset page.
7. **Warband pipeline constraints bind every candidate:** OBJ/FBX→OpenBRF, DDS DXT1/DXT3/DXT5 with
   dimensions multiple of four, item/scene wiring, UI mesh/presentation entries, `module_sounds.py`
   ids and `font_data.xml`/`font.dds`.
8. **Visual validation requires in-game screenshots.** No icon, cosmetic, prop or reticle visual claim
   is valid without D-captured screenshots and owner review; the reticle layer is additive only and
   must never be described as a native reticle resize.
9. **Builders do not evaluate peers.** Source the evidence; E reviews licences; Lead/owner decide. Do
   not self-approve or review another builder's package.

## Procedures

### Candidate intake (before any download or commit)
1. Classify the candidate (environment prop / clothing / armour / hair / face / icon / reticle / sound /
   font) and state intended use.
2. Open the **primary licence page** (not a credit list or store blurb); record URL, licence name +
   version, observation date, HTTP status and author.
3. Verify **modification and redistribution** are allowed; allowed set is CC0, CC BY 3.0/4.0, SIL OFL
   1.1, Apache 2.0, MIT. Reject/stop on CC BY-SA/ND/NC, GPL/AGPL, Sampling+, QAL, Sonniss, Sketchfab
   store/editorial, "free for personal use", OSP-without-written-terms, unknown/ripped.
4. Check free-tier/paid-tier scope, extra terms, and **embedded third-party content** separately.
5. Fill the intake register (`reference/ASSET_INTAKE_CHECKLIST.md` when present; otherwise
   `reference/FREE_ASSET_SOURCES.md` §3.9) with licence evidence, download/SHA status, screenshot status
   and gate. UNKNOWN stays UNKNOWN.
6. Do **not** download into the repo, commit a binary, or add a build/install artifact. Docs/definitions
   may be committed.
7. Request E independent licence review. Do not self-review and do not treat review as clearance.
8. Only after E review + owner approval: add source SHA-256, modifications list and a
   `THIRD_PARTY_NOTICES.md` (or `docs/CREDITS.md`) row; then the binary asset PR.
9. For visual assets: D captures the screenshot matrix (same build/scene/camera), owner + E blind review;
   record hashes; only then may a visual claim be made.

### Cosmetics / icon layer
1. Keep inventory item icons (3D item meshes) separate from the kill-feed/HUD/reticle sprite contract.
2. Add slots only through `configs/ui_icon_map.json` with author + licence + licence URL + page URL +
   attribution; validate JSON and cross-references.
3. Icons are white-on-transparent, DXT5, multiple-of-four atlas pages; attribution register generated
   from the JSON before any CC BY icon ships.
4. Reticle work is an **additive overlay candidate** only; variants and measurements stay in the concept
   doc; no native-resize claim.

### Attribution
Keep exact strings: game-icons "Icons made by {author}. Available on https://game-icons.net" + licence
link + changes; Font Awesome CC BY 4.0 attribution + header; OFL notice for fonts; CC0 courtesy credit
optional; Freesound CC BY format; `THIRD_PARTY_NOTICES.md` row per asset with author/source/licence/
version/date/changes. Native-asset and no-endorsement statements stay in the public notice.

## Evidence and gates

| Claim | Minimum evidence | Gate |
| --- | --- | --- |
| Candidate is licence-cleared for docs | primary licence URL + date + author + modification/redistribution answer; register row | E independent review; owner decision for public use |
| Candidate is cleared for a binary asset PR | above + source SHA-256 + modifications + notice row + owner approval | no binary before all fields filled |
| Icon/reticle mapping is defined | valid `configs/ui_icon_map.json`; 0 missing licence fields; attribution register plan | no visual claim until D screenshots |
| Visual asset is acceptable | in-game screenshot matrix (build SHA, camera, backgrounds, resolutions) + blind owner/E review | no acceptance from docs; owner sign-off |
| Private/local build uses native content | explicit private-only label; nothing captured in repo/evidence | never a public bundle |
| Reticle overlay works | additive overlay screenshots; no native resize claim | owner review; D capture |

## Common failures

| Symptom | Likely cause | Required response |
| --- | --- | --- |
| Licence recorded from a credit list or store blurb | treated credit as licence | reopen primary licence page; record URL/date; stop if no terms |
| Binary/texture committed before approval | skipped intake gate | remove binary; record provenance; restart intake; no history rewrite as "approved" |
| "Page says CC0" but embedded textures/HDRI unclear | embedded third-party content | check each embedded asset; stop or exclude the unclear parts |
| Free-tier asset mixed with paid/bundled content | ignored pack scope/licence file | record exact pack/version; check included licence; re-scope |
| OSP/community credit used as permission | credit ≠ licence | written per-asset terms or stop |
| MakeHuman community asset assumed CC0 | core licence ≠ per-asset licence | check the asset page; only CC0-qualified exports |
| Native/original prop planned for a public build | ignored R-03/R-05 | replace or omit; private-only label |
| Retextured/recoloured asset "becomes ours" | derivative still under source licence | keep licence/attribution; no relicensing |
| Visual claim without screenshots | skipped owner/D gate | withdraw claim; request D capture + owner review |
| Reticle described as "resized/native" | overlay confused with engine UI | reword to additive overlay; no native-resize claim |

## Handoff / review

Handoff includes: candidate IDs/sources/licence evidence (URL + date + HTTP status), adopt/adapt/avoid
decision, download/SHA status (normally not downloaded), modifications, embedded-asset checks, screenshot
status, exact docs/JSON changed, tests/validation run, and explicit gaps. E reviews licences
independently; Lead/owner approves and merges; builders do not review peers or self-approve. Private
evidence stays under `local/`/`evidence/` (gitignored). No install, build, launch or public claim is
authorized by this file.

## File map

| Path | Purpose |
| --- | --- |
| `AGENTS_ASSETS.md` | this guidance |
| `.agents/skills/asset-licence-intake/SKILL.md` | focused licence/intake discipline skill |
| `reference/FREE_ASSET_SOURCES.md` | licence catalogue, decisions, register, verification log |
| `reference/ASSET_INTAKE_CHECKLIST.md` | intake checklist (pending merge; use this skill's checklist meanwhile) |
| `docs/ICON_MAPPING.md` | icon/event/currency/reticle mapping, native-atlas risk, screenshot plan |
| `configs/ui_icon_map.json` | definitions-only slots/events/candidates (no binaries) |
| `reference/RETICLE_OVERLAY_CONCEPT.md` | additive reticle variants, geometry, evidence status, test matrix |
| `reference/LEGAL_RIGHTS_AND_CREDITS.md` | rights dossier, R-01…R-15, publication models |
| `docs/PROVENANCE.md` | original authorship, permission and archive provenance |
| `THIRD_PARTY_NOTICES.md` / `docs/CREDITS.md` | future attribution register (create before first binary asset PR) |
| `docs/ICON_MAPPING.md` §10 | required in-game screenshot comparison plan |
