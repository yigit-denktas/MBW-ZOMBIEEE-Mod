# In-game cosmetics / icon layer — mapping contract

**Status:** design contract and mapping proposal. **Not implemented.** No atlas, BRF, presentation
or sound has been produced or tested in Warband; no game launch was performed for this document. No
binary asset is committed. This is not acceptance of any ledger leaf or City outcome.
**Observed:** 2026-10-24, branch `agent/g-free-assets` (base `main` `c72de64`), owner task `task-49`.
**Related:** [`reference/FREE_ASSET_SOURCES.md`](../reference/FREE_ASSET_SOURCES.md) (licence
catalogue), [`configs/ui_icon_map.json`](../configs/ui_icon_map.json) (definitions-only mapping),
[`reference/LEGAL_RIGHTS_AND_CREDITS.md`](../reference/LEGAL_RIGHTS_AND_CREDITS.md) (rights gate).
**Review:** independently reviewed by Agent E on 2026-10-24 (cross-review record:
[`reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md`](../reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md) §A; PR #31 review comment). Findings are folded in; this is
**not** legal clearance and **not** acceptance.
**Task-64 addendum:** cosmetics/equipment/cover/reticle slots (§4.6) and the required screenshot
comparison plan (§10). Visual validation is **not** performed here.

**Scope.** A kill-feed / HUD icon layer for `ZOMBIEEE_Remaster` that maps **melee, bow/crossbow,
firearm, zombie and money/USD** events to icons, plus the atlas contract that a later
implementation will follow. It is **additive** to the game UI; it does not replace native kill
notifications or native inventory icons.

**Non-goals.** No inventory-icon replacement (inventory icons are 3D item meshes, §2.3 of the
catalogue), no native-asset redistribution, no engine patching in this task, no visual or gameplay
acceptance.

---

## 1. Why a separate icon layer

1. **Native kill feedback is text, not an icon feed.** We have not verified a native icon feed; the
   safe design is an **additive presentation** that renders text plus an icon per row, with a
   text-only fallback. (Native feed specifics are **open** — the community "killstreaks and
   statistics" threads were Cloudflare-blocked in this pass; see catalogue §3.6.)
2. **Native UI art has no recorded redistribution right.** Native HUD/score meshes, item meshes,
   fonts and hard-coded sounds are excluded by the rights gate (legal dossier R-03/R-05). Our public
   icon layer must be built from cleared replacements (game-icons.net CC BY 3.0 / Font Awesome CC BY
   4.0 / our own glyphs).
3. **Owner decision: money is a USD symbol, not a gold coin.** "Gold coin" icons read as an RPG
   currency; ZOMBIEEE's economy is modern. The canonical money mark is `$` (typographic glyph
   first, icon fallback), with a locale-independent amount format.
4. **Modifier + redistribution friction is lowest with a small, central atlas.** One atlas, one
   attribution register, one licence story.

---

## 2. Warband UI facts this contract relies on (verified)

| Fact | Evidence |
| --- | --- |
| UI screens/HUDs are **presentations** with triggers; overlays are text/mesh/button/check-box/combo/image-button overlays manipulated by `overlay_set_color`, `overlay_set_alpha`, `overlay_set_position`, `overlay_set_size`, `overlay_set_text` | Persistent World `module_presentations.py` (BSD-3-Clause code) |
| Presentation space is a **1000 × 1000 virtual canvas** with `set_fixed_point_multiplier 1000` | Persistent World presentations (e.g. 500,375 = centre; 1500 panel sizes) |
| Custom UI images are **mesh resources** registered in `module_meshes.py` and drawn with `create_mesh_overlay`; mods add entries such as score graphics, progress bars and charts | Persistent World `module_meshes.py` (`mp_score_a/b`, `pw_progress_bar`, `pw_stats_chart_*`, checkbox/menu meshes) |
| UI textures are **DDS**; alpha textures DXT3/DXT5; dimensions multiple of four | Modding Wiki 3D art pipeline (public domain) |
| Inventory item icons come from the **item mesh**, not a 2D icon field | Item record documentation in `module_items.py` (meshes list; no icon field) |
| Weapon classes carry item-type flags: `itp_type_one_handed_wpn`, `itp_type_two_handed_wpn`, `itp_type_polearm`, `itp_type_bow`, `itp_type_crossbow`, `itp_type_arrows`, `itp_type_bolts`, `itp_type_thrown`, `itp_type_pistol` (firearms) | `header_items.py` in the same code source |
| Sounds are `module_sounds.py` entries with `.ogg`/`.wav` files and flags (`sf_2d`, `sf_looping`, …) | Persistent World `module_sounds.py` |

**Not verified (must stay open):** whether a sprite-style mesh needs an extra BRF mesh flag for UI
crispness; the exact DDS mipmap behaviour for HUD sprites; native kill-feed event availability. These
require a build/launch test that this task does not perform.

**Native boundaries (no redistribution right recorded; never copy into repo):** `mesh_mp_ingame_menu`, `mesh_mp_ui_host_main`,
`mesh_load_window`, `mesh_mp_score_*`, native item meshes, `font_data.xml`/`font.dds`, native sound
files. See catalogue §2.7.

---

## 3. Atlas contract (proposal)

| Property | Proposed value | Rationale |
| --- | --- | --- |
| Runtime format | DDS, **DXT5** (alpha gradients) | Matches verified Warband texture guidance; icons have anti-aliased alpha edges |
| Source format | SVG (game-icons / Font Awesome) or authored vector | Editable, recolourable, no raster scaling artefacts |
| Master render | 64 × 64 px white `#FFFFFF` on transparent, 1× pixel grid, no drop shadow | Downscale to 32/16 with clean alpha; white allows runtime tint |
| Delivered sizes | 64, 32, 16 px (24 px optional) | Feed row icon 32; compact HUD 16; large hit marker 64 |
| Atlas pages | 256 × 256 or 512 × 512, ≤ 64 slots/page, **2 px padding** | Fewer materials/draw states; bleed safety at DXT |
| Naming | `ui_zdr_<slot>` (slot list in `configs/ui_icon_map.json`) | Stable ids, no spaces; matches module mesh id convention |
| Tint | White glyph + `overlay_set_color` | One glyph serves survivor/undead/team/alert states without extra art |
| Fallback | Text token from the same mapping (e.g. `[BOW]`) | No missing-glyph boxes, no engine errors if the atlas is absent |
| Attribution | One register generated from the JSON slots (author + licence + URL) | CC BY compliance without hand-maintained lists |

**Important style constraint:** monochrome silhouettes (game-icons) at 16–32 px must be checked for
legibility before approval; a filled silhouette is preferable to thin-line detail. If a slot fails
at 16 px, deliver it at 24/32 px only and record the minimum size in the JSON.

---

## 4. Required mappings

### 4.1 The five required categories

| Category | Canonical icon key | Primary source (licence) | Fallback icon | Text token | Notes |
| --- | --- | --- | --- | --- | --- |
| **Melee** | `melee` | game-icons `crossed-swords` (Lorc, CC BY 3.0) | `melee-single` = `sword-brandish` (Delapouite) | `[MELEE]` | Also used for polearms/axes; the weapon name in the row disambiguates |
| **Bow / crossbow** | `bow` | game-icons `bow-arrow` (Delapouite, CC BY 3.0) | `bowman` (Lorc) | `[BOW]` | Distinguish crossbow with `crossbow` = game-icons `crossbow` (Carl Olsen) |
| **Firearm** | `firearm` | game-icons `rifle` (sbed, CC BY 3.0) | Font Awesome `gun` (CC BY 4.0); `ak47`/`uzi`/`revolver` class variants | `[FIREARM]` | Class variants: `firearm-rifle` (`ak47`), `firearm-smg` (`uzi`), `firearm-pistol` (`revolver`), `firearm-bolt` (`winchester-rifle`) |
| **Zombie** | `zombie` | game-icons `shambling-zombie` (Delapouite, CC BY 3.0) | `dead-head` (Delapouite) | `[ZOMBIE]` | Faction tint (red) for hostile undead; `raise-zombie` for wave-spawn events |
| **Money / USD** | `money-usd` | **`$` glyph** rasterised from an OFL font (Inter, OFL 1.1) — zero extra licence | Font Awesome `dollar-sign` (CC BY 4.0) or game-icons `banknote` (Delapouite) | `$` + amount | **No gold coin.** Typographic symbol is the primary; sprite is fallback |

### 4.2 Event → icon map (kill feed and HUD)

Severity/priority controls row ordering and colour; every row carries text so colour is never the
only channel.

| Event id | Row template | Icon key | Priority | Colour / tint | TTL |
| --- | --- | --- | --- | --- | --- |
| `kill.melee` | `{killer} killed {victim} with {weapon}` | `melee` | 20 | default | 6 s |
| `kill.bow` | …with bow | `bow` | 20 | default | 6 s |
| `kill.crossbow` | …with crossbow | `crossbow` | 20 | default | 6 s |
| `kill.firearm` | …with firearm | `firearm` (+class variant) | 25 | default | 6 s |
| `kill.thrown` / `kill.explosive` | …with thrown weapon / explosion | `explosive` (`grenade`, sbed) | 30 | warning | 7 s |
| `kill.zombie` | `{killer} put down {zombie}` | `zombie` | 15 | hostile tint | 5 s |
| `kill.headshot` | badge on the weapon row | `headshot` (`archery-target`, Lorc) | 25 | accent | row TTL |
| `kill.teamkill` | `{killer} team-killed {victim}` | `teamkill` (`pirate-skull`, Lorc) | 40 | danger | 8 s |
| `death.suicide` | `{player} died` | `death` (`dead-head`, Delapouite) | 30 | muted | 6 s |
| `death.bleedout` | `{player} bled out` | `death` | 30 | muted | 6 s |
| `wave.start` | `Wave {n}` | `wave` (`raise-zombie`, Skoll) | 35 | hostile | 5 s |
| `round.start` | `Round {n}` | `round` (`ringing-bell`, Lorc) | 35 | neutral | 5 s |
| `money.gain` | `+$ {amount}` | `money-usd` | 10 | positive | 4 s |
| `money.spend` | `-$ {amount}` | `money-usd` | 10 | negative | 4 s |
| `money.bounty` | `Bounty +$ {amount}` | `money-usd` | 20 | accent | 5 s |
| `money.insufficient` | `Not enough money` | `money-usd` | 10 | negative | 4 s |

**Row rules:** max 5 visible rows; newest at top; fade out; no per-frame allocation; drop oldest on
overflow; never exceed 1 icon + 1 text row per event. A text-only feed is the mandatory fallback.

### 4.3 Weapon class → icon (from item type flags)

| Item type flag | Icon slot | Confident? |
| --- | --- | --- |
| `itp_type_one_handed_wpn`, `itp_type_two_handed_wpn`, `itp_type_polearm` | `melee` | yes (flag verified) |
| `itp_type_bow` | `bow` | yes |
| `itp_type_crossbow` | `crossbow` | yes |
| `itp_type_thrown` | `explosive` (or `melee` for throwing knives/axes if preferred) | mapping decision |
| `itp_type_pistol` | `firearm` | yes (firearms use this class) |
| `itp_type_arrows`, `itp_type_bolts` | ammo badge only (no kill row icon) | yes |
| unknown / unset | `firearm` only if the item name/telemetry says firearm; otherwise **no icon + text token** | must fall back honestly |

The telemetry/trigger layer is the source of truth for the weapon used (not the guessed icon). If the
weapon id is unknown, the row shows the text token and no icon rather than a wrong silhouette.

### 4.4 Currency (USD) contract

- **Canonical mark:** `$` (U+0024) rendered from the UI font atlas (OFL), not a coin sprite.
- **Amount format:** `$` + grouped integer (`$1,234`), never `1.234 $`; negative as `-$12`; clamp
  to 7 digits in the feed and move the full value to a tooltip/console; no floating-point drift
  (store minor units in telemetry).
- **Events:** gain, spend, bounty, insufficient funds; tint positive/negative; icon is an anchor, the
  amount is always text.
- **Native gold-coin art is not used**, and no third-party coin art is needed.

### 4.5 Zombie / faction tinting

- One white `zombie` glyph, tinted hostile (red) or neutral (grey) at runtime; the row text always
  names the victim type.
- Do not encode "zombie vs survivor" by colour alone; the icon shape plus text carries it.

---

### 4.6 Cosmetics / equipment / cover / reticle slots (task-64 addendum)

Slots for between-wave upgrade UI and an additive reticle overlay. All icons are 2D UI only (not 3D
models) and require the same attribution/atlas rules as §3–§4.

| Slot key | Use | Primary icon (source, licence) | Fallback | Text token |
| --- | --- | --- | --- | --- |
| `armour` | armour purchase/upgrade | game-icons `kevlar-vest` (Skoll, CC BY 3.0) | `breastplate` (Lorc) | `[ARMOUR]` |
| `armour-upgrade` | upgrade action | game-icons `armor-upgrade` (Delapouite, CC BY 3.0) | `armour` | `[UPGRADE]` |
| `clothing` | clothing/cosmetic purchase | game-icons `hoodie` (Delapouite, CC BY 3.0) | `person` (Delapouite) | `[CLOTHING]` |
| `helmet` | helmet/hat cosmetic | game-icons `light-helm` (Delapouite, CC BY 3.0) | `breastplate` (Lorc) | `[HELMET]` |
| `hair` | hairstyle cosmetic | game-icons `hair-strands` (Delapouite, CC BY 3.0) | `person` (Delapouite) | `[HAIR]` |
| `face` | face/head cosmetic | game-icons `person` (Delapouite, CC BY 3.0) | `hair` | `[FACE]` |
| `crate` | supply/crate cover prop UI | game-icons `wooden-crate` (Delapouite, CC BY 3.0) | `barricade` (Delapouite) | `[CRATE]` |
| `barricade` | barricade/cover deployment | game-icons `barricade` (Delapouite, CC BY 3.0) | `crate` | `[COVER]` |
| `reticle` | **additive** reticle overlay candidate | project-authored crosshair (best) or game-icons `reticule` (Lorc, CC BY 3.0) | `crosshair` (Delapouite) / Font Awesome `crosshairs` (CC BY 4.0) | n/a — engine reticle remains |

**Reticle rule:** this layer may **add/replace an overlay texture**, never claim to resize the native
reticle; any visual acceptance requires the in-game screenshot comparison in §10. Icon page pattern
`https://game-icons.net/1x1/<author>/<icon>.html`; candidate pages checked 2026-10-24.

3D character/cosmetic candidate sources (Kenney Animated Characters Survivors, MakeHuman community
categories) are tracked in `reference/FREE_ASSET_SOURCES.md` §3.8/§3.9; they are not icon slots.

---

## 5. Native atlas risk and free replacements

| Native element we would otherwise touch | Status | Replacement for a public/clean-room build |
| --- | --- | --- |
| Native HUD/score meshes (`mesh_mp_score_*`, `mesh_mp_ingame_menu`, `mesh_mp_ui_host_main`) | No redistribution right recorded; treat as non-redistributable (legal dossier R-03/R-05) | Our own atlas + presentation overlays; layout re-implemented from scratch |
| Native inventory item icons (item meshes) | No redistribution right recorded; treat as non-redistributable (R-03/R-05) | 3D item meshes authored from cleared sources (catalogue §3.4), or keep private-only |
| Native fonts (`font_data.xml`, `font.dds`) | No redistribution right recorded; treat as non-redistributable (R-05) | OFL font → `font.dds` + `font_data.xml` in our module's language folder |
| Native sounds (hard-coded ids) | No redistribution right recorded; treat as non-redistributable (R-05) | CC0/CC-BY sounds with new `module_sounds.py` ids (catalogue §3.5) |
| Native kill notifications (text) | Engine UI; internals unverified; no redistribution right recorded | Additive presentation; text-only fallback; no engine hooks claimed |
| Native reticle/crosshair (engine UI) | Engine-owned; no redistribution right recorded; **no native resize claim** | Additive overlay candidate (`reticle` slot) + screenshot comparison (§10); owner/E approval before any binary |

**Policy:** the private/local build may *reference* native assets from the user's own installation
(never captured into the repo or evidence bundles). Any public artifact must use the replacement
column. This is the same boundary as [`reference/LEGAL_RIGHTS_AND_CREDITS.md`](../reference/LEGAL_RIGHTS_AND_CREDITS.md)
§4 — a conservative project position, not a legal determination.

---

## 6. Implementation path (proposal, not done)

1. **Author/collect vectors** for each slot from the licence-cleared sources; record author, licence,
   icon URL and modification in `configs/ui_icon_map.json` (one entry per slot).
2. **Render** 64 px white-on-transparent masters; visual QA on dark, bright and blood-red backgrounds
   at 16/32 px; reject illegible thin-line glyphs.
3. **Pack** into a 256/512 atlas with 2 px padding; export DDS DXT5; keep the SVG sources out of the
   repo until the licence-cleared asset PR (with the §1.4 register from the catalogue).
4. **BRF + module wiring:** import the atlas as a mesh/sprite resource in OpenBRF; add
   `module_meshes.py` entries; draw in a presentation with `create_mesh_overlay` and
   `overlay_set_position/size/color/alpha`; all positions in the 1000×1000 space.
5. **Feed data source:** server-authoritative events from our own trigger/telemetry layer, not
   scraped from native UI. Bounded queue, TTL, max 5 rows, no per-tick allocation.
6. **Fallback:** if the atlas is missing or a slot id is unknown, render text only; log once and stay
   silent (no engine-error spam).
7. **Verification later (separate task):** offline JSON validation + licence-register check now; a
   build/launch visual pass only when the owner schedules it — not this task.

---

## 7. Accessibility and presentation rules

- **Never icon-only:** every feed row includes the weapon/event text; the icon is redundant encoding.
- **Minimum size:** 16 px in dense HUD; 32 px in the kill feed; no icon below 16 px.
- **Contrast:** white glyph over a dark translucent plate; verify ≥ 4.5:1 against the plate; do not
  rely on the 3D scene behind the text.
- **Colour-blind safety:** severity uses icon shape + text, not just red/green; team tint is additive.
- **Motion:** fade in/out only; no flashing above 3 Hz; respect a future "reduced motion" toggle.
- **Localisation:** text tokens and row templates are module strings; `$` is locale-formatted, not
  hard-coded to English words.

---

## 8. Definitions file (this PR's only executable artifact)

`configs/ui_icon_map.json` is a **definitions-only proposal**: schema/version, atlas contract, icon
slots with source/author/licence/attribution, event map, weapon-class map, currency contract and
native-risk table. It contains **no binary data, no code and no native asset reference that would be
shipped**. It must validate as JSON and is not wired into the module system.

Consumers (future):
- an icon build script (SVG → PNG → DDS → BRF) can iterate `slots[]`;
- an attribution generator can emit the CC BY/OFL register from `slots[]`;
- the presentation code can resolve `events[].icon` to `slots[].key`.

---

## 9. Open items (do not present as resolved)

1. **Native kill-feed internals unverified** — direct forum fetches were Cloudflare-blocked; the
   design must remain additive + text fallback.
2. **DDS/sprite behaviour for HUD scale** unverified in-engine; the atlas contract may need a
   mipmap/format adjustment after a real build test.
3. **Money glyph choice:** `$` from OFL font (preferred) vs Font Awesome `dollar-sign` (fallback) —
   decide when the first atlas is produced.
4. **Attribution register** not generated yet; it is mandatory before any CC BY icon ships.
5. **Modern survivor 3D set** still missing (catalogue §3.4 gap) — irrelevant to the 2D icon layer,
   but blocks a fully licence-clean visual remaster.
6. **No acceptance claim:** this file does not accept any ledger leaf, the legal gate, or any City
   outcome; no visual or gameplay verification has been performed.
7. **Screenshots are required for visual/asset validation:** cosmetic/prop/reticle candidates and
   any visual change need the in-game comparison in §10; none captured in this docs-only task.

---

## 10. Screenshot comparison plan (required for visual/asset validation)

**Owner/Lead requirement:** any visual or asset validation (icon atlas, cosmetic/prop replacement,
reticle overlay) needs **in-game screenshots**; this document does not claim any such validation and
no game launch was performed for it.

| Step | Requirement |
| --- | --- |
| 1. Freeze the build | same module SHA, same scene/map, same HUD scale (1000×1000 presentation space), same camera/FOV/position, same time-of-day and weather |
| 2. Capture baseline | 3 frames each on dark, bright and blood-red backgrounds; 1920×1080 and 1280×720; native reticle/HUD left untouched |
| 3. Capture candidate | same frames with the additive overlay/atlas loaded; no other change |
| 4. Measure | reticle width at a fixed aim distance (px), icon legibility at 16/32/64 px, contrast vs plate, overlap/occlusion with kill feed |
| 5. Review | owner + E blind comparison; record pass/fail per slot; store under `local/`/`evidence/` (gitignored, never committed) |
| 6. Prove | only then may a visual claim be made; reticle is described as an **additive overlay**, never a native resize; receipt records build SHA + screenshot hashes |

**Non-claims:** no screenshots exist for this document, no visual acceptance is implied, and no
binary asset may be committed before licence clearance + this comparison.

The project-authored reticle/overlay concept (geometry, variants A/B/C, candidate licences, reticle-
specific measurements) is [`reference/RETICLE_OVERLAY_CONCEPT.md`](../reference/RETICLE_OVERLAY_CONCEPT.md);
it is the subject of this validation gate and contains no binary or visual claim.
