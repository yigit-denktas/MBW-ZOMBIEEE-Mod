# Warband AI / behavior modding — community source pack (cited)

**Task:** task-36 (Agent E). **Purpose:** verified, cited source inventory for Agent C's task-35
AI research (`reference/WARBAND_AI_MODDING.md`) and for task-30/34 behavior work.
**Ownership:** C owns synthesis, prototypes and implementation; this file owns **source
verification, credits and reliability limits**.
**Observed:** 2026-10-24 against `main` `8c7c932`.
**Policy (hard):** **link-only.** No community code, scripts, constants or assets are copied into
this repository; nothing was installed or executed; no game was launched. Community sources are
evidence for *semantics and pitfalls*, not ready-made code. Re-implement independently from
documented operations; respect each source's permissions (summary in §9).

---

## 0. How to read this file

- **"What it establishes"** is limited to what was directly observed on the cited page/file; it is
  not a design recommendation. C decides what to use.
- **"Limits"** records why a source cannot be treated as current/authoritative on our build
  (Warband **1.174** + **WSE2 1.1.5.4**): era mismatch, engine differences, player reports vs
  measured behavior, missing licence, link rot.
- **Live pages are frequently bot-blocked** (TaleWorlds/Nexus use Cloudflare). Every blocked source
  below also has a Wayback capture or an explicit "unverified" label.
- **Dates in source evidence** are the source's own dates; "observed" dates are ours.
- **Project-internal context (not community sources):**
  [ORIGINAL_0.4_BEHAVIOR.md](ORIGINAL_0.4_BEHAVIOR.md) (original wave/troop/AI data),
  [CITY_SURVIVOR_AI_BEHAVIOR_CONTRACT_2026-10-24.md](CITY_SURVIVOR_AI_BEHAVIOR_CONTRACT_2026-10-24.md)
  (our current orders contract), [docs/BOT_RECON.md](../docs/BOT_RECON.md) (original bot call graph).

---

## 1. Canonical community AI mod — Motomataru's "Formations and AI" compilation

> **Important name check:** no GitHub repository named "FormAI", "Battle AI" or "Native AI" for
> Warband was found. Those names correspond to the **three minimods inside Motomataru's
> compilation** below, plus a "Native AI with formations" option. Do not attribute them as three
> independent projects.

| Field | Value |
| --- | --- |
| Source | Nexus Mods — *Formations and AI with Campaign AI - Compiled for Native* |
| Live URL | <https://www.nexusmods.com/mbwarband/mods/2475> (HTTP 403 to automated fetch, observed 2026-10-24) |
| Verified via | Wayback capture **2025-03-10**: <https://web.archive.org/web/20250310050221/https://www.nexusmods.com/mbwarband/mods/2475> |
| Author / uploader | **Motomataru** (created and uploaded by motomataru) |
| Versions | original upload 2011-01-05; "Compiled for WB **1.153** 09/16/2012"; last updated 2017-02-14; version **1.168** |
| What it establishes | "Playable compilation of three minimods by motomataru: (1) a formations mod, (2) an extension mod to replace Native Battlefield AI, (3) a collection of tweaks and fixes for Native Campaign AI." Description: "Native AI is given the ability to make the same formations. The formations AI replaces Native AI. It makes decisions based primarily on army size rather than army composition. Each type of unit has different objectives." |
| Community variants | The related forum poll (source D1) offers exactly: **Formation AI** / **Native AI with formations** / **Native AI** — i.e. the "FormAI / Battle AI / Native AI" family is this lineage. |
| Credits (from file page) | **Mirathei** — original concept and code; **Caba'drin** — order menu interface, conversion to slots, weapon swing strip, division typing, much more; **Sphere** — modmerger installation system, auto options menu, suggestions; **Rubik** — portions of Improved Autoloot; **Idibil** — use in Brytenwalda; **Othr, Dunde, Treebeard, WindyPlains** — fixes; **Brytenwalda betatesters**; **HokieBT** — hosted AI prototype in SWC; and other players. |
| Permissions (from file page) | **Upload: not allowed to other sites under any circumstances.** **Modification: must get permission from the author.** Conversion: not allowed. Asset use: must get permission. No sale/paid use. |
| Limits | Warband 1.1xx era (2011–2017), **not** WSE2 1.1.5.4/Warband 1.174-verified; distributed as a compiled mod, not a maintained source library; strict permissions mean **link-only** for us. Its behavior claims are the author's, not measured on our build. |

**Use for our project:** a lead for *which behaviors are worth modelling* (formations, unit-type
objectives, battlefield vs campaign AI separation) and *what community AI code looks like* — not
code to import. Any behavior we adopt must be independently expressed in native ops documented in
§3/§5 and validated by D.

---

## 2. FormAI code artifact inside a community mod repo (credits + licence caution)

| Field | Value |
| --- | --- |
| Source | GitHub — `cvlc/tgsmod` (*The Gathering Storm*, a Wheel of Time mod, beta) |
| URL | <https://github.com/cvlc/tgsmod> |
| Observed | repository metadata 2026-10-24: last push **2015-12-13**, no repository licence detected (`NOASSERTION`), but a `license.txt` exists |
| FormAI files present | `formations_presentations.py`, `formAI_constants.py`, `formAI_scripts.py`, `formAI_mission_templates.py` (plus `formations_*` variants) |
| File attribution (verified header) | `formations_presentations.py`: **"Formations AI for Warband by Motomataru — rel. 05/03/10 — EDIT FOR ORDER DISPLAY 11/19/10 by Caba'drin"**. `formAI_constants.py`: **"Formations AI by Motomataru — rel. 12/26/10"**. |
| What it establishes | Confirms the FormAI lineage is *custom module-system logic* (presentations + mission-template triggers + scripts), not a native engine AI opcode. It exposes tunable parameters, e.g. in `formAI_constants.py`: `AI_long_range = 13000` (comment: "do not put over 130m if you want archers to always fire"), `AI_firing_distance`, `AI_charge_distance = 2000`, `Hold_Point = 100` ("archer hold if outnumbered"), battle phases (`BP_Setup`, `BP_Jockey`, …), `AI_Max_Reinforcements = 2`, `AI_Replace_Dead_Player = 1`. |
| Licence analysis | Repo `license.txt` covers **TGS mod-specific assets** under a modified 2-clause BSD ("Copyright (c) 2012, TGS Mod Team and contributors") requiring full credit retention. FormAI inside it is **third-party work** by Motomataru/Caba'drin/others; TGS's licence does not clearly grant rights to it, and Motomataru's Nexus permissions (modification/asset use require permission, no reupload) still govern his work. **Conclusion: link-only; do not copy these files, constants or their exact code blocks.** |
| Limits | 2010–2015 code for Warband 1.1xx module system; depends on order-menu presentations/`module_constants`; unverified under WSE2. Downloading/inspecting is fine; reuse is not authorized by this record. |

---

## 3. Mount&Blade Modding Wiki — public-domain operation and authoring references

| Field | Value |
| --- | --- |
| Source | *Mount&Blade Modding Wiki* static archive, <https://mbmodwiki.github.io/> (archive of the OLL Clan wiki, 2012–2015; repository last pushed 2020-04-26) |
| Licence | Main Page states: **"All the contributions herein are released as public domain."** (still retain author credit where the page names one) |
| Reliability | Warband-era (mostly 2011–2014) community documentation; opcode database predates WSE2 and some ops were later extended by WSE2 (see §5). Good for *names/arity/semantics*, not proof of current engine behavior. |

Verified pages:

| ID | Page | What it establishes | Limits |
| --- | --- | --- | --- |
| W1 | [List of operations](https://mbmodwiki.github.io/List_of_operations) | Opcode database generated by Swyter/Theoris + contributors (page says generated **2011-03-19** from the M&B Command Database). Confirms the base ops C needs, with opcodes: `team_give_order` **1790**, `team_set_order_position` **1791**, `agent_set_scripted_destination` **1730**, `agent_set_speed_limit` **1736**, `agent_set_division` **1783**, `agent_set_group` **1766**, `agent_set_defend_action` **1746**, `agent_force_rethink` **1732**, `agent_get_ammo` **1727**, `agent_set_ammo` **1776**. **`agent_set_ai` and `agent_set_weapon_mode` are not present** in this database — do not assume those names. | 2011 M&B-era DB; opcode numbers/arity can be stale for WSE2; cross-check against WSE2 SDK and the local compiled headers. |
| W2 | [Operation](https://mbmodwiki.github.io/Operation) | Defines "operation" and the category taxonomy of the module scripting language (conceptual baseline). | Conceptual only, no engine behavior. |
| W3 | [Official Module System Documentation: Part 01](https://mbmodwiki.github.io/Official_Module_System_Documentation:_Part_01) (Parts 1–10 exist) | Baseline module-system concepts, file layout and compile workflow; useful to explain why AI behavior lives in `mission_templates`/`scripts`/`presentations`. | Warband-era docs; not WSE2-specific. |
| W4 | [Adding new multiplayer faction](https://mbmodwiki.github.io/Adding_new_multiplayer_faction) | Has explicit sections **"Multiplayer Ai Troops"** and **"Multiplayer Player Classes"**: multiplayer AI troops are ordinary `_multiplayer_ai` troop records assigned to a faction, and bots are drawn from the team's faction. This is the mechanism our `native_roster_patch` uses to make team-1 bots native Zombies. | Community tutorial, not engine guarantee; entity/table formatting may differ; behavior still needs engine evidence. |
| W5 | [Client and Server Events](https://mbmodwiki.github.io/Client_and_Server_Events) | Multiplayer mental model: which code runs client vs server and how events are synchronized (written by **Yoshiboy**, for the "Hunt" mod era). Relevant to not putting behavior logic on clients. | Older multiplayer workflow; dedicated-host specifics need WSE2/1.174 verification. |
| W6 | [Agent regeneration script](https://mbmodwiki.github.io/Agent_regeneration_script) | Example community script with explicit **Credit** and **Forum Link** sections (coded by **cdv**); shows the community credit convention and the singleplayer caveat. | Singleplayer example; not AI behavior; no multiplayer validation. |

Also present but not reviewed in depth: `Operations`, `Definition of terms`, `Category:Script`,
`Category:Module System`. `mbcommands.ollclan.eu` (original command DB referenced by W1) was not
relied on; the archived wiki mirror is the stable citation.

---

## 4. TaleWorlds forum threads — community practice, behavior reports and pitfalls

All live thread pages are Cloudflare-blocked to automated clients (observed 2026-10-24); each entry
was verified from a Wayback capture. Forum posts are **player/author opinions and reports**, not
measurements on our build.

| ID | Thread | Verified metadata | What it establishes / useful content | Limits |
| --- | --- | --- | --- | --- |
| D1 | [Formations AI](https://forums.taleworlds.com/index.php?threads/formations-ai.251520/) ([Wayback 2023-10-23](https://web.archive.org/web/20231023052806/https://forums.taleworlds.com/index.php?threads/formations-ai.251520/)) | Start **2012-10-17**, thread starter **Leifdin** (Floris Mod Pack subforum) | Poll options are the community taxonomy: **Formation AI / Native AI with formations / Native AI**. Posts report concrete pitfalls: formation AI hesitates to charge, retreats to reform on reinforcements, archers vs infantry dynamics, and degraded behavior at battle size >150 on maps designed for smaller fights. Useful as *failure-mode checklist* for any hold/formation design. | Player opinions; Warband 1.15x/Floris era; no code, no licence grant. |
| D2 | [AI formation settings: formations AI or formations with native?](https://forums.taleworlds.com/index.php?threads/ai-formation-settings-formations-ai-or-formations-with-native.294677/) | Start **2014-01-14**, thread starter **stigma** | Community trade-off discussion between formations AI and native AI; useful framing for "hold vs charge" behavior decisions. | Discussion only; no code; no measurements. |
| D3 | [\[WB\] Competitive-style combat AI — Playable version (0.2)](https://forums.taleworlds.com/index.php?threads/wb-competitive-style-combat-ai-playable-version-0-2-out.363466/) | Start **2017-04-03**, thread starter **Oliveran** | A later community combat-AI mod project; relevant as evidence that AI combat behavior is moddable and as a source of stated behavior goals/pitfalls. | Thread claims; code distribution/licence not verified; not WSE2. |
| D4 | [Battlefield Tactics kit. Multiple formations per team + command revamp!](https://forums.taleworlds.com/index.php?threads/battlefield-tactics-kit-multiple-formations-per-team-command-revamp.34685/) | Start **2008-04-03**, thread starter **Mirathei** (OSP kit) | Early community formation/command kit; Mirathei is also credited in Motomataru's compilation (§1) as "original concept and code". Useful history of team-order/command modelling. | 2008 M&B-era; OSP terms are stated in the thread — read them before any reuse; link-only here. |
| D5 | [Warband Script Enhancer 2 (thread)](https://forums.taleworlds.com/index.php?threads/warband-script-enhancer-2-v1-1-4-2.384882/) | Start **2019-06-27**, thread starter **K700**; 143 pages when captured | Official WSE2 discussion/support thread. The WSE2 SDK README points to a specific documentation post: `…/warband-script-enhancer.384882/#post-9126370`. Use for WSE2-specific behavior questions, not as an AI design source. | Very long thread; version drift (v1.1.x); forum search/quote tooling needed. |

Not relied on: a Chinese-language forum thread on battlefield behavior-control research
(`bbs.mountblade.com.cn/thread-2111625`) was seen in search results but not translated/reviewed —
recorded as **unverified pointer**, not evidence.

---

## 5. WSE2 docs — pinned runtime 1.1.5.4 (Ruslan-700/WSE2-Releases)

WSE2 is our **engine target**, so its documented options/ops override older community assumptions.

| ID | Source | Verified facts | Relevance / limits |
| --- | --- | --- | --- |
| S1 | [Release v1.1.5.4](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4) | Published **2026-10-14**; assets `WSE2.zip`, `WSE2_Installer.exe`, `WSE2_WFaS.zip`, `WSE2_WFaS_Installer.exe`. Changelog includes `[Battle]` options **`bDegradeBrokenShields`**, **`iRangedBumpStun`** ("keeps an attacker's bump from stunning a ranged agent who is blocking"), **`bRainAffectsFirearms`**, and **removes `bParry`** ("never entered the parry state"); Lua `OnConversation*` callbacks; fixes for `store_random_in_range` 64-bit bounds and frame-rate-dependent attack/block inputs. | Directly relevant to blocking/parry and AI ranged behavior; these are **config semantics**, not AI policy. Our build must pin the same release; no licence field observed on the repo. |
| S2 | [WSE2 README](https://github.com/Ruslan-700/WSE2-Releases/blob/master/README.md) | Describes WSE2 as a reimplementation/extension of the engine with new scripting ops, triggers, Lua; links the official forum thread. | High-level; no AI guarantees. |
| S3 | [WSE2 SDK `README.txt`](https://github.com/Ruslan-700/WSE2-Releases/blob/master/Warband/WSE2%20SDK/README.txt) | "To enhance the module system, add the contents of the `_addon` files to your original module files. Some files (`header_operations_addon.py`) require that you append their contents at the end of the original file." Points documentation to the forum post above. | Shows WSE2 extensions are **additive** and must be merged into module headers; relevant to any op availability assumption. |
| S4 | [WSE2 SDK `header_operations_addon.py`](https://github.com/Ruslan-700/WSE2-Releases/blob/master/Warband/WSE2%20SDK/header_operations_addon.py) | Contains WSE2-added/extended operations, e.g. `break_loop`, `continue_loop`, extended `try_for_agents`, `is_vanilla_warband`, position-rotate extras. **The AI/order ops in §3 (team orders, scripted destination, speed, defend, division/group, ammo) are not redefined here**, so their base semantics should be assumed from native docs but verified in engine. | Addon list is not a complete reference; absence here ≠ absence in engine. |
| S5 | [WSE2 SDK `header_triggers_addon.py`](https://github.com/Ruslan-700/WSE2-Releases/blob/master/Warband/WSE2%20SDK/header_triggers_addon.py) | WSE2-specific trigger definitions. | Needed when writing triggers that rely on WSE2 events; not AI policy. |
| S6 | [WSE2 SDK `luaGuide.html`](https://github.com/Ruslan-700/WSE2-Releases/blob/master/Warband/WSE2%20SDK/luaGuide.html) | Lua scripting reference bundled with the SDK (also present locally in the owner's pinned WSE2 install). | Instrumentation path (telemetry) — behavior changes still go through module ops/triggers. |

**WSE2 licence note:** the release repository shows no repository licence field and distributes
third-party engine binaries; **link-only, never redistribute WSE2 binaries in this repo**. The SDK
addon files are documentation for modders; we cite them, we do not vendor them.

---

## 6. Operation-definition mirrors (cross-check only — no licence detected)

| ID | Source | Observed | Use | Limit |
| --- | --- | --- | --- | --- |
| G1 | [Veehats/WarbandCoop `header_operations.py`](https://github.com/Veehats/WarbandCoop/blob/main/header_operations.py) | 153,987 B; repo pushed 2025-04-13; **no licence detected** | Cross-check modern opcode names/arity for multiplayer scripting. | No licence → link-only; mirrors can drift from WSE2. |
| G2 | [CaueVaranda/Warband-Module-System `header_mission_templates.py`](https://github.com/CaueVaranda/Warband-Module-System/blob/main/header_mission_templates.py) | 4,561 B; repo pushed 2026-06-27; **no licence detected** | Cross-check mission-template/order constants. | No licence; community port, not official. |
| G3 | [LilyModzStuff/warband_mod_source `source/compiler.py`](https://github.com/LilyModzStuff/warband_mod_source/blob/master/source/compiler.py) | Repo pushed 2022-09-08; no licence detected | Used by task-33 only to confirm the compiled `troops.txt` field layout; **not an AI source**. | No licence; do not vendor. |

**Rule:** compare definitions, then test in engine. A mirror is never authority over the WSE2 SDK
or the engine's own compiled headers.

---

## 7. Blocked / unverified sources (do not rely on)

| Source | Status |
| --- | --- |
| Nexus Mods live pages (including Mods 2475) | HTTP 403 Cloudflare to automated clients (observed 2026-10-24); verified from Wayback capture instead. |
| Doghotel "Brainy Bots" dedicated-server patch (IndieDB) | HTTP 403 when previously attempted by A; not inspected. Listed only as a known community pointer to check manually. No claims made. |
| Chinese forum thread on battlefield behavior-control research (`bbs.mountblade.com.cn/thread-2111625`) | Seen in search results; not translated/reviewed. Unverified pointer. |
| Original OLL Clan command DB (`mbcommands.ollclan.eu`) | Not relied on; the Modding Wiki archive (W1) is the stable citation. |

---

## 8. Coverage map for C's task-35 questions (sources to read; synthesis is C's)

| Question | Best starting sources | Why |
| --- | --- | --- |
| Hold/fire semantics: `team_give_order`, `team_set_order_position`, `mordr_hold` | W1 (opcodes 1790/1791), D4 (historical command kit), D1/D2 (behavior pitfalls) | Base op definitions + community experience with orders and formation behavior. |
| `agent_set_scripted_destination` pitfalls | W1 (opcode 1730), D1 (charge hesitation), D3 (combat-AI goals), our own T26 evidence | Scripted destinations override combat movement in practice; community reports agree formation behavior can stall charging. |
| How AI picks firearms vs melee / ammo | S1 (`iRangedBumpStun`, `bRainAffectsFirearms`), W1 (`agent_get_ammo` 1727, `agent_set_ammo` 1776), our `ORIGINAL_0.4_BEHAVIOR.md` (original loadouts/ammo absent) | Config/op capabilities + original data constraints; actual engine choice needs D's evidence. |
| Slowing/steering zombies without gear | W1 (`agent_set_speed_limit` 1736, `agent_force_rethink` 1732, `agent_set_division` 1783 / `agent_set_group` 1766), D1/D2 | Ops exist for speed/division; no community source claims a proven "slow zombie" recipe — must be tested. |
| Wave spawning/reinforcement | W4 (faction `_multiplayer_ai` troops), our `ORIGINAL_0.4_BEHAVIOR.md` (wave table + trigger 14/15 staging), D1/D2 (battle-size/reinforcement pitfalls) | Faction/troop mechanism + our original-data table; FormAI constants mention `AI_Max_Reinforcements` but are not native wave logic. |
| Blocking/parry | S1 (`bParry` removed; `bDegradeBrokenShields`; ranged-agent blocking bump), W1 (`agent_set_defend_action` 1746; `server_set_control_block_dir`), our `ORIGINAL_0.4_BEHAVIOR.md` (shield/skill data) | WSE2 changed parry semantics; base op for defend action; original data shows shield/skill prerequisites. |

---

## 9. Credits and reuse rules to preserve

**Community authors named in this pack** (link/credit, do not copy):
Motomataru (Formations AI / battlefield AI / campaign AI compilation); Mirathei (original concept
and code; Battlefield Tactics kit); Caba'drin (order menu interface, slot conversion, weapon swing
strip, division typing); Sphere (modmerger/auto options); Rubik, Idibil, Othr, Dunde, Treebeard,
WindyPlains, HokieBT, Brytenwalda betatesters (credits on Nexus 2475); Swyter, Theoris and Modding
Wiki contributors (operation database); Yoshiboy (client/server events); cdv (agent regeneration
example); stigma, Leifdin, Oliveran, K700 (forum threads); the WSE2 team (Ruslan-700) for the
runtime and SDK docs.

**Rules:**

1. **No code, constants, scripts or assets from this pack are copied** into this repository —
   consistent with our existing policy and with Motomataru's Nexus permissions.
2. Any *semantic* reuse must be independently re-expressed with documented native operations; cite
   the source in comments/docs, not in code import.
3. Do not redistribute WSE2 binaries, the Nexus compilation, TGS files, or wiki dumps.
4. If a future public release ever uses community code (not planned), re-check the exact permission
   text first; several sources above are explicitly restrictive or unlicensed.
5. Keep the original authors' credits in any doc that builds on their work.

---

## 10. Verification log (observed 2026-10-24)

| Check | Method | Result |
| --- | --- | --- |
| Nexus 2475 title/author/date/permissions/credits | Wayback capture 2025-03-10, full text extraction | verified as recorded in §1 |
| FormAI file attribution and tunable constants | raw GitHub files (`formations_presentations.py`, `formAI_constants.py`), 200 OK | verified as recorded in §2 |
| TGS licence scope | raw `license.txt` | modified 2-clause BSD for TGS assets; third-party FormAI rights not granted — link-only |
| Modding Wiki pages W1–W6 | HTTP 200 + page text extraction; main page public-domain statement; repo metadata (pushed 2020-04-26) | verified |
| Opcode table contents | parsed `List_of_operations` rows for named ops | opcodes as in §3; `agent_set_ai`/`agent_set_weapon_mode` absent |
| Forum threads D1–D5 | Wayback captures; titles, thread starters, start dates extracted from page metadata | verified; live pages blocked |
| WSE2 release v1.1.5.4 + SDK files | GitHub API release metadata; raw SDK files HTTP 200 | verified |
| WSE2 addon AI-op overlap | grep of `header_operations_addon.py` | base AI/order ops not redefined there |
| Operation mirrors G1–G3 | GitHub contents API + licence field | files exist; no licence detected |

---

## 11. Limits of this pack (explicit)

- **No engine evidence:** none of these sources proves behavior on **Warband 1.174 + WSE2 1.1.5.4**;
  D's sealed runs remain the only observation channel.
- **Era skew:** sources span 2008–2026; FormAI/Motomataru's compilation targets Warband ~1.153
  (2012); WSE2 changes parry/block and some op semantics.
- **No licence grant** for most code sources; several are explicitly non-redistributable, and
  operation mirrors have no licence at all.
- **Forum reports are not measurements**; they are useful failure-mode checklists, not proof.
- **Link rot/bot walls:** TaleWorlds/Nexus live pages are Cloudflare-blocked; citations include
  Wayback captures but captures can be partial/edited (thread edits, deleted posts).
- **No synthesis here:** C's `reference/WARBAND_AI_MODDING.md` owns the behavior conclusions and
  prototype; this file only certifies sources, credits and reliability.
