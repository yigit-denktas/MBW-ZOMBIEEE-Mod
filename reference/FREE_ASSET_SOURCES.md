# Free-to-use asset sources for a Warband mod (cosmetics + icon layer)

**Status:** research catalogue and integration plan. **Docs-only:** no asset binary is downloaded
into, or committed to, this repository; no game launch; no runtime, visual or acceptance claim.
**This is not legal advice and grants no licence.** It records what each source states, the date it
was observed, and the integration constraints that follow.
**Observed:** 2026-10-24, from branch `agent/g-free-assets` (base `main` `c72de64`), owner task
`task-49`.
**Review:** independent licence review by Agent E is required before this catalogue is treated as
reviewed (see §9). Until then this file is a **pre-review draft**.
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

1. **Preferred, in order:** CC0 / public domain → CC BY 3.0/4.0 (with a shipped attribution
   register) → SIL OFL 1.1 (fonts), Apache-2.0, MIT/ISC (code/tools).
2. **Conditional:** licences that allow use *inside a product* but forbid redistributing the assets
   as assets. A Warband module is distributed as loose `Resource/`, `Textures/`, `Sounds/`, `Data/`
   and compiled-text files, so the mod package *is* an asset collection. Treat these as **not
   frictionless**; only use them if the owner decides the whole module is the "product" and legal
   review agrees. They are marked **AVOID (bundle)** below, not "illegal".
3. **Excluded from a distributable bundle:** CC BY-NC, CC BY-SA (share-alike would extend to the
   adapted asset and complicate the whole bundle), GPL/AGPL assets (copyleft and, for AGPL, the
   network clause), "free for personal use", "for non-commercial mods only", and every ripped or
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

### 2.7 Native-asset boundary (do not distribute)

From the engine and the owner's private module, the following are **not ours to publish**:
native UI meshes/textures and native item meshes; native fonts (`font_data.xml`, `font.dds`);
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
| IC-02 | [Kenney — Game Icons](https://kenney.nl/assets/game-icons) (105 icons, 2D) | **CC0** (Kenney support: "all game assets on the asset pages are public domain licensed (CC0)"; asset page: License CC0) | Yes | Yes | Not required (credit "Kenney" appreciated) | General GUI/prompt glyphs, not weapon silhouettes; actual pack contents not inspected on disk in this pass (licence clear regardless) | **ADAPT** — generic UI glyphs only |
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
| M-02 | [KayKit — Adventurers](https://kaylousberg.itch.io/kaykit-adventurers) (free tier) | **CC0** (itch page: "Free for personal and commercial use, no attribution required. (CC0 Licensed)"; asset license field: CC0) | Yes | Yes | Not required | 5 rigged/animated fantasy characters + 25+ weapons/shields/accessories, 1024 atlas; **fantasy style does not match ZOMBIEEE's modern setting** — placeholders/dev only | **ADAPT** — dev placeholders |
| M-03 | [KayKit — Skeletons](https://kaylousberg.itch.io/kaykit-skeletons) (legacy/new) | **CC0** (same publisher/licence model; verify per page on download) | Yes | Yes | Not required | Skeleton characters usable as zombie/skeleton stand-ins for tests; fantasy style | **ADAPT** — test stand-ins only |
| M-04 | [Blender Studio — Human Base Meshes v1.4.1](https://www.blender.org/download/demo-files/) | **CC0** (download page: "49 MB – CC0") | Yes | Yes | Not required | 17 clean base meshes (bodies/parts), .blend; no clothing/hair; needs rigging to Warband skeleton and UV/material work; Blender 4.2+ file | **ADOPT** — body base for authored survivors |
| M-05 | [MakeHuman](http://www.makehumancommunity.org/content/license.html) + community assets | **Source/data AGPL3**, with an **optional CC0 export**: exports are CC0 **only** if (a) produced by an *official, unmodified* MakeHuman export, or (b) the asset is a 2D PNG/BMP/JPG | Yes | Yes **only** for CC0-qualified exports | Not required for CC0 exports | Strict process gate: document the MakeHuman build/version and that it was unmodified; modified MakeHuman or non-export data is AGPL. Use for body/clothing/hair bases | **ADAPT** — only with the export-process rule |
| M-06 | [Quaternius site assets](https://quaternius.com/license.html) | **Quaternius Asset License (QAL) v1.0**, last updated 2026-08-28: may use/modify in products, but **may not resell or redistribute the assets themselves as assets**, including modified form | Yes (in a product) | **No** (as loose asset files) | Not required | Verified text; applies per asset version at time of download. Not suitable for an unpacked Warband module unless the package is a finished product and legal agrees | **AVOID (bundle)** |
| M-07 | [Kenney characters](https://kenney.nl/assets) (character/kit packs; per-asset licence page is CC0) | **CC0** | Yes | Yes | Not required | Blocky style; placeholder proportions/rig differ from Warband skeleton | **ADAPT** — placeholders |
| M-08 | [Sketchfab](https://sketchfab.com/) free downloadable models | Per-model licence; store licences forbid standalone-file distribution; CC0/CC-BY models exist | Per model | Only CC0/CC-BY per model page | Per model | Must open each model page, record licence/author/date, reject store/editorial licences and any "no redistribution" terms; export formats vary | **ADAPT** — secondary, per-asset verification |
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
| S-03 | [Freesound](https://freesound.org/) | Per-sound **CC0 / CC BY / CC BY-NC** (FAQ: three licences; Sampling+ legacy) | Yes (per licence) | Yes for CC0/CC BY; **no** for NC | **Required** for CC BY: title, author, sound URL, licence | Filter to CC0/CC BY only; account required to download; keep an attribution list; avoid NC and Sampling+; zombie/ambience/foley | **ADOPT** — filtered CC0/CC BY only |
| S-04 | [Sonniss #GameAudioGDC bundle](https://sonniss.com/gdc-bundle-license/) | **Custom EULA v2.0 (2026-08-27)**: synchronised use in finished projects only; **may not distribute/publish/sub-license the sound effects as sound effects**, modified or not | Yes (in a project) | **No** (as sound files) | Not required | Explicitly disallows supplying the effects as files/asset packs; an unpacked mod's `Sounds/` folder is exactly that. Not frictionless | **AVOID (bundle)** |
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
| "Free for personal use" texture/model/font sites; "free" CDN aggregators | Not a reuse grant for redistribution |
| AI-generated asset packs with unclear training-data provenance | Provenance cannot be audited; owner/legal risk |
| Native Warband UI/item/font/sound assets | TaleWorlds property; not redistributable |
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

**Deliberately not in the first integration:** any 3D modern clothing/armour (gap), third-party OSP
assets (terms unknown), native assets (not redistributable), and anything requiring the owner's
public/private distribution decision.

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

Do **not** use brand logos (Kenney, Poly Haven, Font Awesome brand icons, etc.) in the mod.

---

## 7. Licence compatibility matrix

| Licence | Modify | Redistribute in mod bundle | Attribution | Share-alike / copyleft | Fit for this project |
| --- | --- | --- | --- | --- | --- |
| CC0 / public domain | Yes | Yes | No | No | **Best** |
| CC BY 3.0 / 4.0 | Yes | Yes | **Yes** (+ link, changes) | No | **Good** with register |
| SIL OFL 1.1 (fonts) | Yes | Yes (with notice; RFN rule on modified font files) | **Yes** | Font software only | **Good** |
| Apache 2.0 | Yes | Yes | Yes (NOTICE) | Patent grant, no copyleft | Good (heavier bookkeeping) |
| MIT / ISC | Yes | Yes | Yes (notice) | No | Good |
| CC BY-SA | Yes | Yes | Yes | **Yes** → avoid in bundle | Avoid |
| GPL / AGPL | Yes | Yes | Yes | **Yes** (AGPL network clause) | Avoid for assets |
| CC BY-NC | Yes | Yes | Yes | No commercial use | Avoid |
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
| Native assets not in repo | `git ls-tree`/`git grep` on branch (`reference/`, `docs/`, `configs/`) | No `.brf/.dds/.wav/.ogg/.ttf/.png` assets added by this task |

---

## 9. Open questions and next actions

1. **Independent review (Agent E):** verify the licence claims in §3, the CC BY/OFL notice strings,
   and the "no raw redistribution" readings for QAL/Sonniss/Sketchfab. Record findings in this file
   or the PR before merge (review loop: G writes, E reviews).
2. **Owner/legal decision on the publication model** (`reference/LEGAL_RIGHTS_AND_CREDITS.md` §5):
   private-only vs public asset-free vs public bundle decides whether any third-party asset can ever
   be redistributed. Until then, **do not bundle**.
3. **Modern clothing/armour gap:** find/verify a CC0 modern-survivor clothing set, or commit to
   authored modular clothing (M-04/M-05 base + M-09 hair). Do not use fantasy placeholders in a
   public build.
4. **OSP permissions:** the original 0.4 credits (Shredzor's OSP, Arch3r, Thel, etc.) remain
   per-asset unknown; contact authors only if the owner wants to reuse them in a public artifact.
5. **Icon production is not implemented:** the mapping is a contract only (see `docs/ICON_MAPPING.md`);
   no atlas/BRF/presentation exists yet, and nothing has been tested in Warband.
6. **Asset register:** before the first binary asset PR, create the register described in §1.4 and
   update `CHANGELOG.md` with the licence evidence.
7. **No acceptance claim:** this catalogue does not accept `ZOM-LEGAL-01`, M4, or any City outcome.
