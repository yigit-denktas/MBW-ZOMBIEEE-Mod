# Legal rights, credits and redistribution gate (M4 / ZOM-LEGAL-01)

**Status:** evidence dossier for the M4 legal/publication gate. **This is not legal advice**, not a
licence grant and not an acceptance. The gate is **OPEN / NOT ACCEPTED**: `ZOM-LEGAL-01` remains
`required`, `backlog` in the Project Record; required City outcomes stay **0/23**, accepted
milestones **0/5**, `runtime_verified=false`.
**Observed:** 2026-10-24 against `main` `3d6791e`.
**Scope:** what rights exist over the original ZOMBIEEE Beta 0.4 content, our own code and the
third-party pieces we depend on or cite; what may and may not be redistributed; the attribution
that must ship; and the unresolved risks. **No original assets are copied into this document or
the repository; source links only.**

---

## 1. Purpose, mapping and evidence classes

**Milestone M4** ("City-first solo release accepted") requires every gate item, including
**`ZOM-LEGAL-01`** ("Resolve publication rights and attribution") and **`ZOM-REL-01`** (packaging,
which depends on `ZOM-LEGAL-01`). This document is the legal-gate evidence record; it does not
change ledger state and does not accept the leaf.

Evidence classes used:

| Class | Meaning |
| --- | --- |
| **archived-primary** | Wayback capture of the original 2012 TaleWorlds post, read directly |
| **inspected-local** | read-only inspection of the owner's private archive / built module |
| **source-verified** | our own repository code/config/ledger read directly at the pinned revision |
| **owner-attested** | repository owner's statement from the project brief; not independently verifiable by an agent |
| **external-unverified** | a page exists but is bot-blocked or not reviewable as a primary legal source |
| **unknown** | explicitly not established — must not be presented as fact or resolved by assumption |

---

## 2. Rights-holder map (what belongs to whom)

| Layer | Rights holder(s) | Evidence | Status |
| --- | --- | --- | --- |
| ZOMBIEEE Beta 0.4 mod code/design and team-authored assets | **Artizan, Nemerius**, Belendor, BattalGaziTR, Hayalperest, Artintrex (2012 team) | Archived OP (§3.1) | Authors verified; **reuse/redistribution terms unknown** beyond the owner attestation |
| Third-party OSP assets credited in the OP | Shredzor's OSP (Shredzorz), Arch3r's Invasion OSP, Modern Buildings OSP, Thel's OSP, Polished Landscapes, MatBerserker, Highlander, Revan Shan, Specialist, BattleOfValmy, Belendor, Shikimaru, WTF clan | Archived OP credits list (§3.1) | **Per-asset terms unknown**; credit list is not a licence (PROVENANCE §2) |
| Nirecotive base-mod content (module base/readme shipped inside the RAR) | **Nireco** / Nirecotive project | RAR readme `ZOMBIEEE/Readme.txt` (2010-10-16), inspected-local | Separate project; **terms unknown**; not a ZOMBIEEE author |
| Mount & Blade: Warband engine/game data and marks | **TaleWorlds Entertainment** (and licence terms via Steam) | Original module contains Warband copyright strings (`ZOMBIEEE/strings.txt`: "Mount&Blade: Warband Copyright 2008-2010 Taleworlds Entertainment"); [Warband Steam EULA app 48700](https://store.steampowered.com/eula/48700_eula_0) (HTTP 200 observed) | Game files remain under TaleWorlds/Steam terms; **not redistributable by this project** |
| WSE2 runtime (binaries/SDK) | WSE2 authors (Ruslan-700 project) | [WSE2-Releases v1.1.5.4](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4); repo shows **no licence field** | Users obtain WSE2 separately; **do not bundle/redistribute binaries** here |
| Third-party game assets possibly present in the 2012 mod | e.g. Left 4 Dead (Valve/Capcom/Turtle Rock lineage as asserted in-thread), Extra Invasion resource files | Archived thread pages 3–4 (§3.4) | **Unverified allegation/statement**; provenance of shipped 0.4 assets not itemised — **high-risk for any public release** |
| This remaster's own code, tools, tests, docs | Repository owner (project authorship; agents work for owner) | Repo metadata; no `LICENSE`/`NOTICE` file present | **No explicit licence**: default copyright applies; owner must decide terms before inviting reuse |
| Third-party project-tracking toolkit in repo (`.agents/skills/…`, `.project-record/agent-installation.json`) | External "Project Record" suite (v0.4.1, suite digest recorded) | Source-verified: files + installation manifest; **no licence/NOTICE in repo** | Licence unknown → repo-redistribution risk (low-medium, but must be resolved before claiming "repo content is ours") |
| Community references cited in docs (Modding Wiki, forum threads, GitHub mirrors) | Respective authors (Swyter/Theoris, forum posters, repo owners) | `reference/WARBAND_AI_COMMUNITY_SOURCES.md` (task-36) | We **cite**, do not copy code/assets; wiki archive is stated public domain; forum text/other repos are not licensed to us |

**Conclusion:** there is **no single rights holder** and no blanket licence. Any public *playable*
release requires at least the original team's and OSP authors' permissions, plus compliance with
TaleWorlds/Steam terms, and resolution of the third-party-asset allegation.

---

## 3. Permission and credit evidence

### 3.1 Verified original team and credits (archived-primary)

Wayback capture **2023-10-08 20:25:35 UTC** of the original OP (post `/post-5251005`):
<https://web.archive.org/web/20231008202535/https://forums.taleworlds.com/index.php?threads/wb-zombieee-invasion-we-need-your-advice.219327/>

- Thread: *"[WB] ZOMBIEEE (Invasion) We Need Your Advice"*, TaleWorlds thread **219327**, started
  **2012-03-03** by **Nemerius**. OP: *"Artizan and I have decided to start a multiplayer, invasion
  like Zombie survival mod … then decided to work on it a little bit more and **release it for the
  community**."*
- **Team (OP wording):** Artizan — Scripter, 3D modeller; **Nemeruis** (= **Nemerius**) — Scripter,
  3D modeller, textures, 2D art, Sounds, Musics, Map editor; Belendor — Scripter; BattalGaziTR —
  Rigs, animations; Hayalperest — Scene prob 3D modeller; Artintrex — Research.
- **Credits (OP wording, a thank-you list, not a licence):** Shredzor's OSP, Arch3r's invasion OSP,
  Modern buildings OSP, Thel's OSP, Polished Landscapes, MatBerserker, Highlander, Revan Shan,
  Specialist, BattleOfValmy, Belendor, Shikimaru, and WTF clan.
- **Release:** OP links "PATCH 0.4" (MediaFire) and announces "New PATCH 0.5 Not yet released";
  the thread was later marked paused (strikethrough) and revived in 2013. Full detail and naming
  cautions: `docs/PROVENANCE.md` §2.

### 3.2 Owner attestation (the current permission basis)

The repository owner **personally knew the original team** and **attests that the original
TaleWorlds page explicitly allowed anyone to take and play the mod**. On that basis the project
treats the **private, local preservation build** as authorized (owner builds from their own archive
for private play; the repository hosts only the remaster's own tooling, tests and docs).

**Limits (must not be over-read):**

- It is **owner-attested**, not a re-checkable archived quotation (the exact sentence was not found
  in the 2021/2023 captures; live forum is Cloudflare-blocked).
- It evidences **permission to download/play**, not a general licence to **modify, republish,
  sublicense or commercially exploit** the original work.
- It does **not** cover third-party OSP assets, Nirecotive, TaleWorlds/Warband data, WSE2 binaries,
  or any third-party game assets.

### 3.3 What the archives do **not** show

- No explicit "you may reuse / redistribute / modify" licence statement in the archived pages.
- No OSP licence texts in the archive or thread; credits only.
- No original Python module-system source in the RAR (last thread page ends with an unanswered
  request for the module source, page 23 `#449`).
- No ModDB/IndieDB/Internet-Archive page or independent GitHub mirror of Beta 0.4 (searches
  negative; see `docs/PROVENANCE.md` §3.5).

### 3.4 Third-party asset-origin risk evidence (2012 thread pages 3–4)

These are **community statements/allegations from the original thread**, not legal findings. They
are reproduced briefly because they directly affect publication risk; the full posts remain at the
cited captures (link-only).

- Page 3 capture <https://web.archive.org/web/20231008232004/https://forums.taleworlds.com/index.php?threads/wb-zombieee-invasion-we-need-your-advice.219327/page-3>
  - `#51` Specialist asks: *"Did you use some Left 4 Dead models? Because they sure look like it…"*
  - `#52` Nemerius replies: *"I downloaded the models from a site called freemodels, i dont know
    where they are taken from"*.
  - `#58` Specialist: *"Other than the ripped models, this mod is amazing."*
  - `#59` Artizan: *"We will not be removing any 'ripped' models, if you are not satisfied, you can
    report us to Capcom or Turtle Rock Studios."*
- Page 4 capture <https://web.archive.org/web/20231009184154/https://forums.taleworlds.com/index.php?threads/wb-zombieee-invasion-we-need-your-advice.219327/page-4>
  - `#61` BattleOfValmy: *"Using another game's models without permission gets you perma-banned on
    this forum, though."*
  - `#67` **Artizan (mod author)** states the UZI came from `thefree3dmodels.com` and *"we got the
    zombie model from Extra Invasion resource files. we couldn't contact the author of the mod…"*.
  - `#68` Specialist quotes a model description: *"SMG UZI - weapon from game Left 4 Dead, with
    texture."*
- The OP to-do list (same page-1 capture) also lists *"Spitter from L4D2 will be brought into mod"* —
  a stated **plan**, not proof it shipped in Beta 0.4.

**Meaning for us:** the 2012 authors acknowledged importing models of uncertain origin, and at least
one community member identified them as from another game. Whether **Beta 0.4 as shipped** contains
those specific assets is **not itemised**. Any public release derived from the RAR therefore carries
a **high-severity, currently unresolved** third-party-IP risk. The private/local build does not
redistribute them; the repository does not contain them.

### 3.5 Runtime / tooling dependencies

- **Warband**: proprietary; the original module is compiled Warband data (contains Warband
  copyright strings). We do not redistribute game files; users must own Warband 1.174.
- **WSE2 1.1.5.4**: third-party runtime; its release repo shows **no licence field**. Users install
  it separately; we do not bundle it. (WSE2 SDK docs are cited, not vendored.)
- **Project Record toolkit** (`.agents/skills`, `.project-record/agent-installation.json`): installed
  third-party tracking skills; **no licence/NOTICE file** in the repo. Redistribution status
  unknown; low product risk but must be resolved before claiming the public repo is fully owned by
  this project.
- **`overlay/lua/msfiles/header_operations.py`**: our file states constants were *"independently
  transcribed from Warband header_operations"*, with a source reference to
  `Veehats/WarbandCoop/blob/main/header_operations.py` — a repo with **no detected licence**
  (`reference/WARBAND_AI_COMMUNITY_SOURCES.md` G1). Independent transcription mitigates, but the
  provenance claim needs review before a public relicensing of our code.

---

## 4. Redistribution matrix

| Item | Current location | In public repo? | Redistribution status | Basis / action |
| --- | --- | --- | --- | --- |
| This repo's own tooling, launcher/installer, tests, telemetry docs | repository | **Yes** | **Can be published only by/with the owner's rights** | No `LICENSE` yet; owner must choose terms. Third-party toolkit files need licence resolution |
| Documentation with short attributed quotations / links | repository | **Yes** | Generally published by owner; keep quotes short/attributed | Wayback links preserved; do not paste full posts |
| Original `ZOMBIEEEBeta04.rar` | owner's private disk | **No** | **Cannot redistribute** | No rights recorded; owner attestation covers private play only |
| Extracted `ZOMBIEEE/` module (incl. OSP/third-party assets) | private/local | **No** | **Cannot redistribute** | Original team + OSP + unknown third-party IP |
| Built `Modules/ZOMBIEEE_Remaster` | owner's game install | **No** | **Cannot redistribute** | Derivative of original assets + Warband data |
| Modified compiled files (mission/scenes/variables/troops/items) produced by build | build output | **No** | **Cannot be published as a package** without permissions | Derivative works of original/Warband data |
| `overlay/lua/main.lua`, `overlay/lua/msfiles/ID_troops.py` | repository | **Yes** | Our code; `ID_troops` is a derived factual label aid | Review derived-data wording; keep as observation aid |
| `overlay/lua/msfiles/header_operations.py` | repository | **Yes** | Our transcription with cited unlicensed reference | Document independent-transcription provenance; review before relicensing |
| Third-party OSP assets (models/textures/sounds/scenes) | inside original RAR | **No** | **Cannot redistribute** | Per-asset licences unknown |
| Nirecotive base content/readme | inside original RAR | **No** | **Cannot redistribute** | Nireco/terms unknown |
| Warband game files / engine | owner's install | **No** | **Cannot redistribute** | TaleWorlds/Steam terms |
| WSE2 binaries/SDK binaries | owner's install; upstream releases | **No** | **Cannot redistribute here** | Third-party runtime; no repo licence observed |
| Session evidence bundles, logs, screenshots, HMAC keys | local `evidence/` / `local/` (gitignored) | **No** | **Must never be published** | May contain paths/account/session data; privacy review required |
| Serial keys / personal paths | never stored | **No** | **Prohibited** | `.gitignore` + policy |
| `.agents/skills/**`, `.project-record/**` | repository | **Yes** | Third-party toolkit, licence unknown | Identify toolkit licence/NOTICE or remove before public-repo relicensing |
| Community code/assets referenced in research docs | not in repo (links only) | **No** | Not redistributed | Cite/link only; see `reference/WARBAND_AI_COMMUNITY_SOURCES.md` |

**Repository scan evidence (source-verified):** `git ls-tree -r origin/main` contains **no**
`.rar/.zip/.7z/.exe/.dll/.brf/.dds/.scn/.wav/.ogg/.mp3/.bmp/.tga/.jpg/.png` files; `.gitignore`
blocks archives, game executables, `Modules/`, `local/`, `evidence/`. This supports "no game assets
or binaries are bundled today" — it does **not** establish rights to publish the derived build.

---

## 5. Publication models (analysis only — owner decision)

| Model | What ships | Rights needed | Current feasibility | Gate effect |
| --- | --- | --- | --- | --- |
| **A. Private/local only (current)** | nothing beyond the public repo | owner attestation for private use | **Current state**; playable locally by owner | Legal gate can stay open; no public release |
| **B. Public repo as-is (code/docs/tests)** | our repo content only | owner's own licence for own code; third-party toolkit/transcription review; quotation hygiene | **Possible now, with fixes**: add `LICENSE`/`NOTICE`, resolve toolkit licence, keep no assets | Does **not** satisfy `ZOM-REL-01` (no playable package) |
| **C. Public patch-only installer** (user supplies bought Warband + own RAR; tool patches locally) | our installer + patches/modified compiled files generated locally | Original team + OSP permissions; comply with TaleWorlds terms; third-party asset exclusions | **Not cleared** | Would need explicit permissions; "patch" still derivative |
| **D. Clean-room asset-free release** (our code/tools only; user supplies game + original archive; no original/derived assets in package) | tools/docs/launcher + user-side build | Owner licence for own code; avoid shipping derived compiled data | **Most plausible public model**, but current build output is not clean-room | Legal gate could pass with review; still not a packaged playable release |
| **E. Full bundled playable release** (RAR/assets/build included) | everything | All of the above + third-party IP clearance | **Blocked** | Cannot pass `ZOM-LEGAL-01` today |

No model should be announced publicly until the owner has chosen one and, for any public package,
qualified advice has reviewed it (see §9; not legal advice).

---

## 6. Required attribution and minimum notices

If/when any public artifact ships, it must carry at least:

1. **Original team:** Artizan; Nemerius (OP spelling "Nemeruis"); Belendor; BattalGaziTR;
   Hayalperest; Artintrex — with roles as quoted in `docs/PROVENANCE.md`.
2. **OSP/community credits (OP):** Shredzor's OSP, Arch3r's Invasion OSP, Modern Buildings OSP,
   Thel's OSP, Polished Landscapes, MatBerserker, Highlander, Revan Shan, Specialist, BattleOfValmy,
   Belendor, Shikimaru, WTF clan.
3. **Base-mod note:** the 2012 module contains the **Nirecotive** readme ("This is Nirecotive mod.
   Made by Nireco"); credit the Nirecotive project if its base content is used. Do **not** describe
   Nireco as a ZOMBIEEE author.
4. **Warband notice:** *Mount & Blade: Warband* © 2008–2010 TaleWorlds Entertainment; users must own
   the game and observe its licence. This project is **not affiliated with or endorsed by**
   TaleWorlds.
5. **WSE2 notice:** WSE2 by the Ruslan-700 project; users obtain it separately; no endorsement.
6. **This project:** remaster tooling/docs by the repository owner (licence to be chosen).
7. **Community sources:** credit the Modding Wiki (Swyter/Theoris/contributors), forum authors and
   repositories cited in `reference/WARBAND_AI_COMMUNITY_SOURCES.md`; link-only reuse.
8. **No-endorsement / unofficial statement** and the fact that **no original assets are
   distributed** in the repo/public artifact.

Suggested notice block (plain text, to be included in a future `NOTICE`/README/release notes/installer
About screen):

```text
ZOMBIEEE (Invasion) Beta 0.4 — original team: Artizan, Nemerius, Belendor, BattalGaziTR,
Hayalperest, Artintrex. OSP/community credits: Shredzor's OSP, Arch3r's Invasion OSP,
Modern Buildings OSP, Thel's OSP, Polished Landscapes, MatBerserker, Highlander,
Revan Shan, Specialist, BattleOfValmy, Belendor, Shikimaru, WTF clan. Built on the
Nirecotive base by Nireco (see the original readme). Mount & Blade: Warband © 2008-2010
TaleWorlds Entertainment. WSE2 by the Ruslan-700 project. This is an unofficial,
non-commercial preservation/remaster project, not affiliated with or endorsed by the
original ZOMBIEEE team, TaleWorlds or the WSE2 authors. No original game or mod assets
are distributed; users must own Warband and their own copy of the original mod.
```

Attribution accuracy rules: keep **Nemerius** as the lead name (preserve "Nemeruis" only as a quoted
OP variant); Belendor appears in both team and OSP credits — keep both; do **not** add "among
others" or unverified names (the OP did not say it); never imply endorsement; do not call the
project "official".

---

## 7. Open risk register

| ID | Risk | Severity | Likelihood | Evidence | Mitigation / status |
| --- | --- | --- | --- | --- | --- |
| **R-01** | Permission basis is owner-attested, not a re-checkable licence sentence; scope (play vs derivative/redistribution) unknown | High (public release) | Certain (it is the current state) | `docs/PROVENANCE.md` §3.1–3.3; live forum blocked | Human-verify/capture the sentence; obtain written confirmation from team; keep private until then — **open** |
| **R-02** | OSP/third-party asset licences not identified; credit list ≠ licence | High | Likely | OP credits; no licence texts found | Per-asset inventory + contact OSP authors; exclude unresolved assets — **open** |
| **R-03** | Original 0.4 may contain models of other-game origin (L4D/Extra Invasion per 2012 thread statements) | **High** | Unknown but plausible (authors' own statements) | §3.4 Wayback pages 3–4, posts #51/#52/#58/#59/#61/#67/#68; OP "Spitter from L4D2" to-do | Do not publicly redistribute assets; itemise/replace/exclude; qualified review — **open, potentially blocking** |
| **R-04** | Nirecotive base-mod terms unknown | Medium | Likely | RAR `Readme.txt`; PROVENANCE §5 | Review Nirecotive terms/credit — **open** |
| **R-05** | Warband/Steam EULA restricts redistribution of game data; built module is derivative | High (for bundled release) | Likely | Original module copyright strings; Warband Steam EULA link | Never redistribute game files; distribution model must avoid bundling — **open** |
| **R-06** | WSE2 runtime has no observed licence grant in its release repo | Medium | Possible | Task-36 §5; repo licence field null | Do not bundle WSE2 binaries; users install separately — **mitigated by policy**, not resolved |
| **R-07** | Public repo has **no LICENSE**; default copyright means no reuse grant for our own code | Medium (public repo) | Certain | `gh api repos/... license` → null; no LICENSE/NOTICE in tree | Owner chooses licence (code/doc split) + NOTICE; legal review — **open** |
| **R-08** | Third-party Project Record toolkit in repo (`.agents`, `.project-record`) has unknown licence | Low–Medium | Certain it is present | `.project-record/agent-installation.json` (suite v0.4.1/digest); no licence file | Identify toolkit licence or remove/repin before relicensing repo — **open** |
| **R-09** | `overlay/lua/msfiles/header_operations.py` cites an unlicensed source repo for transcription | Low–Medium | Possible | File header + task-36 G1 (no licence detected) | Document independent transcription; review/clean before public relicensing — **open** |
| **R-10** | Quotes/links from forums/wiki in our docs could exceed acceptable quotation if expanded | Low | Low | Short attributed quotes + Wayback links currently | Keep excerpts short, attributed; link rather than paste — **controlled** |
| **R-11** | Trademark/name use ("Mount & Blade", "Warband", "WSE2", "ZOMBIEEE") could imply endorsement | Medium | Medium if marketed ambiguously | Project naming/README | Keep nominative/descriptive use + explicit no-endorsement notice — **controlled by notice** |
| **R-12** | Session evidence/privacy: bundles may contain paths/account/session data | High if published | Certain if published | `.gitignore`; diagnostics policy | Never publish; redaction review before any share — **controlled by policy** |
| **R-13** | Ledger note contains a name typo (`Nendorius/Nemerius`) | Low (credits accuracy) | Certain | `progress/ledger.json` note for ZOM-LEGAL-01 | A to correct in `progress/**`; do not propagate typo — **open (A)** |
| **R-14** | No qualified legal review performed; jurisdiction/contract unknown | High for public release | Certain | This document | Obtain review before public package — **open** |
| **R-15** | Downstream forks/mirrors may redistribute assets despite policy | Medium | Unknown | Public repo | Add licence/NOTICE + clear redistribution warning; cannot fully control — **residual** |

---

## 8. Mapping to ZOM-LEGAL-01 and M4

**Ledger leaf (source-verified from `progress/ledger.json` at `main` `3d6791e`):**

| Field | Value |
| --- | --- |
| ID / title | `ZOM-LEGAL-01` — Resolve publication rights and attribution |
| Milestone | **M4** (City-first solo release accepted) |
| Required | **true** |
| State | **backlog** (not accepted) |
| Owner | "Agent B — implementation; user retains release acceptance" |
| Criterion | *"Original and OSP contributors credited; installer asset distribution reviewed; unlicensed material never bundled"* |
| Evidence already attached | issue #5, PR #18, issue #5 comment `6378327556` |
| Completion basis | "No final criterion acceptance; prototype implementation must not count as Done" |

**Criterion assessment (this document's contribution):**

| Criterion component | Assessment | Evidence | Remaining |
| --- | --- | --- | --- |
| Original + OSP contributors credited | **VERIFIED** for names/roles/credit list | archived OP (§3.1), `docs/PROVENANCE.md` §2, README attribution | OSP individual authors/terms still unknown; ledger typo (R-13) |
| Installer asset distribution reviewed | **REVIEWED (bounded)** — current model never bundles assets: installer is a dry-run planner; build uses a user-supplied RAR and local extraction; repo scan shows no assets | `installer/manifest.py` (dry-run, consent-required), `tools/build.py`, `.gitignore`, git tree scan; §4 | No public installer/package exists; derivative-patch permissions unresolved (R-01/R-02/R-03) |
| Unlicensed material never bundled | **CONDITIONAL** — no game/mod assets or binaries in repo today; but third-party toolkit and one transcription-provenance file need resolution | §4 repo scan; R-07/R-08/R-09 | Resolve toolkit/transcription provenance; keep policy enforced |

**M4 dependency context:** `ZOM-REL-01` ("Package City-first accessible solo v1.0 candidate") is
`blocked: true` and depends on `ZOM-LEGAL-01`; M4 acceptance rule is **all-gate-items**
(`ZOM-QA-01`, `ZOM-QA-02`, `ZOM-ADMIN-01`, `ZOM-LEGAL-01`, `ZOM-REL-01`). Because `ZOM-LEGAL-01` is
open, M4 cannot be accepted; accepted milestones remain **0/5**.

**What would change the leaf state (owner/authority decision, not ours):** owner sign-off on a
chosen distribution model; per-asset inventory with exclusions; documented permissions (or a
clean-room/asset-free design); a licence decision for our own code; qualified review. Until then,
`ZOM-LEGAL-01` stays `backlog`/required and no public release may be claimed.

---

## 9. Recommended next actions (engineering/provenance, not legal advice)

1. **Human-verify the permission record:** open the archived thread in a browser, capture the exact
   sentence/date/post-id, or obtain fresh written approval from the surviving team members.
2. **Per-asset inventory** of the owner's RAR (hashes + origin guesses), separating: team-authored,
   OSP-credited, Nirecotive/engine-derived, and unknown/third-party-game-origin. Exclude or replace
   unresolved items from any public artifact.
3. **Contact OSP authors** for the credited packs; record grant/denial/unknown per asset.
4. **Choose a publication model** (§5) explicitly; prefer asset-free/clean-room for anything public.
5. **Add `LICENSE` + `NOTICE`** to this repository (owner decision): separate code/doc terms if
   desired, keep attribution block §6, and state that no game/mod assets are distributed.
6. **Resolve third-party inclusions** in the public repo (Project Record toolkit licence; header
   transcription provenance).
7. **Correct the ledger note typo** (Nemerius) via Agent A in `progress/**`; keep `ZOM-LEGAL-01`
   state unchanged until owner acceptance.
8. **Post this dossier on issue #5** and keep Wayback/links archived; do not paste long forum text.
9. **Before any public package**, obtain qualified legal review of the chosen model and terms.

---

## 10. Verification log / sources

| Check | Method | Result |
| --- | --- | --- |
| Original team/credits/release | Wayback capture 2023-10-08 of OP, text extraction | verified (§3.1) |
| Forum third-party asset statements | Wayback page-3 capture 2023-10-08, page-4 capture 2023-10-09 | verified as statements (§3.4) |
| Repo licence | GitHub API `license` field; tree grep for LICENSE/NOTICE | **null / absent** (R-07) |
| Repo asset/binary scan | `git ls-tree -r origin/main` filter for game/archive/binary extensions | **none present** (§4) |
| Installer distribution model | `installer/manifest.py` flags `dry_run: true`, `execution_enabled: false`, `consent_required: true`; build via user-supplied archive | reviewed (§4, §8) |
| Third-party toolkit | `.project-record/agent-installation.json` (suite v0.4.1, digest) | present, licence unknown (R-08) |
| Overlay transcription provenance | `overlay/lua/msfiles/header_operations.py` header + task-36 G1 | open review (R-09) |
| Warband terms | [Steam EULA app 48700](https://store.steampowered.com/eula/48700_eula_0) (HTTP 200) | external terms; not interpreted here |
| WSE2 licence | release repo metadata; task-36 §5 | no licence field observed (R-06) |
| Ledger state | `progress/ledger.json` at `main` `3d6791e` | `ZOM-LEGAL-01` backlog/required; M4 all-gate-items; 0/23, 0/5 |
| Live TaleWorlds/Nexus pages | HTTP fetch | Cloudflare-blocked (403); Wayback used |

**Explicit limits:** this file records evidence and engineering judgement; it is **not legal
advice**, does not determine fair use or licence validity, and does not resolve jurisdiction. All
unresolved items are marked **open/unknown**. Original assets were not copied; only short,
attributed quotations and links are used.
