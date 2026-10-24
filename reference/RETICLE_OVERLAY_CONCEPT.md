# Reticle / overlay concept (project-authored candidate + licence-cleared alternatives)

**Status:** concept and validation plan only. **No binary asset exists**, no atlas/BRF/DDS/presentation
has been produced, no game launch was performed, and **no visual claim is made**. Visual/asset
validation requires E licence review **and** in-game screenshots captured by D (owner/Lead requirement);
until then nothing here is accepted or shipped.
**Observed:** 2026-10-24, branch `agent/g-asset-candidates`, owner task-64 follow-up (Lead request).
**Related:** [`docs/ICON_MAPPING.md`](../docs/ICON_MAPPING.md) §4.6 and §10 (screenshot comparison plan),
[`reference/FREE_ASSET_SOURCES.md`](FREE_ASSET_SOURCES.md) §3.7–§3.8 (props/cosmetics),
[`configs/ui_icon_map.json`](../configs/ui_icon_map.json) (`reticle` slot),
[`reference/LEGAL_RIGHTS_AND_CREDITS.md`](LEGAL_RIGHTS_AND_CREDITS.md) (rights gate).

**Routing.** The reticle is a **UI asset/presentation** concern, not telemetry: C owns readback, A owns
fire-mode/accuracy tuning (task-59), G owns asset licensing/candidates, E reviews licences, D captures
screenshots, Lead/owner approve. Width/accuracy behaviour is gameplay tuning — this concept only
defines an **additive overlay sprite** and how to validate it.

---

## 1. Why an additive overlay (not a native reticle resize)

- Warband's native reticle/crosshair is **engine-owned**; we have no verified engine hook to resize or
  replace it, and must not claim one. A safe first step is an **additive presentation overlay** drawn
  above the native HUD.
- The overlay can express a *presentation* of spread/state (e.g. scale a ring by a value supplied by
  gameplay), but the concept does **not** assert that it matches hit probability or that the native
  reticle is changed. Any claim beyond "an overlay texture was drawn" needs D screenshots + A/C data.
- **Double-reticle risk:** if the native reticle remains visible, the overlay must be distinguishable
  (lighter tint/position) or the design must wait for an engine-supported suppression path (unverified).
  This is an explicit open question, not assumed solved.

---

## 2. Project-authored concept (preferred; zero third-party licence)

All geometry is **our own** (simple line/ring primitives); no third-party SVG/PNG is copied. Authoring
tools (Inkscape/Blender) do not add asset obligations to the exported art.

### 2.1 Master specification

| Property | Value |
| --- | --- |
| Master canvas | 64 × 64 px, transparent background, white `#FFFFFF` foreground |
| Coordinate origin | exact centre (32,32) at 64 px |
| Stroke | 2 px minimum; no anti-aliased hairlines below 2 px |
| Centre dot | 2 × 2 px (at 64 px) |
| Arm layout | 4 arms at 90°, length 10 px from gap edge to tip, gap radius 6 px from centre |
| Variants | **A** classic cross (4 arms + dot), **B** tick/chevron (4 short ticks + dot, lower clutter), **C** ring + dot (1.5–2 px ring + dot) |
| Display sizes | 64, 48, 32 px (16 px only for compact HUD; must pass legibility check) |
| Colour | white glyph; runtime tint via `overlay_set_color`; empty/reload state may tint amber/red **only if** readability on bright/blood-red backgrounds is proven |
| Alpha | uniform, no soft gradient needed; DXT5 for alpha safety |
| Atlas slot | `ui_zdr_reticle` plus optional variants `ui_zdr_reticle_a/b/c`; optional separate spread ring `ui_zdr_reticle_spread` |
| Source form | authored vector (SVG/Blender) kept outside the repo until a licence-cleared asset PR |

### 2.2 Optional spread ring (presentation only)

- A separate ring sprite scaled by a **gameplay-supplied** factor; the concept does not define that
  factor and makes no accuracy claim. If A's tuning does not expose a value, ship the static variants
  only.
- Ring stroke 1.5–2 px, diameter variants; must not overlap the kill feed or obscure targets.

### 2.3 Integration notes (Warband)

- UI images are **mesh entries** in `module_meshes.py` drawn with `create_mesh_overlay`; presentation
  space is the verified 1000×1000 virtual canvas (see `docs/ICON_MAPPING.md` §2).
- Textures are **DDS**; alpha textures DXT3/DXT5; dimensions must be a multiple of four.
- Tint/alpha via `overlay_set_color`/`overlay_set_alpha`; no engine patch, no native asset copied.
- Source art must remain available for future skins; do not commit binaries in this docs phase.

---

## 3. Licence-cleared alternatives (candidates only)

| Candidate | Source & licence | Attribution / notice | Notes |
| --- | --- | --- | --- |
| Project-authored A/B/C (above) | our own work | project credit | **Preferred**: zero third-party licence, full control, no style mismatch |
| game-icons `reticule` | [lorc/reticule](https://game-icons.net/1x1/lorc/reticule.html) — **CC BY 3.0** | "Icons made by Lorc. Available on https://game-icons.net" + licence link + changes | SVG monochrome, fits atlas; needs attribution register row |
| game-icons `crosshair` | [delapouite/crosshair](https://game-icons.net/1x1/delapouite/crosshair.html) — **CC BY 3.0** | "Icons made by Delapouite. Available on https://game-icons.net" + licence link + changes | Alternative silhouette |
| Font Awesome `crosshairs` | [Font Awesome Free](https://fontawesome.com/license/free) — icons **CC BY 4.0** | CC BY 4.0 attribution + licence link; keep header | Fallback; heavier attribution bookkeeping |

All three candidate pages were checked **HTTP 200** on 2026-10-24. No candidate is downloaded or
committed here. Any chosen candidate needs a `THIRD_PARTY_NOTICES.md` row (primary; `docs/CREDITS.md`
alternative) and E clearance.

---

## 4. Screenshot comparison plan (reticle-specific)

This refines `docs/ICON_MAPPING.md` §10; **D captures**, E/owner review, no visual claim before then.

| Step | Requirement |
| --- | --- |
| 0. Preconditions | E licence clearance for the chosen candidate; Lead approval; build SHA frozen; no binary committed before this point |
| 1. Baseline | native reticle only (no overlay); 3 frames each on dark/bright/blood-red backgrounds; 1920×1080 and 1280×720; fixed camera/FOV/position/time-of-day |
| 2. Candidate matrix | A, B, C (and optional spread ring), each at the same frames; record atlas slot + alpha/tint settings |
| 3. Aim-distance set | fixed aim targets at ~5 m, ~10 m, ~25 m equivalent in-scene distances; same pitch/yaw |
| 4. Measurements | outer arm span (px), gap radius (px), centre dot (px), ring diameter (px), opacity/contrast at 16/32/48/64 px display, occlusion with kill feed/HUD, double-reticle visibility |
| 5. Blind review | owner + E label A/B/C vs baseline without knowing which is which; pass/fail per variant |
| 6. Evidence | screenshots + hashes under `local/`/`evidence/` (gitignored, never committed); receipt records build SHA + chosen variant + measurement table |
| 7. Claim gate | only after 4–6: may say "additive overlay drawn and compared"; **never** "native reticle resized/changed" unless engine evidence exists |

**Failure conditions (stop, do not claim):** double reticle unacceptable; overlay obscures target or
feed; DXT5 alpha fringing; overlay not visible at 720p; any measurement contradicts the concept.

---

## 5. Risks / unknowns

1. Native reticle cannot be hidden — double reticle may make the overlay unusable.
2. Engine HUD scale/overlay ordering for the reticle is unverified in-engine.
3. Spread-ring input value from A's tuning is not confirmed; static variants are the fallback.
4. CC BY candidates require attribution/notice work; authored avoids it.
5. No screenshots exist yet; no visual acceptance, no gameplay/accuracy claim.

---

## 6. Acceptance gates (checklist)

- [ ] E independent licence review of the chosen candidate (and attribution row).
- [ ] Lead/owner approval of the concept; E clears screenshots scope.
- [ ] D captures the §4 matrix and stores evidence privately.
- [ ] Owner + E blind review recorded with pass/fail.
- [ ] Only then: asset PR with `THIRD_PARTY_NOTICES` evidence and DDS/BRF binaries (owner-approved).
- [ ] No acceptance of any ledger leaf, legal gate or City outcome follows from this concept.

**Non-claims:** no binary, no game launch, no screenshot, no visual or accuracy claim, no native
reticle resize, no acceptance/legal clearance.
