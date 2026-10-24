# Original authorship, permission and archive provenance

**Status:** working provenance record, updated 2026-10-24 by Agent E.
**Evidence classes used here:** *archived-primary* (a Wayback Machine capture of the original
TaleWorlds post), *inspected-local* (read-only inspection of the owner's private archive),
*owner-attested* (the repository owner's personal knowledge; not independently re-verified),
*unknown* (explicitly not established). Nothing in this file is a legal opinion or a licence grant.

**What this record does and does not establish**

- **Establishes:** who the original 2012 ZOMBIEEE team were and what they were credited for;
  that Beta 0.4 was publicly released by them for the community; the identity of the historical
  archive this project builds from; and that the owner attests the original page allowed anyone to
  take and play the mod.
- **Does not establish:** a general redistribution licence for the original mod or its assets,
  per-asset OSP permissions, or permission to publish a packaged build. The public repository
  contains **only** this project's own code, tests and documentation.

---

## 1. Identity of the original work

- **Name:** *ZOMBIEEE (Invasion)*, a multiplayer invasion/survival mod for *Mount & Blade: Warband*.
- **Historical version:** **Beta 0.4** (2012). In 2012 the thread listed "PATCH 0.4" with a MediaFire
  download and announced "New PATCH 0.5 Not yet released"; 0.5 was never released in this archive.
- **Original community thread:** *"[WB] ZOMBIEEE (Invasion) We Need Your Advice"*, TaleWorlds forums
  thread **219327**, prefix **MP — Apocalypse**, posted in *The Pioneer's Guild — Mods Under
  Construction*. Started **2012-03-03** by **Nemerius**.
  Live URL: <https://forums.taleworlds.com/index.php?threads/wb-zombieee-invasion-we-need-your-advice.219327/>
- **Private source archive:** `ZOMBIEEEBeta04.rar` (owner-supplied; **not committed**), RAR4,
  `167,493,071` bytes, SHA-256
  `9be100ff41ce6f8ebadd4aa27377f70f402883fab271999a8cab8cc1da001d1e`, 1,068 files / 18 folders in a
  single top-level `ZOMBIEEE/` directory. The RAR carries no ZOMBIEEE-specific readme or credits file
  (see §5). Identity is pinned in [`reference/ARCHIVE.txt`](../reference/ARCHIVE.txt) and enforced by
  `tools/archive_audit.py` / `tools/build.py`.

## 2. Verified original team and credits (archived-primary)

Source: Wayback Machine capture **2023-10-08 20:25:35 UTC** of the thread's first page, which includes
the original post (post id `/post-5251005`):
<https://web.archive.org/web/20231008202535/https://forums.taleworlds.com/index.php?threads/wb-zombieee-invasion-we-need-your-advice.219327/>

The original post opens: *"Hello there, Artizan and I have decided to start a multiplayer, invasion
like Zombie survival mod for ourselves, then decided to work on it a little bit more and release it
for the community."* — i.e. **Artizan and Nemerius are the two founders**, and the project was
released publicly to the community.

**Mod team as written in the OP** (reproduced exactly, roles verbatim; the OP spells the second name
"Nemeruis", while the account and thread starter are "Nemerius"):

| Name (OP spelling) | Role (OP wording) |
| --- | --- |
| **Artizan** | Scripter, 3D modeller |
| **Nemeruis** (= **Nemerius**, thread starter) | Scripter, 3D modeller, textures, 2D art, Sounds, Musics, Map editor |
| **Belendor** | Scripter |
| **BattalGaziTR** | Rigs, animations |
| **Hayalperest** | Scene prob 3D modeller |
| **Artintrex** | Research |

**Credits listed in the OP** (verbatim; this is a thank-you list, **not** a licence statement):

> Shredzor's OSP, Arch3r's invasion OSP, Modern buildings OSP, Thel's OSP, Polished Landscapes,
> MatBerserker, Highlander, Revan Shan, Specialist, BattleOfValmy, Belendor, Shikimaru,
> and WTF clan!

Notes for future editors:

- Spell the lead **Nemerius** (account/thread starter); the team list's "Nemeruis" is an OP typo and
  should be preserved only as a quoted variant.
- "Shredzor's OSP" refers to the OSP of forum member **Shredzorz**, who replied in the thread
  ("Always nice to see my OSP assets in good hands.").
- **Belendor** appears both in the mod team (scripter) and in the credits list; keep both.
- "among others" in older drafts was **not** in the OP — do not add names that cannot be sourced.
- No other person is named as an owner/author here. If a name cannot be verified from a primary
  source, describe it as "original ZOMBIEEE team (archived credits)" and record it as unknown rather
  than guessing.

## 3. Permission and reuse record

### 3.1 Permission basis — owner attestation

The repository owner **personally knew the original ZOMBIEEE team** and **attests that the original
TaleWorlds page explicitly allowed anyone to take and play the mod**. On that basis this project
treats a **private, local preservation/remaster build** as authorized: the owner builds the module
locally from their own archive for private play, and this repository hosts only the remaster's own
tooling, tests and documentation.

- **Evidence class:** *owner-attested*. It is recorded here at the owner's direction and is the
  permission basis for the private build.
- **Limit:** this attestation is **not** a quotation from a re-checkable archived page, and it does
  **not** by itself authorize redistribution of original assets (see §3.4).

### 3.2 What the archived thread confirms

All 23 thread pages were retrieved from Wayback captures dated 2023-10-08 … 2023-10-19 and searched
(read-only, local copies):

- The OP publicly released **Patch 0.4** with a download link and described the project as released
  *"for the community"*. That supports **free public download/play** of the original mod.
- The thread was later marked paused (strikethrough: *"We are not working on this mod at the
  moment…"*) and was revived by the team in 2013; Nemerius posted in 2013 that a 0.5 was planned.
- **No explicit "you may reuse/redistribute/modify" sentence was found** in those captures. The last
  page ends with an unanswered request for the module-system source (page 23, `#449`).
- **Evidence class:** *archived-primary* for the release, credits and revival; *unknown* for an
  explicit reuse grant.

### 3.3 Live source is bot-blocked

The live TaleWorlds forum now serves a Cloudflare challenge to automated clients, so the original
wording cannot be re-fetched and re-verified by an agent. Any future editor must **not** present a
paraphrase as a quotation. If a human browses the thread, capture the exact sentence, date and post
id and add it below as *archived-primary* or *owner-attested-with-link*.

- **Known limitation:** the archived captures are 2021/2023 snapshots of a 2012–2013 thread; an
  OP edit or deleted post containing the permission sentence may simply not be in the captures.

### 3.4 What this record authorizes — and what it does not

**Authorized (per owner attestation):**

- private, local building and play of the preserved/remastered mod by the owner;
- publishing **this repository's own** code, tests and documentation.

**Not authorized by this record:**

- redistributing the original RAR, extracted module, built `Modules/` output, textures, models,
  sounds, scenes, compiled mission data, or Warband/WSE2 binaries;
- bundling or re-licensing third-party OSP content (each remains under its own author's terms);
- claiming a blanket licence over the historical mod or implying the original team endorse this
  project;
- any public packaged release before issue
  [#5](https://github.com/yigit-denktas/MBW-ZOMBIEEE-Mod/issues/5) records a per-asset
  provenance/permission matrix with unresolved assets excluded.

The independent **ZOMBIEEE2** continuation is out of scope and is not used.

### 3.5 Explicit unknowns (do not silently resolve these)

1. The **exact wording and date** of the original "anyone may take/play" statement; it is currently
   owner-attested, not archive-verified.
2. Whether any such permission was intended to cover **derivative remasters** or redistribution, in
   addition to downloading/playing/hosting.
3. **Per-asset OSP terms**: the OP credits OSP packs and individuals, but no OSP licence texts were
   found in the archive or the thread.
4. Authorship of specific textures/models/scenes; the OP gives team-level and OSP-level credit only.
5. Any **Nirecotive** base-mod terms (see §5) — a separate 2010 mod by "Nireco" whose readme ships
   inside this RAR.
6. Whether a ModDB/IndieDB page ever existed: searches found **no** ModDB or IndieDB page, **no**
   Wayback capture of one, **no** Internet Archive item, and **no** independent GitHub mirror of
   Beta 0.4. The only indexed code references to `ZOMBIEEEBeta04` are in this repository itself.

## 4. Asset and evidence boundary (what stays local)

| Item | Where it lives | In Git? | Why |
| --- | --- | --- | --- |
| `ZOMBIEEEBeta04.rar` (original archive) | owner's private disk | **No** | third-party historical assets; no redistribution right recorded |
| Extracted `ZOMBIEEE/` module | owner's private disk | **No** | same |
| Built `Modules/ZOMBIEEE_Remaster` | owner's game install | **No** | derived from original assets |
| Warband and WSE2 binaries | owner's game install | **No** | licensed game/third-party runtime |
| Sealed flight-recorder bundles, logs, screenshots | local `local/` / `evidence/` | **No** | may contain paths, account data, session data |
| Recorder HMAC keys / control files | local session dirs | **No** | secrets |
| This project's tooling, tests, docs, overlays | repository | **Yes** | original work of this project, no game assets |

`.gitignore` enforces the `local/` and `evidence/` boundaries; the repository's policy is that no
serial keys, personal paths, logs or original assets are committed.

## 5. Archive inspection and the Nirecotive base-mod note

Read-only inspection of the extracted original archive (`7z l` listing, then reading text files):

- The archive contains exactly one top-level folder, `ZOMBIEEE/`, with **1,068 files in 18 folders**.
- Its only top-level readme, `ZOMBIEEE/Readme.txt` (**495 bytes**), is dated **2010-10-16** — more
  than a year before the 2012 ZOMBIEEE release — and reads:

  > "This is Nirecotive mod. Made by Nireco
  >
  > Provided version is client/demo version of the mod. You can do everything you could with full
  > version on any full version server, but you can only host with limited set of features."

  It then lists Nirecotive server features (CTF spawn fix, day time, show pollers). The remaining
  `Readme.txt` files in `Data/`, `Textures/`, `Resource/`, `Music/` and `languages/` are the stock
  Warband placeholder texts.
- **Conclusion (labelled as inference):** the ZOMBIEEE module was built on the **Nirecotive**
  multiplayer module base and the base mod's readme was left in place. This file is **not** a
  ZOMBIEEE credits file, and it does not claim that Nireco authored ZOMBIEEE.
- Nirecotive is a separate, publicly documented Warband multiplayer mod by *Nireco* (for example its
  own TaleWorlds thread and Nexus Mods listing). Its terms are separate and **not** reviewed here;
  until they are, the Nirecotive readme/base content stays local with the rest of the original
  assets. Do not describe Nireco as a ZOMBIEEE author.
- **Evidence class:** *inspected-local* for the file dates/contents; *unknown* for Nirecotive's
  licence terms.

## 6. How this record was verified (reproducible, read-only)

1. Enumerated Wayback captures for the thread via the CDX API, then fetched all 23 page captures into
   a temporary local folder and searched them for credits and reuse language.
2. Fetched the 2021 and 2023 first-page captures to compare the OP before/after edits.
3. Listed the owner's archive with `7z l` (no extraction of tracked files, no modification) and read
   the module's text readmes.
4. Searched GitHub (repository + code search), ModDB, IndieDB and the Internet Archive for mirrors or
   pages; none were found for Beta 0.4.
5. Cross-checked archive identity against `reference/ARCHIVE.txt`.

No game was launched. No original asset was copied into the repository.

## 7. Remaining work to close issue #5

- [ ] Per-asset provenance matrix: authored assets vs OSP contributions vs engine/Warband data.
- [ ] Locate individual OSP licences or direct approvals (where they still exist).
- [ ] Capture the exact "take/play" permission sentence (human-verified, linked) or obtain fresh
      written approval from the surviving team members.
- [ ] Review Nirecotive base-mod terms separately.
- [ ] Decide the distribution model for any future packaged release (patch-only from a locally
      supplied original archive remains the working assumption) and exclude unresolved assets.

## 8. Sources

| Source | What it establishes | Class |
| --- | --- | --- |
| [Wayback capture 2023-10-08 of thread page 1](https://web.archive.org/web/20231008202535/https://forums.taleworlds.com/index.php?threads/wb-zombieee-invasion-we-need-your-advice.219327/) (post `/post-5251005`) | Original team, roles, OSP credits, public Beta 0.4 release | archived-primary |
| [Wayback capture 2021-06-21 of thread page 1](https://web.archive.org/web/20210621213902/https://forums.taleworlds.com/index.php?threads/wb-zombieee-invasion-we-need-your-advice.219327/) | OP text is stable across captures | archived-primary |
| Wayback pages 2–23 of the same thread (captures 2023-10-08 … 2023-10-19) | Pause/revival history; **no explicit reuse grant found**; final request for module source unanswered | archived-primary / shows *unknown* for reuse grant |
| [Live TaleWorlds thread](https://forums.taleworlds.com/index.php?threads/wb-zombieee-invasion-we-need-your-advice.219327/) | Canonical URL; currently bot-blocked (Cloudflare) | blocked |
| Owner-supplied `ZOMBIEEEBeta04.rar` + extracted module | Archive identity, 1,068 files, Nirecotive readme | inspected-local |
| [`reference/ARCHIVE.txt`](../reference/ARCHIVE.txt) | Pinned size/SHA-256 used by the builder | inspected-local |
| Owner attestation (this project brief, 2026-10-24) | Permission basis for the private build | owner-attested |
| GitHub / ModDB / IndieDB / Internet Archive searches | No independent mirror, page or item for Beta 0.4 | negative result |

---

*Ownership wording is reviewed with the repository's integration lead (Agent A) because the
Project Record leaf `ZOM-LEGAL-01` and the public tracker are maintained there. This document does
not change ledger status: required City outcomes remain 0/23 and no legal gate is "accepted".*
