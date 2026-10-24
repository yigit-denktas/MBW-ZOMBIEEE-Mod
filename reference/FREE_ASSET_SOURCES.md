# Free-to-use asset sources for a Warband mod (cosmetics + icon layer)

**Status:** research catalogue and integration plan. **Docs-only:** no asset binary is downloaded
into, or committed to, this repository; no game launch; no runtime, visual or acceptance claim.
**This is not legal advice and grants no licence.** It records what each source states, the date it
was observed, and the integration constraints that follow.
**Observed:** 2026-10-24, from branch `agent/g-free-assets` (base `main` `c72de64`), owner task
`task-49`.

**Addendum (task-64, 2026-10-24):** environment/defensive-prop and survivor
cosmetics/armour/faces/hairstyles candidates in §3.7–§3.8; reticle overlay candidates and the required
screenshot-comparison plan in `docs/ICON_MAPPING.md` §4.6/§10. **Visual/asset validation requires
in-game screenshots** (owner/Lead); none were captured in this docs-only task, and no native reticle
resize is claimed.
**Review:** independently reviewed by Agent E on 2026-10-24 (cross-review record:
[`reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md`](CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md);
review comment on PR #31). E's findings are folded in; this is still **not** legal clearance and **not**
an acceptance (§9).
**Related:** [`docs/ICON_MAPPING.md`](../docs/ICON_MAPPING.md) (icon/event/currency contract),
[`configs/ui_icon_map.json`](../configs/ui_icon_map.json) (definitions-only proposal, no binaries),
[`reference/LEGAL_RIGHTS_AND_CREDITS.md`](LEGAL_RIGHTS_AND_CREDITS.md) (ZOMBIEEE rights dossier).

**Non-claims.** No original ZOMBIEEE or Warband asset is licence-cleared by this document. Nothing
here changes ledger state: City required outcomes stay **0/23**, milestones **0/5**,
`runtime_verified=false`, `ZOM-LEGAL-01` stays open. "Frictionless" below means *licence clarity +
format fit + integration effort*, not in-game approval.

Evidence classes used:

| Class | Meaning |
| --- | --- |
| **verified-primary** | licence/terms page or repository file read directly on 2026-10-24 (HTTP 200) |
| **verified-community** | community documentation read directly; not an official engine or legal document |
| **statement** | the site's own plain-language claim, not a standard licence text |
| **external-blocked** | the page exists but was bot-blocked; not relied on |
| **unknown** | explicitly not established — never presented as fact |

---

## 1. Licence policy for this project

1. **Preferred, in order:** CC0 1.0 (a public-domain-equivalent waiver **with a fallback licence**)
   → CC BY 3.0/4.0 (with a shipped attribution register) → SIL OFL 1.1 (fonts), Apache-2.0, MIT/ISC
   (code/tools). Do not describe CC0 as universal "public domain" status.
2. **Conditional:** licences that allow use *inside a product* but forbid redistributing the assets
   as assets. A Warband module is distributed as loose `Resource/`, `Textures/`, `Sounds/`, `Data/`
   and compiled-text files, so the mod package *is* an asset collection. Treat these as **not
   frictionless**; only use them if the owner decides the whole module is the "product" and legal
   review agrees. They are marked **AVOID (bundle)** below, not "illegal".
3. **Excluded from a distributable bundle:** CC BY-NC, CC BY-ND, CC BY-SA (share-alike would extend
   to the adapted asset and complicate the whole bundle), GPL/AGPL assets (copyleft and, for AGPL, the
   network clause), legacy CC Sampling+ (still present on old Freesound sounds), unknown/custom
   licences, "free for personal use", "for non-commercial mods only", and every ripped or
   unattributed game asset.
4. **No binary commits.** This repository stays asset-free. If a later PR adds a cleared asset it
   must add, in the same commit: source URL, author, licence + version, observation date, SHA-256 of
   the *source* download, the exact list of modifications, and the required attribution text
   (see §6). Until then, only definitions (markdown/JSON) are committed.
5. **Private/local build ≠ public bundle.** The owner's private build may reference native Warband
   assets from their own installation; those files must never be captured into the repo, evidence
   bundles or releases (see `reference/LEGAL_RIGHTS_AND_CREDITS.md` §4).

---

## 2. Warband integration constraints (verified)

Everything in this section is what makes an external asset "frictionless" or not. The engine is a
2010-era title; modern glTF/PBR workflows need conversion.

### 2.1 Build pipeline

- The Warband **Module System** is a set of Python scripts; the game does **not** read Python. The
  scripts compile content to the text files under `Modules/<module>/`. The official build log
  enumerates the stages: *"Exporting meshes… Exporting sounds… Exporting presentations… Exporting
  map icons…"* → so any new mesh/texture/sound/presentation must be wired into the module system,
  not just dropped in a folder. **verified-community:** [Official Module System Documentation Part
  01](https://mbmodwiki.github.io/Official_Module_System_Documentation:_Part_01) (last modified
  2015-06-29; wiki content public domain).

### 2.2 Meshes and textures

- Mesh workflow: export **OBJ** from the DCC tool, import into **OpenBRF**, assign materials/shaders
  and texture references (diffuse, normal, specular), then Ctrl+E to validate. **verified-community:**
  [Outline of the Mount&Blade 3D Art pipeline](https://mbmodwiki.github.io/index.php@title=Outline_of_the_Mount&Blade_3D_Art_pipeline%3A_How_to_make_your_models_and_get_them_in_the_game&printable=yes.html)
  (last modified 2012-01-14; public domain).
- Textures are **DDS with DXT compression**: DXT1 for RGB without alpha; **DXT3 or DXT5 for alpha**
  (DXT3 for hard alpha edges such as hair, DXT5 for gradients); texture dimensions must be a
  **multiple of four**; community guidance is 512×512 standard, 1024×1024 detailed, 256×256 for small
  detail/normal/specular maps (same source). 1-bit alpha sprites therefore should prefer DXT3, not
  DXT1.
- Consequence for icons: an SVG cannot be used at runtime. Rasterise → PNG with alpha → DDS →
  BRF/OpenBRF. Prefer a single packed atlas over many tiny textures (fewer materials/draw states).

### 2.3 Items and "weapon icons"

- An item record is: item id, display name, **list of meshes**, flags, capabilities, value, stats,
  modifiers, optional triggers/factions. There is **no 2D icon field**: the inventory window renders
  the item's mesh. **verified-primary (code):** `module_items.py` record documentation in
  [vornne/pw_module_system](https://github.com/vornne/pw_module_system) (BSD-3-Clause, see §3.6).
- Consequence: a "weapon icon" for inventory/tooltips means a **3D item mesh**, not a sprite. The
  2D silhouette layer this task proposes is a **kill-feed/HUD layer**, not an inventory-icon
  replacement; keep the two contracts separate.
- Weapon-class flags usable for mapping (verified from the same module system's `header_items.py`):
  `itp_type_one_handed_wpn 0x2`, `itp_type_two_handed_wpn 0x3`, `itp_type_polearm 0x4`,
  `itp_type_arrows 0x5`, `itp_type_bolts 0x6`, `itp_type_bow 0x8`, `itp_type_crossbow 0x9`,
  `itp_type_thrown 0xA`, **`itp_type_pistol 0x10`** (firearms). Unknown/unset class must fall back
  to a generic token, never to a wrong weapon icon.

### 2.4 UI layer

- UI screens/HUDs are **presentations** (`module_presentations.py` records with triggers). Overlays
  are created with module-system operations: `create_text_overlay`, `create_mesh_overlay`,
  `create_button_overlay`, `create_image_button_overlay`, `create_check_box_overlay`,
  `create_combo_*`, and manipulated with `overlay_set_color`, `overlay_set_alpha`,
  `overlay_set_position`, `overlay_set_size`, `overlay_set_text`, `overlay_animate_to_*`.
  **verified-primary (code):** Persistent World `module_presentations.py` (`game_credits`,
  `game_multiplayer_admin_panel`, `admin_menu`, …).
- Presentation coordinates are a **1000×1000 virtual canvas** with `set_fixed_point_multiplier 1000`
  (positions like 500,375 for centre; sizes like 1500 for oversize panels). Same source.
- Custom UI images are **mesh entries**: `module_meshes.py` maps a module id to a mesh resource
  (e.g. `mp_score_a`, `mp_score_b`, `load_window`, `checkbox_off/on`, `white_plane`,
  `mp_ingame_menu`, `mp_inventory_slot_*`, `pw_stats_chart_*`, `pw_progress_bar`). A mod adds its own
  entries there and draws them with `create_mesh_overlay`. Same source.
- Consequence: our icon atlas must ship as BRF mesh/sprite resource(s) plus `module_meshes.py`
  entries and presentation overlays. A future implementation can reuse the recorded patterns but
  must not copy Persistent World art (its repository contains code only, no `.brf`/`.dds`).
- **Native UI meshes/textures** referenced by those names (e.g. `mesh_load_window`,
  `mesh_mp_ingame_menu`, `mesh_mp_ui_host_main`, score graphics) are TaleWorlds game assets. They
  are not in this repository and cannot be redistributed. A public/clean-room build needs our own
  equivalents; the private/local build may reference the user's installation (see §2.7).

### 2.5 Sounds

- Sounds are declared in `module_sounds.py` as `("sound_id", flags, ["file.ogg", ...])`; the same
  file mixes **`.ogg` and `.wav`** entries, with flags such as `sf_2d`, `sf_looping`,
  `sf_stream_from_hd`, priority and volume. Music tracks are declared separately
  (`module_music.py`, `.ogg`).
- The file header warns that **many sound entries are hard-coded into the engine and should not be
  removed** (to disable them, empty their file list); mod sounds go before the animation sound
  group. **verified-primary (code):** Persistent World `module_sounds.py`, `module_music.py`.
- Consequence: add new sound ids rather than reusing/removing native ids; verify sample rate/codec
  against the engine at build time (not verified in this pass — no game launch).

### 2.6 Fonts

- Warband fonts are **bitmap atlases**: `font_data.xml` (glyph metrics/table) plus a `font.dds`
  texture, placed under `Data/languages/<lang>/` and `Textures/languages/<lang>/`. The community
  workflow uses **BMFont** to rasterise a TTF and a converter (Swyter's XML tool) to produce the
  Warband XML. **verified-community:** Mount&Blade Chinese forum font guide (thread 2076056; the
  toolchain and file placement are described there; forum content is community-authored, not an
  official engine doc).
- Consequence: licences must permit **rasterising/embedding** the font into an atlas. OFL 1.1
  permits embedding and redistribution with its notice; do not redistribute a modified font file
  under a Reserved Font Name. Glyph coverage (Latin + punctuation + `$`) must be tested, and the
  native font files themselves are TaleWorlds assets.

### 2.7 Native-asset boundary (no redistribution right recorded)

For the engine and the owner's private module, **no redistribution right is recorded for this
project**; treat the following as **non-redistributable and do not bundle them** (legal dossier
R-03/R-05): native UI meshes/textures and native item meshes; native fonts (`font_data.xml`, `font.dds`);
hard-coded native sound files; all original ZOMBIEEE Beta 0.4 content and its OSP/third-party
credits; Warband game files; WSE2 binaries. The rights position is recorded in
[`reference/LEGAL_RIGHTS_AND_CREDITS.md`](LEGAL_RIGHTS_AND_CREDITS.md). This catalogue only clears
**new, independently licensed replacements**.

### 2.8 Conversion toolchain (not vendored)

OpenBRF (BRF/mesh/texture authoring), Blender (modelling/rigging/export), an image editor with DDS
support (GIMP + DDS plug-in, ImageMagick, or a DXT compressor), Audacity/ffmpeg (audio conversion),
BMFont (font atlas), Swyter's font XML converter. **We do not vendor tools**; each tool's licence is
separate from the licence of the assets it produces (the evidence for that separation belongs with
the asset licence, not the editor). Verify each tool's current licence before bundling any of it.

---

## 3. Source catalogue (verified licences)

Format: **decision** is ADOPT (primary), ADAPT (usable with a process/format constraint), or
**AVOID** (for a distributable Warband bundle, unless the owner's legal decision changes the model).
"Redistribute?" means *can the asset files be included in the mod package*. All observation dates
are **2026-10-24**.

### 3.1 UI icons (kill-feed / HUD silhouettes)

| ID | Source | Licence | Modify | Redistribute | Attribution | Constraints / notes | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IC-01 | [game-icons.net](https://game-icons.net/) — SVG/PNG, 4,000+ monochrome icons | **CC BY 3.0** (site "About": "provided under the terms of the Creative Commons 3.0 BY license") | Yes | Yes (as part of a work) | **Required:** "Icons made by {author}. Available on https://game-icons.net"; link licence; note changes | SVG is editable (recolour/threshold); attribution is per-icon author; must ship an attribution register. Icons verified on tag pages: `crossed-swords` (Lorc), `sword-brandish` (Delapouite), `gladius` (Skoll), `bow-arrow` (Delapouite), `bowman` (Lorc), `crossbow` (Carl Olsen), `rifle` (sbed), `ak47` (Skoll), `uzi` (Delapouite), `revolver` (Skoll), `winchester-rifle` (Skoll), `shambling-zombie`/`dead-head` (Delapouite), `raise-zombie` (Skoll), `grenade` (sbed), `crossed-pistols` (Lorc), `gunshot` (Lorc), `archery-target` (Lorc), `crosshair` (Delapouite), `banknote` (Delapouite), `cash` (Lorc), `pirate-skull` (Lorc), `ringing-bell` (Lorc), `profit` (Lorc), `dark-squad` (Lorc) | **ADOPT** — primary icon source |
| IC-02 | [Kenney — Game Icons](https://kenney.nl/assets/game-icons) (105 icons, 2D) | **CC0** (Kenney support: "all game assets on the asset pages are public domain licensed (CC0)"; asset page: License CC0) | Yes | Yes | Not required (credit "Kenney" appreciated; **do not use the Kenney logo**) | General GUI/prompt glyphs, not weapon silhouettes; check each pack's included license file (some bundles include contributions); contents not inspected on disk in this pass | **ADAPT** — generic UI glyphs only |
| IC-03 | [Font Awesome Free](https://fontawesome.com/license/free) — icon SVGs | **Icons: CC BY 4.0**; fonts SIL OFL 1.1; code MIT (repo `LICENSE.txt`) | Yes | Yes | **Required** for icons (CC BY): attribution + licence link; file headers already carry a notice — keep it | Verified individual SVGs: `dollar-sign` and `gun` (Font Awesome Free 6.7.2). Do **not** use brand icons (trademarks). | **ADAPT** — `dollar-sign` money glyph and firearm fallback |
| IC-04 | [Material Symbols / Material Design Icons](https://github.com/google/material-design-icons) | **Apache License 2.0** (repo `LICENSE`) | Yes | Yes | NOTICE/copyright retention; state changes | `attach_money` style glyphs exist; Apache is fine but heavier attribution bookkeeping than CC0/CC BY for one symbol | **AVOID (for this layer)** — no need to add a third icon licence when IC-01/IC-03 cover it |

**Recommendation:** use **IC-01** for the five required silhouettes (melee, bow, crossbow, firearm,
zombie) and the money glyph unless the owner prefers the Font Awesome `$`; use **IC-02** for neutral
UI glyphs (time, health, ammo, team). Ship one attribution register generated from
`configs/ui_icon_map.json`.

### 3.2 Fonts (UI labels, kill-feed text, numerals)

| ID | Source | Licence | Modify | Redistribute | Attribution | Constraints | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F-01 | [Inter](https://fonts.google.com/specimen/Inter) — Google Fonts repository `ofl/inter` | **SIL OFL 1.1** (OFL.txt verified) | Yes (font software) | Yes, with OFL notice | Copyright notice + OFL; reserved-name rule on modified font files | Rasterise to `font.dds` atlas; do not commit TTF binaries (keeps repo asset-free); test glyph coverage | **ADOPT** — body/UI text |
| F-02 | [Oswald](https://fonts.google.com/specimen/Oswald) — `ofl/oswald` | **SIL OFL 1.1** (OFL.txt verified) | Yes | Yes, with OFL notice | Copyright (Oswald Project Authors) + OFL | Condensed labels/kill-feed rows; test at 12–16 px | **ADOPT** — condensed labels |
| F-03 | [Cinzel](https://fonts.google.com/specimen/Cinzel) — `ofl/cinzel` | **SIL OFL 1.1** (OFL.txt verified) | Yes | Yes, with OFL notice | Copyright (Cinzel Project Authors) + OFL | Menu/title only (serif caps); not for dense feed text | **ADOPT** — title/menu |
| F-04 | [Rajdhani](https://fonts.google.com/specimen/Rajdhani) — `ofl/rajdhani` | **SIL OFL 1.1** (OFL.txt verified) | Yes | Yes, with OFL notice | Copyright (Indian Type Foundry) + OFL | Numeric/tactical readouts; optional | **ADAPT** — optional numerals |
| F-05 | Native Warband font (`font_data.xml` + `font.dds`) | TaleWorlds game asset | No (not ours) | **No** | — | Must not be captured/redistributed; local build only | **AVOID (bundle)** |

**Font rule of thumb:** rasterised *documents/images* made with the font are not "Font Software" for
OFL redistribution purposes, but the atlas is a derivative of the font; the safe path is to keep the
OFL notice in the credits and never ship a modified `.ttf`. Confirm with Agent E/legal before any
public package.

### 3.3 Textures and materials

| ID | Source | Licence | Modify | Redistribute | Attribution | Constraints | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TX-01 | [Poly Haven](https://polyhaven.com/) — HDRIs, PBR textures, models | **CC0** (licence page: "all licensed as CC0… You can redistribute them") | Yes | Yes | Not required | Use the **asset files**, not their logos/avatars/example renders (those are excluded by the site ToS §4); convert to DDS DXT1/3/5 | **ADOPT** — primary texture/HDRI source |
| TX-02 | [ambientCG](https://ambientcg.com/) — PBR materials, HDRIs, models | **CC0** (docs: "You can include the raw files in your project, for example a video game") | Yes | Yes | Not required | DDS conversion; PBR maps must be reduced to Warband's diffuse/normal/specular expectations | **ADOPT** — primary texture source |
| TX-03 | [cgbookcase](https://www.cgbookcase.com/) — PBR textures | **site statement**: "100% free, no restrictions" (no standard licence name observed) | Yes (per statement) | Yes (per statement) | Not required (per statement) | Not a named licence; keep as *fallback* and record the statement + date per download; prefer TX-01/TX-02 | **ADAPT** — fallback only |
| TX-04 | Kenney texture/kit assets | **CC0** | Yes | Yes | Not required | Good for low-poly style, limited PBR | **ADAPT** — style-dependent |

### 3.4 3D models — weapons, clothing/armour, bodies, hairstyles

| ID | Source | Licence | Modify | Redistribute | Attribution | Constraints | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M-01 | [OpenGameArt — "Low Poly Guns Pack" by quaternius](https://opengameart.org/content/low-poly-guns-pack) (2021-06-18) | **CC0** as published on the OGA page | Yes | Yes | Not required | 40 gun models, FBX/OBJ/Blend; author's own site now uses the restrictive QAL (M-06) — take the **CC0 OGA copy only**, record page + date; low-poly style; needs rescale/rig-to-hand | **ADOPT** — firearm placeholder/first 3D integration |
| M-02 | [KayKit — Adventurers](https://kaylousberg.itch.io/kaykit-adventurers) (free tier) | **CC0** (itch page: "Free for personal and commercial use, no attribution required. (CC0 Licensed)"; asset license field: CC0) | Yes | Yes | Not required | **Free-tier only** (EXTRA/SOURCE are paid tiers — record pack/version and check the included licence); 5 rigged/animated fantasy characters + 25+ weapons/accessories; **fantasy style does not match ZOMBIEEE's modern setting** — dev placeholders only. The "please don't resell unmodified copies" line is a request, not a CC0 restriction | **ADAPT** — dev placeholders |
| M-03 | [KayKit — Skeletons](https://kaylousberg.itch.io/kaykit-skeletons) (legacy/new) | **CC0** (same publisher/licence model; verify per page on download) | Yes | Yes | Not required | Skeleton characters usable as zombie/skeleton stand-ins for tests; fantasy style | **ADAPT** — test stand-ins only |
| M-04 | [Blender Studio — Human Base Meshes v1.4.1](https://www.blender.org/download/demo-files/) | **CC0** (download page: "49 MB – CC0") | Yes | Yes | Not required | **CC0 applies to this bundle only** — Blender demo assets are not site-wide CC0 (splash/Ellie bundles are CC-BY or CC-BY-SA); 17 base meshes (bodies/parts), .blend; no clothing/hair; needs rigging/UV/material work | **ADOPT** — body base for authored survivors |
| M-05 | [MakeHuman](http://www.makehumancommunity.org/content/license.html) + community assets (live site 404; [Wayback 2026-08-27 capture](https://web.archive.org/web/20260827233101/http://www.makehumancommunity.org/content/license.html)) | **Source/data AGPL3**, with an **optional CC0 export**; the licence grants CC0 **only if** (a) the assets were bundled in an export made using the file-export function of an **OFFICIAL and UNMODIFIED** MakeHuman **and/or** (b) the asset consists solely of a **2D binary image in PNG, BMP or JPG** | Yes | Yes **only** for CC0-qualified exports | Not required for CC0 exports | Quote both conditions verbatim and document the MakeHuman build/version + unmodified status per export; modified MakeHuman code stays AGPL (and AGPL §13 network-source obligation applies if ever run as a service — not planned). Use for body/clothing/hair bases | **ADAPT** — only with the export-process rule |
| M-06 | [Quaternius site assets](https://quaternius.com/license.html) | **Quaternius Asset License (QAL) v1.0**, last updated 2026-08-28: may use/modify in products, but **may not resell or redistribute the assets themselves as assets**, original **or modified**, alone or bundled with other assets | Yes (in a product) | **No** (as loose asset files) | Not required | Verified text; applies per asset version at time of download. A module folder containing raw model/texture files is arguably redistribution of the assets as assets even inside a product → exclude from public builds; only a compiled/finished product after legal review | **AVOID (bundle)** |
| M-07 | [Kenney characters](https://kenney.nl/assets) (character/kit packs; per-asset licence page is CC0) | **CC0** | Yes | Yes | Not required | Blocky style; placeholder proportions/rig differ from Warband skeleton | **ADAPT** — placeholders |
| M-08 | [Sketchfab](https://sketchfab.com/) free downloadable models | Per-model licence; **standard** and **editorial** store licences both forbid standalone-file distribution/access; CC0/CC-BY models exist | Per model | Only CC0/CC-BY per model page | Per model | Record licence/author/date per model; reject store/editorial and any "no redistribution" terms; store licences also prohibit promoting **weapons/explosives** (relevant to a zombie/gun mod) and sub-licensing; export formats vary | **ADAPT** — secondary, per-asset verification |
| M-09 | Hairstyles: **authored hair meshes** (Blender sculpt/cards) | Our own work (owner) | Yes | Yes | Project credit | No third-party licence; matches Warband head/skeleton; time cost. This is the most reliable route given the gap | **ADOPT** — preferred hair path |
| M-10 | Hairstyles via **MakeHuman hair assets** (CC0-qualified exports) | CC0 (same condition as M-05) | Yes | Yes | Not required | Process gate as M-05; hair proxies export as meshes; retopo/rig to Warband head | **ADAPT** — alternative hair path |
| M-11 | Blender Studio "Hair Styles" geometry-nodes demo | **CC-BY-SA** (demo-files page) | Yes | Yes, but share-alike | Required | Share-alike would extend to adapted hair assets; avoid for the mod bundle | **AVOID (bundle)** |
| M-12 | Poly Haven models (props, furniture, industrial, environment) | **CC0** | Yes | Yes | Not required | Not characters/weapons; strong for City scene props and texture support | **ADOPT** — environment props |

**Gap statement (honest):** there is no single CC0 source in this pass that covers **modern
survivor clothing/armour and hairstyles at ZOMBIEEE's visual target**. The practical plan is
M-04/M-05 bodies + M-09 authored hair + authored/modular clothing, with M-02/M-07 only as dev
placeholders. Modern tactical clothing remains an **open sourcing gap** (§9).

### 3.5 Sounds

| ID | Source | Licence | Modify | Redistribute | Attribution | Constraints | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S-01 | [Kenney — UI Audio](https://kenney.nl/assets/ui-audio) and [Impact Sounds](https://kenney.nl/assets/impact-sounds) | **CC0** (asset pages read: License "Creative Commons CC0"; site-wide CC0 statement) | Yes | Yes | Not required | UI clicks/beeps and impact hits; .ogg/.wav; trim/normalise; add `module_sounds.py` ids | **ADOPT** — UI + impact |
| S-02 | [OpenGameArt — "The Free Firearm Sound Library"](https://opengameart.org/content/the-free-firearm-sound-library) (Ben Jaszczak, Brian Nelson, Kevin Heras, Matthew Nanney; Kickstarted 2013) | **CC0** ("CC0 NO RIGHTS RESERVED for this library… without royalty or credit") | Yes | Yes | Not required (authors requested courtesy only) | ~194 MB 7z prepared library; large — select a small subset; check sample rate/format and convert; metadata inside files is informative | **ADOPT** — firearm sounds |
| S-03 | [Freesound](https://freesound.org/) | Per-sound **CC0 / CC BY / CC BY-NC**; legacy **CC Sampling+ still exists on old sounds**; per-uploader **July-2026 GenAI preferences** may add conditions | Yes (per licence) | Yes for CC0/CC BY; **no** for NC/Sampling+ | **Required** for CC BY: title, author, sound URL, licence | Filter **per sound** to CC0/CC BY (do not assume Sampling+ is gone); account required to download; record GenAI preference if present (we do not train AI); keep an attribution list; zombie/ambience/foley | **ADOPT** — filtered CC0/CC BY only |
| S-04 | [Sonniss #GameAudioGDC bundle](https://sonniss.com/gdc-bundle-license/) | **Custom EULA v2.0 (effective 2026-08-27)**: synchronised use in finished projects only; **may not distribute/publish/sub-license the effects as effects**, modified or not (explicitly not as files, libraries, asset packs, templates or SDKs); **no AI/ML training**; no attribution required | Yes (in a project) | **No** (as sound files) | Not required | Applies per download date/version; an unpacked mod's `Sounds/` folder is exactly the forbidden supply. Not frictionless | **AVOID (bundle)** |
| S-05 | Nexus/ModDB/other mod sound packs (incl. "Mortal Women Sound Pack", cRPG sound packs) | Per-upload permissions; often "ask author"; may contain rips | Per author | Only with explicit written permission | Per author | Not verified in this pass; do not copy from mod archives; use only as design reference unless permission is recorded | **AVOID** |
| S-06 | BBC Sound Effects / Pixabay / Mixkit / ZapSplat-type sites | Mixed/custom terms; several restrict redistribution as standalone assets | Varies | Varies | Varies | Not verified in this pass; treat as **verify-first/avoid** for a raw mod bundle until terms are read and recorded | **AVOID (for now)** |
| S-07 | Native Warband sounds (hard-coded ids) | TaleWorlds game assets | No | **No** | — | Do not capture/redistribute; private build references the user's install | **AVOID (bundle)** |

### 3.6 Warband community code/design sources (mechanics and pipeline, not asset rips)

| ID | Source | Licence | What it establishes | Reuse position | Decision |
| --- | --- | --- | --- | --- | --- |
| W-01 | [vornne/pw_module_system](https://github.com/vornne/pw_module_system) — Persistent World module system (Python only) | **BSD-3-Clause** (repo `LICENSE.txt` verified: "Copyright (c) 2010 Steven Schwartfeger, Persistent World") | How a real MP mod structures presentations, HUD meshes, sounds, items; UI coordinate space; native-sound warning; custom score/progress/chart overlays | Code reuse permitted with copyright notice + licence text; no art is in the repo; we should still prefer our own implementation and cite the pattern | **ADOPT** — pipeline/design reference; reuse only with BSD notice |
| W-02 | cRPG (Persistent multiplayer economy/progression mod) — [TaleWorlds thread 379486](https://forums.taleworlds.com/index.php?threads/crpg.379486/); "cRPG source code for 1.127" [thread 126175](https://forums.taleworlds.com/index.php?threads/crpg-source-code-for-1-127.126175/); GitHub mirror [epuronta/cRPG-Toolkit](https://github.com/epuronta/cRPG-Toolkit) | Mirror repo: **no licence** (GitHub API `license: null`; archived repository, last push 2012-03-18); source thread terms not re-verified (forum pages Cloudflare-blocked in this pass) | Design source for persistent economy/equipment UI conventions, currency sinks/sources, scoreboard/kill feedback concepts | **Link-only design reference.** Do not copy code, assets, or item/economy tables; do not assume reuse rights | **ADOPT as design reference only** |
| W-03 | FormAI (Motomataru; presentations/order HUD) — as recorded in `reference/WARBAND_AI_COMMUNITY_SOURCES.md` | Reuse not authorized by that record | Presentation-based HUD/order display patterns | Design reference only | **ADAPT as reference only** |
| W-04 | Community "Killstreaks and statistics" OSP code thread (TaleWorlds 449101) and Varena NeoGK (447294) | Terms not verified (Cloudflare-blocked direct fetch) | Evidence that MP mods implement custom kill/stat presentations | Link-only; no copying | **ADAPT as design lead only** |
| W-05 | [Mount&Blade Modding Wiki](https://mbmodwiki.github.io/) (OLL Clan archive) | **Public domain** (site footer: "Content is available under Public Domain") | Official module-system docs, 3D art pipeline, operation list | Can quote/reuse with courtesy citation | **ADOPT** — primary pipeline reference |
| W-06 | Original ZOMBIEEE Beta 0.4 OSP/community credits (Shredzor's OSP, Arch3r's Invasion OSP, Modern Buildings OSP, Thel's OSP, Polished Landscapes, etc.) | **Per-asset terms unknown** (credits are not a licence; see legal dossier §3.3/§4) | Historical provenance only | Do not copy assets; contact authors/record permissions if ever needed | **AVOID as asset source** |

**Never copy unlicensed rips.** A mod archive is not a licence. cRPG/other Warband mods are cited
here for *mechanics and pipeline patterns*, never as an asset source; a pile of `.brf`/`.dds` inside
a mod is not redistributable just because the mod is public.

---

### 3.7 Environment / defensive props (task-64 addendum)

Candidates for City cover/barricades and between-wave upgrades. All must still pass the engine
integration constraints (§2.2–§2.4) and the ownership rules (§1). **Visual validation requires in-game
screenshots** (owner/Lead); none were taken in this docs-only pass.

| ID | Source | Licence | Modify | Redistribute | Attribution | Constraints / notes | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EP-01 | [Poly Haven models](https://polyhaven.com/models) — CC0 prop candidates from the site API (521 models): `concrete_road_barrier`, `concrete_road_barrier_02`, `modular_chainlink_fence`, `old_military_crate`, `Barrel_01`, `Barrel_02`, `barrel_03`, `plastic_crate_01..03`, `wine_barrel_01` | **CC0** (licence page verified: redistribution allowed) | Yes | Yes | Not required | Use the asset files, not preview renders/logos (ToS §4); convert FBX/OBJ→BRF, add collision mesh, check scale and navmesh fit; style/poly suitability is per-asset | **ADOPT** — first environment candidates |
| EP-02 | [Kenney — Survival Kit](https://kenney.nl/assets/survival-kit) (80 models, CC0) | **CC0** (asset page verified) | Yes | Yes | Not required | Contents not itemised in this pass — check the pack's own license file and pick crates/barrels/sandbag-like pieces; low-poly style | **ADAPT** — style-dependent |
| EP-03 | [ambientCG 3D assets](https://ambientcg.com/) (models/terrain, CC0) | **CC0** | Yes | Yes | Not required | General CC0 source; per-asset suitability for cover/barricade geometry must be checked | **ADAPT** — fallback |
| EP-04 | KayKit prop/kit packs (CC0 free tiers) | **CC0** | Yes | Yes | Not required | Fantasy style; placeholders/dev only for modern City props | **ADAPT** — placeholders |
| EP-05 | **Project-authored sandbag/barricade/crate meshes** | Our own work (owner) | Yes | Yes | Project credit | Best route for a public/clean-room build: no third-party licence, full control of collision/navmesh and scale; cost is art time | **ADOPT (preferred for public)** |
| EP-06 | Existing City props (`spr_zombie_sandbag_wall`, barrels, `band_a`, plants, poles) | Native/original-ZOMBIEEE/third-party: **no recorded redistribution right** | No (private build reference only) | **No** (public bundle) | — | Private/local build only; public/clean-room release needs replacement or omission (`reference/LEGAL_RIGHTS_AND_CREDITS.md` R-03/R-05). The task-63 map design records the same boundary | **AVOID (bundle)** |

**Collision/navmesh warning:** a barricade that changes walkable space needs a scene/navmesh update and
D runtime validation; decorative cover that does not block pathing is the lower-risk first step.

### 3.8 Survivor cosmetics / armour / faces / hairstyles (task-64 addendum)

For between-wave upgrades/buying (body/face/hair/clothing/armour variants). The 2D upgrade-UI icons are
separate from the 3D meshes; both must stay licence-clean and be screenshot-validated later.

| ID | Source | Licence | Modify | Redistribute | Attribution | Constraints / notes | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C-01 | **MakeHuman** + community assets ([Wayback 2026-08-27 capture](https://web.archive.org/web/20260827233101/http://www.makehumancommunity.org/content/license.html)) | **AGPL3 source/data; CC0 export only** under the two exact conditions: official **and unmodified** MakeHuman export **and/or** a 2D PNG/BMP/JPG | Yes | Only CC0-qualified exports | Not required for CC0 exports | Process gate per export (build/version, unmodified); bodies, face morphs, hair proxies, clothing bases; retopo/rig to Warband skeleton; AGPL §13 note if ever service-hosted | **ADAPT** — primary base library with the export-process rule |
| C-02 | [Blender Studio — Human Base Meshes v1.4.1](https://www.blender.org/download/demo-files/) | **CC0** (bundle-scoped) | Yes | Yes | Not required | Head/body base only (no clothes/hair); CC0 applies to this bundle, not all Blender demos | **ADOPT** — head/body base |
| C-03 | KayKit Adventurers accessories (free-tier CC0) | **CC0** | Yes | Yes | Not required | Fantasy armour/accessories; dev placeholders only for a modern survivor look | **ADAPT** — placeholders |
| C-04 | **Project-authored modular clothing/armour/hair/faces** | Our own work (owner) | Yes | Yes | Project credit | Best for public/clean-room; matches modern setting and Warband rig; needs art time and screenshot review | **ADOPT (preferred for public)** |
| C-05 | game-icons.net equipment/upgrade icons: `kevlar-vest` (Skoll), `trench-body-armor` (Skoll), `breastplate` (Lorc), `leather-armor` (Delapouite), `armor-upgrade` (Delapouite), `gloves` (Delapouite), `greaves` (Delapouite), `light-helm` (Delapouite), `hoodie` (Delapouite), `hair-strands` (Delapouite), `person` (Delapouite), `barricade` (Delapouite), `wooden-crate` (Delapouite) | **CC BY 3.0** | Yes | Yes | **Required** per icon: "Icons made by {author}. Available on https://game-icons.net" + licence link + changes | 2D upgrade/UI icons only (not 3D models); attribution register required; `docs/ICON_MAPPING.md` §4.6 maps the slots | **ADOPT** — upgrade UI icons |
| C-06 | Reticle overlay candidates: **project-authored** (best) / game-icons `reticule` (Lorc) or `crosshair` (Delapouite) / Font Awesome `crosshairs` (CC BY 4.0) | CC0 (authored) / **CC BY 3.0** (game-icons) / **CC BY 4.0** (FA) | Yes | Yes | Required for CC BY (per-icon/project credit) | **Additive overlay only**; do **not** claim native reticle resize. Screenshot comparison plan in `docs/ICON_MAPPING.md` §10; no binary until cleared; owner+E approval | **ADAPT** — candidate only |
| C-07 | Modern tactical clothing/armour CC0 source | **not verified in this pass** | — | — | — | No single CC0 modern-survivor set found; per-asset Sketchfab CC0 is a last resort (store/editorial excluded); Mixamo/Adobe asset redistribution is not cleared for a mod bundle | **OPEN** — use authored/C-01 bases meanwhile |

Icon page pattern: `https://game-icons.net/1x1/<author>/<icon>.html`; all candidate C-05/C-06 icon pages
were checked on 2026-10-24 (HTTP 200).

---

## 4. Avoid list (with reasons)

| Source / class | Reason |
| --- | --- |
| Original ZOMBIEEE 0.4 assets and its OSP/third-party credits | Per-asset terms unknown; 2012 thread statements about models of other-game origin; private build only (legal dossier R-02/R-03) |
| Any asset ripped from another game (L4D, Call of Duty, etc.) | Copyright infringement; "2012 authors said so" is not a licence |
| Nexus/ModDB/Steam Workshop packs without explicit written permission | Upload permissions vary; archives often mix rips |
| Quaternius site assets (M-06, QAL) | Forbids redistributing assets as assets; an unpacked module is asset files |
| Sonniss GDC bundle (S-04) | Forbids supplying the effects as files |
| Sketchfab store/editorial licences (M-08) | Forbid standalone-file access; mods are unpacked |
| CC BY-SA / GPL / AGPL / CC BY-NC assets | Share-alike/copyleft/non-commercial conflicts with a mixed mod bundle |
| CC BY-ND / legacy CC Sampling+ / unknown custom licences | No-derivatives/share-alike/unknown terms conflict with a modified, mixed bundle |
| "Free for personal use" texture/model/font sites; "free" CDN aggregators | Not a reuse grant for redistribution |
| AI-generated asset packs with unclear training-data provenance | Provenance cannot be audited; owner/legal risk |
| Native Warband UI/item/font/sound assets | **No redistribution right recorded** for this project; treat as non-redistributable and do not bundle (legal dossier R-03/R-05) |
| WSE2 binaries | Third-party runtime with no observed licence grant; users install separately |

---

## 5. Shortlist for first integration

Ordered by *frictionless value per hour*; all items are definitions/prototype-scope only, no binary
commits yet.

| Rank | Item | Why first | Next action |
| --- | --- | --- | --- |
| 1 | **IC-01 game-icons.net** five silhouettes + money glyph | Exactly covers melee/bow/crossbow/firearm/zombie; SVG editable; CC BY only | Generate the attribution register from `configs/ui_icon_map.json`; keep SVGs out of the repo until a licence-cleared asset PR |
| 2 | **IC-03 Font Awesome `dollar-sign`** | Owner wants USD symbol, not a gold coin; single CC BY icon | Use the rasterised glyph from an OFL font first (zero extra licence), FA as fallback |
| 3 | **S-01 Kenney UI/Impact (CC0)** | Instant HUD/hit feedback; zero attribution | Pick 8–12 files, record source page + date |
| 4 | **S-02 OGA Free Firearm Library (CC0)** | Firearm shots/reloads are the mod's core audio | Select a small subset, document source |
| 5 | **TX-01/TX-02 Poly Haven + ambientCG (CC0)** | Scene/prop/UI background textures with the cleanest terms | Convert one test texture to DDS DXT1/DXT5 and note pipeline |
| 6 | **F-01/F-02 OFL fonts** | Kill-feed/labels need a coherent typeface | Rasterise a small glyph set to `font.dds`/`font_data.xml` on a later build task |
| 7 | **M-01 OGA guns (CC0) + M-02/M-03 KayKit (CC0)** | 3D placeholders for weapon/zombie tests without licence risk | Record OGA CC0 provenance; treat style as placeholder |
| 8 | **M-04 Blender base + M-05 MakeHuman (CC0 export) + M-09 authored hair** | Body/clothing/hair pipeline with clear output terms | Document MakeHuman export process before first export |
| 9 | **S-03 Freesound CC0/CC-BY subset** | Zombie/ambience/foley gaps | Filter CC0; if CC BY, fill the attribution template |
| 10 | **EP-01 Poly Haven CC0 props** (`concrete_road_barrier`, crates, barrels, chainlink fence) | First licence-clean environment/cover candidates; CC0 | Pick 1–2 props, export OBJ→OpenBRF, add collision, record source/date; screenshot plan before visual claim |
| 11 | **C-01/C-02/C-04 survivor body/cosmetic base** (MakeHuman CC0 exports + Blender base + authored) | Licence-clean bodies/faces/hair/clothing route; no modern-CC0 off-the-shelf set | Document MakeHuman export process; prototype one male/female cosmetic variant; screenshots for review |
| 12 | **C-05/C-06 upgrade icons + reticle candidates** | Between-wave upgrade UI + additive reticle option with clear attribution | Generate attribution rows from the JSON; screenshot comparison (`docs/ICON_MAPPING.md` §10) before any visual claim |

**Deliberately not in the first integration:** any 3D modern clothing/armour (gap), third-party OSP
assets (terms unknown), native assets (no redistribution right recorded; treat as non-redistributable),
and anything requiring the owner's public/private distribution decision.

---

## 6. Attribution and notices (exact strings to ship)

When assets are eventually added to a public artifact, ship a `NOTICE`/credits block containing at
least:

1. **Icons (CC BY 3.0):** "Icons made by {author}. Available on https://game-icons.net" — one line
   per icon author actually used, with the licence link
   <https://creativecommons.org/licenses/by/3.0/> and a note that icons were adapted (cropped,
   recoloured, rasterised).
2. **Font Awesome (CC BY 4.0):** "Dollar-sign icon by Fonticons, Inc. (Font Awesome Free), licensed
   under CC BY 4.0" + licence link; keep the copyright header in source SVGs.
3. **Fonts (SIL OFL 1.1):** keep each font's copyright line (Inter Project Authors; Cinzel Project
   Authors; Oswald Project Authors; Indian Type Foundry for Rajdhani) and the OFL link
   <https://scripts.sil.org/OFL>.
4. **CC0 sources (courtesy):** "Kenney" (CC0), "Poly Haven" (CC0), "ambientCG" (CC0), "KayKit by Kay
   Lousberg" (CC0), "OpenGameArt contributors (CC0)" — not required, but good practice and useful
   provenance.
5. **Freesound (CC BY case):** `"<sound title>" by <user> ( <sound URL> ), licensed under CC BY 4.0`
   (the site's recommended format).
6. **Free Firearm Sound Library (CC0):** "Firearm sounds by Ben Jaszczak, Brian Nelson, Kevin Heras,
   Matthew Nanney (CC0)" — courtesy.
7. **Persistent World BSD-3:** if any of its code/patterns are reused, reproduce the copyright
   notice, the three conditions and the disclaimer (full BSD-3 text) in the distribution.
8. **No endorsement:** "Not affiliated with or endorsed by TaleWorlds Entertainment, the original
   ZOMBIEEE team, WSE2 authors, game-icons.net, Font Awesome, Kenney, Poly Haven, ambientCG, KayKit,
   MakeHuman or the Blender Studio." Keep nominative use only.
9. **Native assets:** state that no Warband/ZOMBIEEE/native assets are distributed and that users
   supply their own game + original archive (see legal dossier §6).

**Register path (required before the first binary asset PR):** create `THIRD_PARTY_NOTICES.md` at the
repository root (or `docs/CREDITS.md` if the Lead prefers), generated from
`configs/ui_icon_map.json`, with one row per asset: asset/slot, author, source URL, licence + version,
date/version obtained, and the changes made. Today the JSON records
`"attribution": {"generated": false, "noticePath": "THIRD_PARTY_NOTICES.md"}` — the register does not
exist yet. When the owner later chooses a licence for our own code/docs, carve out third-party
components explicitly; a repo without a `LICENSE` does not revoke the CC BY status of the icons.

Do **not** use brand logos (Kenney, Poly Haven, Font Awesome brand icons, etc.) in the mod.

---

## 7. Licence compatibility matrix

| Licence | Modify | Redistribute in mod bundle | Attribution | Share-alike / copyleft | Fit for this project |
| --- | --- | --- | --- | --- | --- |
| CC0 1.0 (public-domain-equivalent waiver + fallback licence) | Yes | Yes | No | No | **Best** |
| CC BY 3.0 / 4.0 | Yes | Yes | **Yes** (+ link, changes) | No | **Good** with register |
| SIL OFL 1.1 (fonts) | Yes | Yes (with notice; RFN rule on modified font files) | **Yes** | Font software only | **Good** |
| Apache 2.0 | Yes | Yes | Yes (NOTICE) | Patent grant, no copyleft | Good (heavier bookkeeping) |
| MIT / ISC | Yes | Yes | Yes (notice) | No | Good |
| CC BY-SA | Yes | Yes | Yes | **Yes** → avoid in bundle | Avoid |
| GPL / AGPL | Yes | Yes | Yes | **Yes** (AGPL network clause) | Avoid for assets |
| CC BY-ND | No (no derivatives) | Yes (unmodified) | Yes | No | Avoid (we modify/convert) |
| CC BY-NC | Yes | Yes | Yes | No commercial use | Avoid |
| Legacy CC Sampling+ | Yes | Yes | Yes | Restricts advertising | Avoid |
| Unknown/custom (incl. "OSP credit only") | Unclear | **No** | Unclear | Unclear | Avoid until written permission |
| QAL v1.0 (Quaternius) | Yes (in product) | **No** (raw assets) | No | No | Avoid for unpacked mod |
| Sonniss EULA | Yes (synced) | **No** (sound files) | No | No | Avoid |
| Sketchfab store/editorial | Limited | **No** (standalone) | Per licence | No | Avoid |
| "Free for personal use" / no licence / "OSP credit only" | Unclear | **No** | Unclear | Unclear | Avoid until written permission |

**Interpretation limit:** this matrix summarises licence texts, not a legal opinion; where the
owner's publication model (private vs public, bundled vs asset-free) is undecided, the safe default
is "no third-party asset is bundled".

---

## 8. Verification log

All URLs fetched 2026-10-24 unless noted.

| Check | Method | Result |
| --- | --- | --- |
| game-icons.net licence/attribution | Read `https://game-icons.net/about.html` (HTTP 200) | CC BY 3.0; attribution wording recorded; author table |
| game-icons icon names/authors | Read tag pages `/tags/weapon.html`, `/tags/gun.html`, `/tags/zombie.html`, `/tags/money.html` (HTTP 200) | Icon ids/authors recorded for the mapping |
| Kenney licence | `https://kenney.nl/support` (HTTP 200) + asset pages (Game Icons, UI Audio, Impact Sounds; HTTP 200, "Creative Commons CC0") | CC0, no attribution required |
| Poly Haven | `https://polyhaven.com/license` (HTTP 200) | CC0; redistribution explicitly allowed; ToS excludes logos/renders |
| ambientCG | `https://docs.ambientcg.com/license/` (HTTP 200) | CC0; raw files in a game project explicitly allowed |
| cgbookcase | `https://www.cgbookcase.com/` (HTTP 200) | Site statement "100% free, no restrictions"; no standard licence name |
| KayKit | `https://kaylousberg.itch.io/kaykit-adventurers` (HTTP 200) | CC0; free tier; contents/format recorded |
| Blender Studio base meshes | `https://www.blender.org/download/demo-files/` (HTTP 200) | Human Base Meshes v1.4.1 — CC0; hair-styles demo is CC-BY-SA |
| MakeHuman | Wayback capture `20260827233101` of `makehumancommunity.org/content/license.html` (HTTP 200) | AGPL3 source/data + CC0 export exception with conditions |
| Quaternius QAL | `https://quaternius.com/license.html` (HTTP 200) | Custom QAL v1.0 (2026-08-28); no raw redistribution |
| OGA Quaternius guns | `https://opengameart.org/content/low-poly-guns-pack` (HTTP 200) | CC0 as published on that page (2021-06-18) |
| Free Firearm Sound Library | `https://opengameart.org/content/the-free-firearm-sound-library` (HTTP 200) | CC0; authors recorded |
| Freesound licences/attribution | `https://freesound.org/help/faq/#licenses` (HTTP 200) | CC0/CC BY/CC BY-NC; attribution format recorded |
| Sonniss EULA | `https://sonniss.com/gdc-bundle-license/` (HTTP 200) | v2.0 (2026-08-27); no supplying effects as files |
| Sketchfab licence | `https://sketchfab.com/licenses` (HTTP 200) | Store licences forbid standalone-file distribution |
| Fonts OFL | `raw.githubusercontent.com/google/fonts/main/ofl/{inter,cinzel,oswald,rajdhani}/OFL.txt` (HTTP 200 ×4) | SIL OFL 1.1 text + copyright lines |
| Font Awesome | `FortAwesome/Font-Awesome/6.x/LICENSE.txt` (HTTP 200); `svgs/solid/dollar-sign.svg` and `gun.svg` (HTTP 200) | Icons CC BY 4.0, fonts OFL, code MIT |
| Material Symbols | `google/material-design-icons/LICENSE` (HTTP 200) | Apache 2.0 |
| Warband pipeline (meshes/textures) | Modding Wiki 3D art pipeline page (HTTP 200, public domain) | OBJ→OpenBRF; DDS DXT1/3/5; sizes multiple of four |
| Warband module system/build stages | Modding Wiki Official Module System Documentation Part 01 (HTTP 200) | Python compiles to game text files; "Exporting meshes/sounds/presentations" |
| Warband UI/presentations/sounds/items | Persistent World source files `module_presentations.py`, `module_meshes.py`, `module_sounds.py`, `module_music.py`, `module_items.py`, `header_items.py`, `LICENSE.txt` (HTTP 200, BSD-3-Clause) | 1000×1000 presentation space; mesh-based UI images; sound formats/flags; item mesh lists; item type flags incl. `itp_type_pistol` |
| Warband font pipeline | Mount&Blade Chinese forum thread 2076056 (HTTP 200) | `font_data.xml` + `font.dds`; BMFont + Swyter XML converter workflow (community) |
| cRPG mirror licence | GitHub API `repos/epuronta/cRPG-Toolkit` (HTTP 200) | `license: null`, archived repo (last push 2012-03-18) → design reference only |
| cRPG/OSP forum threads (direct fetch) | `forums.taleworlds.com` (HTTP 403 Cloudflare) | **external-blocked**; not relied on; cite search-index URLs only |
| Independent review (E) | Cross-review record `reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md` §A + PR #31 review comment (2026-10-24) | **No blockers**; A1/A5–A13 corrections folded into this revision; no legal clearance |
| Poly Haven model candidates | `https://api.polyhaven.com/assets?t=models` (HTTP 200) | 521 models; CC0 candidates listed for EP-01 (barriers, crates, barrels, chainlink fence) |
| Kenney Survival Kit | `https://kenney.nl/assets/survival-kit` (HTTP 200) | CC0, 80 models; contents not itemised in this pass |
| game-icons equipment/upgrade icons | `/tags/armor.html`, `/tags/clothing.html` + HEAD checks of candidate pages (HTTP 200) | ids/authors for armour/clothing/helmet/hair/face/crate/barricade recorded |
| Reticle candidates | `game-icons.net/1x1/lorc/reticule.html`, `.../delapouite/crosshair.html`, Font Awesome `svgs/solid/crosshairs.svg` (HTTP 200) | Licence-cleared candidates; additive overlay only, no native-resize claim |
| Screenshot validation | Not performed (docs-only, no game launch) | Required before any visual/asset acceptance; plan in `docs/ICON_MAPPING.md` §10 |
| Native assets not in repo | `git ls-tree`/`git grep` on branch (`reference/`, `docs/`, `configs/`) | No `.brf/.dds/.wav/.ogg/.ttf/.png` assets added by this task |

---

## 9. Open questions and next actions

1. **Independent review (Agent E) — completed 2026-10-24:** E's cross-review
   ([`reference/CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md`](CROSS_REVIEW_LEGAL_RELEASE_2026-10-24.md) §A and
   the PR #31 review comment) found **no blockers**; corrections A1/A5–A13 are folded into this revision
   (per-icon attribution, free-tier/bundle scopes, MakeHuman's exact two conditions, QAL "even modified",
   Sonniss constraints/version, Sketchfab editorial/weapons rules, Freesound Sampling+/GenAI,
   Font Awesome's three parts, conservative native-asset wording). E's review is **not** legal clearance,
   **not** acceptance and **not** adoption of any ledger leaf.
2. **Owner/legal decision on the publication model** (`reference/LEGAL_RIGHTS_AND_CREDITS.md` §5):
   private-only vs public asset-free vs public bundle decides whether any third-party asset can ever
   be redistributed. Until then, **do not bundle**.
3. **Modern clothing/armour gap (partially addressed in task-64):** §3.8 adds MakeHuman/Blender/
   authored bases + upgrade icons, but no CC0 modern-tactical set is verified; keep authored modular
   clothing as the default and do not use fantasy placeholders in a public build.
4. **OSP permissions:** the original 0.4 credits (Shredzor's OSP, Arch3r, Thel, etc.) remain
   per-asset unknown; contact authors only if the owner wants to reuse them in a public artifact.
5. **Icon production is not implemented:** the mapping is a contract only (see `docs/ICON_MAPPING.md`);
   no atlas/BRF/presentation exists yet, and nothing has been tested in Warband.
6. **Asset register:** before the first binary asset PR, create `THIRD_PARTY_NOTICES.md` from
   `configs/ui_icon_map.json` (see §6) and let release metadata (F/Lead) carry the single CHANGELOG
   entry; a duplicate `[Unreleased]` section was removed from this branch to avoid a version-scheme
   conflict with PR #29 (`0.3.0-rc.1`).
7. **No acceptance claim:** this catalogue does not accept `ZOM-LEGAL-01`, M4, or any City outcome.
8. **Task-64 visual validation is pending screenshots:** the owner/Lead require in-game screenshots
   for any visual/asset validation; none were captured in this docs-only task. The comparison plan is
   `docs/ICON_MAPPING.md` §10. Reticle work stays additive (no native reticle resize claim); any new
   prop/icon needs E review + `THIRD_PARTY_NOTICES` evidence before binaries.
