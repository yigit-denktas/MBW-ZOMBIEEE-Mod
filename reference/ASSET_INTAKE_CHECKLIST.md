# Asset intake checklist (task-64 follow-up)

**Status:** process checklist only. **No asset is downloaded or committed**, no game launch, no visual
or acceptance claim. This is how a licence-cleared candidate becomes a binary asset PR.
**Observed:** 2026-10-24, branch `agent/g-asset-batch2` (stacked on task-64 follow-ups, PR #52).
**Related:** [`reference/FREE_ASSET_SOURCES.md`](FREE_ASSET_SOURCES.md) §1/§3.9/§6/§7,
[`reference/RETICLE_OVERLAY_CONCEPT.md`](RETICLE_OVERLAY_CONCEPT.md) §3.1/§4,
[`docs/ICON_MAPPING.md`](../docs/ICON_MAPPING.md) §10,
[`reference/LEGAL_RIGHTS_AND_CREDITS.md`](LEGAL_RIGHTS_AND_CREDITS.md).

A candidate may become a binary asset PR **only when every box below is filled** and the E/owner gates
pass. Unknown stays unknown; an empty box stops the candidate.

---

## A. Identification

- [ ] Candidate ID + category (environment prop / clothing / armour / hair / face / icon / reticle / sound / font).
- [ ] Source URL + author/uploader + page title.
- [ ] Licence name + version + licence URL; observation date; HTTP status at observation.
- [ ] Source file(s), formats, size, poly/tri counts, texture resolutions, animations/rig notes.
- [ ] Intended use (scene prop / item / UI icon / reticle overlay / sound / font).

## B. Licence gate

- [ ] Modification **and** redistribution in a mod bundle are allowed; allowed set is **CC0, CC BY
      3.0/4.0, SIL OFL 1.1, Apache 2.0, MIT** (per the catalogue §1/§7).
- [ ] No CC BY-SA/ND/NC, GPL/AGPL, legacy Sampling+, Quaternius QAL, Sonniss, Sketchfab
      store/editorial, "free for personal use", unknown/custom licence.
- [ ] Embedded third-party content checked separately (textures, HDRI, fonts, rigs, scripts).
- [ ] No native/original Warband/ZOMBIEEE asset is used for a public artifact (private build
      reference only; legal dossier R-03/R-05).
- [ ] CC BY: attribution string + licence link + changes recorded; CC0: courtesy provenance recorded.
- [ ] OSP/community credit text is **not** treated as a licence; written per-asset terms required.

## C. Engine fit (Warband)

- [ ] Mesh: OBJ/FBX → OpenBRF; scale/orientation; collision mesh; skeleton/rig compatibility; item or
      scene-prop wiring.
- [ ] Textures: DDS DXT1/DXT3/DXT5; dimensions multiple of four; PBR maps reduced to
      diffuse/normal/specular.
- [ ] UI: presentation mesh entry; 1000×1000 virtual canvas; tint/alpha; DDS alpha.
- [ ] Sounds: `.ogg`/`.wav`; new `module_sounds.py` id (never overwrite hard-coded native ids).
- [ ] Fonts: OFL notice; `font_data.xml` + `font.dds`; glyph coverage test.

## D. Provenance evidence

- [ ] SHA-256 of the source download + licence snapshot/date.
- [ ] Modifications list (convert/rescale/retopo/recolour).
- [ ] `THIRD_PARTY_NOTICES.md` row: asset, author, source URL, licence + version, date obtained,
      changes (primary; `docs/CREDITS.md` alternative).
- [ ] **No binary committed before owner approval**; private evidence stays under `local/`/`evidence/`
      (gitignored, never uploaded).

## E. Validation gates

- [ ] E independent licence review (no self-review; builders do not evaluate peers).
- [ ] Owner approval of use and distribution model.
- [ ] D captures in-game screenshots + owner blind review for visual assets (ICON_MAPPING §10).
- [ ] Additive overlay only; **no native reticle resize claim**.
- [ ] Receipt records build SHA + screenshot hashes; no acceptance or legal clearance.

## F. Stop conditions

- Any unknown licence → stop.
- Any embedded third-party asset unclear → stop.
- Any native/original asset for a public artifact → stop (private-only).
- Any visual claim before D screenshots + owner review → stop.
- No binary in this repo while any box above is empty.
