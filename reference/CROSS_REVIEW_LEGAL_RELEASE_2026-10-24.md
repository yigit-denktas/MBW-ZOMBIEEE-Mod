# Cross-review — G free-asset licence claims, C diagnostics research, F release/legal claims (task-51)

**Reviewer:** Agent E (independent; no self-review). **Date:** 2026-10-24. **Status:** review record for
three drafts/areas — **not acceptance**, not legal advice, docs-only, no game launch.
**Artifacts reviewed:** G's planned `reference/FREE_ASSET_SOURCES.md` + `docs/ICON_MAPPING.md`
(claims supplied in review request; files not yet pushed), C's draft
`reference/MODDER_DIAGNOSTICS_RESEARCH.md` (uncommitted in `.team-c2`), F's current release metadata on
`main` (`VERSION` 0.2.0, `CHANGELOG.md`, `README.md`, `launcher/release_gate.py`; task-50 branch not yet
pushed). Map to `reference/LEGAL_RIGHTS_AND_CREDITS.md` risks R-01…R-15.

**Verification rule:** each licence was fetched from the primary page on 2026-10-24 (Wayback where the
live site failed); no third-party text longer than a short quoted phrase is reproduced here.

---

## A. G's free-asset licence claims — verification and corrections

| # | G's claim | Verdict | Correction / condition to publish |
| --- | --- | --- | --- |
| A1 | game-icons.net CC BY 3.0; credit `"Icons made by {author}. Available on https://game-icons.net"` | **Verified** — [about page](https://game-icons.net/about.html) says Creative Commons 3.0 BY and gives exactly that mention | Attribution is **per icon author**, not just the site: list each author used (Lorc, Delapouite, Skoll, …; authors table on the page). Also state title/where possible + licence link + any edits made. |
| A2 | Kenney CC0, attribution not required | **Verified** — [support page](https://kenney.nl/support): "all game assets on the asset pages are public domain licensed (CC0)… Attribution is not required… Do not use our logo" | Publish per-asset "license file included" caveat and the no-logo rule. Some bundles include contributions — check the pack's own license file. |
| A3 | Poly Haven CC0, explicitly allows redistribution | **Verified** — [license page](https://polyhaven.com/license): CC0; "You can redistribute them… even in a product you sell" | Also note site content **other than the assets** (logos, renders, copy) is not CC0 (ToS §4). |
| A4 | ambientCG CC0, raw files allowed in a game project | **Verified** — [license docs](https://docs.ambientcg.com/license/): "You can include the raw files in your project, for example a video game." | Optional credit text provided on the page; no attribution required. |
| A5 | KayKit (Kay Lousberg) CC0, free tier commercial/no attribution | **Verified** — [itch page](https://kaylousberg.itch.io/kaykit-adventurers): "Free for personal and commercial use, no attribution required. (CC0 Licensed)" | It is **free-tier** CC0; EXTRA/SOURCE are paid tiers — document which pack/version and check the included licence. The "please don't resell unmodified copies or claim them as your own" line is a request, not a CC0 restriction; do not misstate it as a licence term. |
| A6 | Blender Studio Human Base Meshes v1.4.1 CC0 | **Verified** — [demo files page](https://www.blender.org/download/demo-files/): Human Base Meshes v1.4.1, 49 MB, **CC0**, updated 2025-01-20 | Scope it to **that bundle**: Blender demo assets are not site-wide CC0 (splash/Ellie/other bundles are CC-BY or CC-BY-SA). Keep version and bundle URL. |
| A7 | MakeHuman AGPL3 source/data; exports may be CC0 only via official unmodified MakeHuman or 2D PNG/BMP/JPG; condition recorded | **Verified** — [Wayback 2026-08-27 capture](https://web.archive.org/web/20260827233101/http://www.makehumancommunity.org/content/license.html) | Quote the two conditions verbatim: (a) export made using the file-export function of an **OFFICIAL and UNMODIFIED** MakeHuman **and/or** (b) the asset consists solely of a 2D binary image in PNG/BMP/JPG. Mention AGPL §13 network-source obligation if any modified MakeHuman is ever run as a service (not planned). Do not distribute modified MakeHuman code under permissive terms. |
| A8 | Quaternius custom QAL v1.0 (updated 2026-08-28); may not redistribute assets as assets → avoid for unpacked module package | **Verified** — [license page](https://quaternius.com/license.html): QAL v1.0, "Last updated: 8/28/2026"; no resell/redistribute assets themselves, original **or modified**, alone or bundled | Keep the "avoid for an unpacked Warband module package" verdict: a module folder containing raw model/texture files is arguably redistribution of assets as assets even inside a Product. Safest: exclude from public builds; if used at all, only in a compiled/finished Product after review. |
| A9 | Sonniss GDC: no redistribution as sound files; only synchronized in finished projects → avoid raw mod sound folders | **Verified** — [GDC bundle licence](https://sonniss.com/gdc-bundle-license/), **Version 2.0 effective 2026-08-27** | Add the exact constraints: synchronized-in-project only; not as files/libraries/templates/SDKs; **no AI/ML training**; no attribution required. Include version/date because it applies per download date. "Raw mod sound folder" exclusion is correct. |
| A10 | Sketchfab store forbids standalone-file distribution; free CC0/CC-BY downloads need per-model verification; secondary source only | **Verified** — [Sketchfab licence agreement](https://sketchfab.com/licenses) | Add: editorial vs standard licence; no promotion of weapons/explosives (relevant to a zombie/gun mod — avoid marketing use); per-model licence must be recorded; no sub-licensing/standalone files. |
| A11 | Freesound CC0/CC-BY/CC-BY-NC; NC and Sampling+ excluded; attribution format | **Verified** — [Freesound FAQ](https://freesound.org/help/faq/): three current licences; legacy **Sampling+ still exists on old sounds**; attribution example given | Do not assume Sampling+ is gone — filter per sound. Add Freesound's July-2026 GenAI preferences as an extra per-uploader condition (our project is not training AI, but record it). Keep the NC-exclusion policy. |
| A12 | Fonts: Inter OFL 1.1 (bitmap atlas fine; keep OFL notice; no modified font files under Reserved Font Name); Font Awesome icons CC BY 4.0; Material Symbols Apache 2.0 | **Mostly verified** — Inter [LICENSE](https://raw.githubusercontent.com/rsms/inter/master/LICENSE.txt) = OFL 1.1; Material Icons [LICENSE](https://raw.githubusercontent.com/google/material-design-icons/master/LICENSE) = Apache 2.0; Font Awesome [LICENSE.txt](https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/LICENSE.txt) = **icons CC BY 4.0, fonts SIL OFL 1.1, code MIT** | Split Font Awesome into its three components; note **brand icons are trademarks** and not licensed by CC BY; keep OFL notice + copyright with font files, Apache NOTICE/licence for Material, CC BY attribution for FA icons. Rasterised bitmap atlases are not the font software, but keep notices as good practice and never redistribute modified fonts under a Reserved Font Name. |
| A13 | Native Warband UI meshes/textures/item meshes are TaleWorlds assets, not redistributable; public repo references replacements; private local build may use native references without bundling | **Verified as the correct conservative position** — Warband copyright strings in the original module; [Warband Steam EULA](https://store.steampowered.com/eula/48700_eula_0) | Phrase as "no redistribution right recorded; treat as non-redistributable and do not bundle" rather than a legal determination. A private/local build may reference installed native data; any public package must exclude native assets. |

### G's specific questions

**(a) Anything I would not publish as stated?** Not the core licences, but publish these corrections:
A1 per-icon author credit; A5 free-tier scope; A6 bundle scope (not site-wide CC0); A7 exact two
conditions; A8 include "even modified" and the unpacked-module risk; A9 version/date + AI-training +
synchronized-only wording; A10 editorial/weapons-promotion restrictions; A11 Sampling+ still present +
per-sound filter; A12 FA three-part split + trademark caveat.

**(b) Is CC BY 3.0/4.0 compatible with our repo having no `LICENSE` yet?** **Yes for embedding**, because
CC BY is attribution-only (no share-alike, commercial use allowed). Requirements to publish:
appropriate credit (author + source URL + licence link + title if supplied), a link to the licence, and
an indication of changes; no additional restrictions may be imposed on the icons. A repo without a
`LICENSE` does not revoke the icons' CC BY status — but keep a **`THIRD_PARTY_NOTICES.md`** (or
`docs/CREDITS`) with a per-asset table (asset, author, source URL, licence, date/version, changes). When
the owner later chooses a licence for our own code/docs, carve out third-party components explicitly.
Do **not** describe CC0 as "public domain" in every jurisdiction — say "CC0 1.0 (public-domain-equivalent
waiver with fallback licence)".

**(c) Exclude CC BY-SA and GPL/AGPL?** **Yes.** Also exclude CC BY-NC, CC BY-ND, legacy Sampling+,
Sonniss raw assets, Quaternius QAL assets for an unpacked package, Sketchfab store assets, and any
unknown/custom licence. Allowed set for the catalogue/icon layer: **CC0, CC BY (3.0/4.0), SIL OFL 1.1,
Apache 2.0, MIT** — each with the notices above. Engine/runtime code (WSE2, FormAI lineage) stays
link-only, never vendored.

**Recommended notice snippet for icon/font use:**

```text
Third-party assets: <asset> by <author> <source URL>, licensed under <CC BY 4.0 / CC0 / OFL 1.1 /
Apache 2.0>; changes: <none|recoloured|re-exported>. Full list in THIRD_PARTY_NOTICES.md.
```

---

## B. C's `MODDER_DIAGNOSTICS_RESEARCH.md` — licence/privacy review

**Scope:** licence claims, `rgl_log` privacy, copied/attached content. No acceptance claim.

| # | Finding | Severity | Required change |
| --- | --- | --- | --- |
| B1 | **`log_rgl` is misread.** The WSE2 changelog bullet "rename `_log` to `log_rgl`" sits under the **Lua** section — it is a Lua API rename (`game._log` → `game.log_rgl`), **not evidence that the engine log file was renamed**. The community op description for `display_debug_message` (opcode 1104) still says it writes to **`rgl_log.txt`** in the program directory. | Medium (factual) | Reword: "WSE2 1.1.x changelog lists a Lua API rename `_log`→`log_rgl`; `rgl_log.txt` remains the engine log per the op docs. Verify actual filenames on our pinned install." Do not present `log_rgl` as the log filename. |
| B2 | **"`display_debug_message` … writes when edit mode is enabled"** over-reads the source. The wiki says op 1104 writes `<string_id>` into `rgl_log.txt` **and displays it with a colour code in debug mode**; "edit mode" is not in that description. | Low | Split into: writes to `rgl_log.txt` (per op docs) / displays in debug mode. Mark any `bEditMode` coupling as unverified. |
| B3 | **Privacy plan for `rgl_log` capture is under-specified.** The doc proposes capturing the log tail + SHA but does not state redaction/bounding/no-commit rules. Engine logs can contain local paths, account/server identifiers, server names/passwords (if misconfigured), chat, IPs. **No copied/attached content was found in the draft** (short quotes + opcode facts only), and the local `dedicated_help.txt` is a local-only artifact. | High if implemented without rules | Add explicit rules: bounded tail (max bytes/lines), **redact or exclude** Windows/UNC/POSIX paths, usernames, server names/password lines, IPs, chat; hash the redacted artifact; keep under `local/`/`evidence/` (gitignored); never commit/upload; privacy review before any share; document the redaction in the receipt. |
| B4 | **Unverified assertions stated as fact:** "WSE2 exposes behavior setters/viewers but no per-agent AI-mode readback"; "no standard community schema exists". Also crash-named log files are "community observation". | Low–Medium | Label as "none found in reviewed sources / not independently verified"; keep them as gaps/unknowns, not engine facts. |
| B5 | **Source licence of the operation mirror:** `Veehats/WarbandCoop/header_operations.py` has **no detected licence**; the draft notes "opcode definitions only". | Low | Cross-check only, no copying; prefer the public-domain Modding Wiki DB + WSE2 SDK; if any table is reproduced, keep it factual/minimal and cite both. |
| B6 | **ZeroBrane MIT claim** is plausible but the draft links the site only. | Low | Link the repository LICENSE (MIT) if the claim stays; otherwise say "MIT per project site (not re-verified)".
| B7 | **WSE2 no-LICENSE claim is correct**: release repo root has no LICENSE (`gh api .../license` → 404). Stats/profiler/mission-debug claims match the changelog (`bShowRenderStats`, `bShowSimulationStats`, `iRenderStatsLogInterval`/`iSimulationStatsLogInterval` config names, profiler ops 3040–3043, `wse_mission_debug_window`). `execute_server_console_command` 3514 exists in the SDK addon. | — | Keep; cite the changelog lines/version for each. |

**Verdict:** C's draft is link-only and contains no copied code; after B1–B4 corrections it is safe to
publish as a research reference. It must not claim observed runtime behaviour (it does not) and must not
turn the `rgl_log` idea into a collector without the B3 privacy rules.

---

## C. F's release/legal claims — current `main` review (task-50 branch not yet pushed)

**Reviewed:** `VERSION` 0.2.0; `CHANGELOG.md`; `README.md` status block; `launcher/release_gate.py`;
`launcher/install.py` (backup/rollback/journal); privacy scan of release-facing text; generated progress
block. **F's `agent/f-release-semver` branch currently equals `main`; no task-50 diff was available.**

| # | Finding | Severity | Required change |
| --- | --- | --- | --- |
| C1 | **Version/traceability stale.** `VERSION` = 0.2.0 while post-0.2.0 work is merged (C AI research/telemetry, legal dossier, M2 installer gates, task-38/42 behaviour). `CHANGELOG` 0.2.0 entries contain **no PR/commit links** (grep found none). | Medium | Task-50's planned 0.3.0 bump and per-entry PR/commit links are needed; release-check should surface missing links. Do not call the version an acceptance. |
| C2 | **Generated README progress block is stale:** "Observed 2026-10-24 against `c5619993`" while `main` is `3a9b859`; the block also states "8/23 · 34.8%". | Medium | Refresh the generated block at the release commit or make it revision-aware; a stale observation revision is a truthfulness defect in release-facing content. |
| C3 | **Ambiguous runtime wording (over-read risk):** CHANGELOG says "Native allied defender spawn 981..984, group/division adoption path, scripted-destination movement and per-round respawn top-up"; README says "native allied defenders". The ledger says spawn is proven but **division 5–7 adoption / hold is unobserved** (DISC-28). | Medium | Reword to "spawn proven; division/hold adoption **unobserved**; scripted movement/refill implemented — candidate only". |
| C4 | **Privacy gate gaps:** `launcher/release_gate.py` personal-path/secret scan **skips `tests/` and `reference/`** (`SCAN_ALLOWLIST_PREFIXES`), uses a Windows-only `C:\Users\…` regex, and lacks UNC/POSIX patterns, entropy checks for unknown tokens, and a test that an allowlisted directory cannot hide a leak. | Medium (defence-in-depth) | Narrow/remove the allowlist or scan all tracked text with explicitly justified exceptions; add `/home/`, `C:/Users/`, `\\\\server\\`, `file://`, and token patterns; add negative-channel tests. |
| C5 | **Release-facing text privacy is otherwise clean:** no actual personal paths, serial keys, tokens or logs found in `README.md`, `CHANGELOG.md`, `docs/WINDOWS_BOOTSTRAP.md`, `docs/PROVENANCE.md`; the installer journals/receipts are documented as private local evidence. | — | Keep the policy; add a test that would catch a future leak. |
| C6 | **Legal/attribution links:** README/CHANGELOG say "redistribution remains uncleared" (honest), but README attribution links only PROVENANCE, not the new `reference/LEGAL_RIGHTS_AND_CREDITS.md`; release gate does not check attribution/NOTICE presence. | Low | Link the legal dossier; add a release-gate check for attribution/NOTICE and for `LICENSE`/`THIRD_PARTY_NOTICES` **presence status** (absence must be reported, not silently pass). |
| C7 | **Installer claims are implementation-backed:** `launcher/install.py` documents/contains backup-first activation, journal, rollback-to-backup and retained trees; the CHANGELOG phrase "backup-first install/rollback" is consistent as an **implementation candidate**, not runtime acceptance. | — | Add "candidate gate; not acceptance" where the release notes could read as runtime proof. |
| C8 | **Legal claims match the dossier:** no redistribution claim; redistribution/legal gate explicitly open; no assets in Git (repo scan). The missing pieces are owner decisions (publication model, repo `LICENSE`) and the third-party-asset risk R-03. | — | Keep; do not move `ZOM-LEGAL-01` until owner acceptance. |

**Privacy/legal verdict for F's current state:** no privacy leak found in the reviewed files; version,
generated-progress revision, adoption wording, and the release-gate allowlist are the items to fix before
task-50 is merge-ready. Re-review the actual 0.3.0 branch/SHA when F pushes it.

---

## D. Consolidated must-fix list (pre-publication / merge)

1. **G:** apply A1, A5–A12 wording corrections; keep CC BY per-icon attribution and a
   `THIRD_PARTY_NOTICES.md`; exclude CC BY-SA/NC/ND/Sampling+/GPL/AGPL/unknown; keep native assets
   reference-only; state Quaternius/Sonniss/Sketchfab exclusions.
2. **C:** fix B1 (`log_rgl` = Lua API, not log filename), B2 (`display_debug_message` wording), B3
   (rgl_log redaction/bounded/no-commit rules), B4 (mark unverified claims unknown); keep link-only and
   public-domain/wiki + WSE2 SDK citations.
3. **F:** bump/link version and CHANGELOG entries; refresh the generated README progress block revision;
   qualify adoption wording; harden the release-gate privacy scan and add attribution/NOTICE checks;
   re-review after the 0.3.0 branch is pushed.
4. **All:** map remaining legal risks (R-01 owner-attested permission, R-02 OSP terms, R-03 third-party
   asset provenance, R-07 no repo LICENSE) to `reference/LEGAL_RIGHTS_AND_CREDITS.md`; no acceptance
   claims, no game launch.

## E. Verification log

| Check | Method | Result |
| --- | --- | --- |
| game-icons / Kenney / Poly Haven / ambientCG / KayKit / Blender / Quaternius / Sonniss | live licence pages fetched 2026-10-24 | verified as in §A |
| MakeHuman | live URL 404; Wayback capture 2026-08-27 | verified exact conditions (§A7) |
| Sketchfab / Freesound / OpenGameArt firearm library | live pages fetched 2026-10-24 | verified; additions in §A10–A11 |
| Font Awesome / Inter / Material Symbols | raw LICENSE files fetched | FA = icons CC BY 4.0 + fonts OFL + code MIT; Inter OFL 1.1; Material Apache 2.0 |
| WSE2 repo licence | `gh api .../license` | 404; root tree has no LICENSE |
| WSE2 changelog claims | `CHANGELOG.MD` fetched | stats config, profiler ops, mission debug, Lua `_log`→`log_rgl` verified in context (Lua section) |
| `display_debug_message` 1104 | Modding Wiki op table | writes `rgl_log.txt`; displays in debug mode (B1/B2) |
| `execute_server_console_command` | WSE2 SDK addon | op 3514 present |
| Release metadata | `VERSION`, `CHANGELOG.md`, `README.md`, `launcher/release_gate.py`, `launcher/install.py` at `main` | findings §C |
| Privacy scan of release-facing text | grep for paths/tokens/serials | no leak found; gate allowlist weakness found |
| G/F drafts | worktree/branch inspection | G files not yet pushed; F branch == main; re-review requested |

**No acceptance claims. No game launch. No third-party code/assets copied. Findings are advisory to G/F/C
and the Lead; the owners decide changes.**
