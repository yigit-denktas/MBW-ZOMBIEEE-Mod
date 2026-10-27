---
name: engine-source-citation
description: Use when citing engine behavior, opcode semantics, order/group arguments, or community sources in Warband/WSE2/Bannerlord research, especially when a header comment, opcode name, remembered API, or second-hand citation is the only support
---

# Engine source citation

## Baseline failure (RED)

On 2026-10-24 a City builder used the `add_visitors_to_current_scene` header comment `<team_no>,<group_no>` as proof that the 5th argument is a formation slot, and passed `GROUPS=(5,6,7)`. The Native multiplayer call site passes the **leader/owner player id** there, so the build encoded a false invariant; review-b2 found the defect live in `agent/a-nextplay`. A related failure: `agent_get_group` was read as a division value, but the getter had returned its own agent id (`id=26|group=26`); later aggregates (8..15) were the same echo, and the latest seal returned `-1`. Earlier research docs had to correct both claims.

Rationalizations used: "the header is official API", "the name says `group_no`", "other mods pass formation groups", "0 obviously means no leader", "I remember how this op works".

## Rule

**Cite at the level you verified. A declaration proves a signature, not semantics.**

- Signature → public header + repo + commit.
- Semantics/behavior → call site or implementation + game/header version.
- Everything else → mark `[unverified]`, including sentinels (`-1`, `0`, `9`), getter conventions, and "obvious" defaults.

Never promote a header comment, an opcode name, a remembered API, a single forum post, or a second-hand citation into engine behavior.

## Procedure

1. **Classify the claim.** Is it signature, argument domain, runtime behavior, or design precedent?
2. **Signature:** cite the public header file, opcode id, repo and commit. Stop there.
3. **Semantics:** find at least one call site (native/community source) and state the argument domain from that call. Check SP vs MP, team vs group, leader id vs formation slot.
4. **Version:** pin the game/engine version or header commit. Note drift (2015 headers vs 1.174; Bannerlord v1.3.14 vs v1.4.7; mod forks). If the claim is version-specific, say so.
5. **Label the claim:** `verified-by-call-site`, `declared-only`, `community-reported`, or `unverified`. Put the label in the sentence, not only in a footnote.
6. **Record provenance:** exact file:line, URL, capture/observation date; record inaccessible sources (403, Cloudflare, login) instead of implying they were read.
7. **Review:** hand the doc to `review-b2` or `E`; no self-approval and no builder-to-builder review. A reviewer's PASS does not turn an unverified claim into engine fact.

## Pressure scenario (GREEN test)

"You have 60 seconds and need one line for the 5th `add_visitors_to_current_scene` argument. The header says `group_no`; a forum post passes formation groups 5..7; the build is waiting. Ship it."

Correct response: header proves only the signature; find the Native MP call site (leader lookup → leader/owner player id); state that 5..7 is a type error; mark the `0`/`-1` sentinel unverified; do not decide from the header or the forum post. If you cannot find a call site, write `[unverified]` and name the missing evidence.

Second scenario: "`agent_get_group` returned 8..15 in a sealed run; use that as division 6 for the class matrix." Correct response: check the getter convention against a known value (`id == group` echo?), check the latest seal (`-1`), and do not use group values as divisions/order sub-classes until verified.

## Rationalization table

| Excuse | Reality |
| --- | --- |
| "The header is official API" | It declares a signature; it does not define MP argument semantics. |
| "The name says `group_no`, so it is a formation group" | The Native MP call passes a leader/owner player id. Names lie. |
| "Another mod passes formation groups" | Community tier, not engine proof; check its engine version and call site. |
| "0/-1 obviously means no leader" | Sentinels are unverified until observed or documented. Probe or mark UNKNOWN. |
| "I remember this op" | Memory is not revision. Re-fetch and cite. |
| "One source is enough" | Versions and mirrors drift; cross-check or label the limit. |
| "The wiki/thread says so" | Player/community observation, not engine behavior; label community and date it. |

## Red flags

- A line number without a repo/commit.
- "Always/never" taken from a header comment.
- A sentinel asserted as fact.
- A getter's return value used without checking its calling convention.
- A citation that is actually second-hand ("our earlier doc cites...").
- Formation/group ids passed as `team_give_order` sub-classes.
- A wiki/forum/mod source described as engine behavior.
- No `[unverified]` label where availability or semantics is untested.

## Checklist

- [ ] Claim classified (signature / semantics / precedent)
- [ ] Signature citations include repo + commit
- [ ] Semantics backed by a call site or implementation
- [ ] Argument domain checked across SP/MP, team/group, leader id
- [ ] Version/commit pinned; drift noted
- [ ] Sentinels and getter conventions labelled verified or `[unverified]`
- [ ] Exact file:line / URL / capture date recorded
- [ ] Inaccessible sources recorded, not implied
- [ ] No copied code/assets; paraphrased facts only
- [ ] Submitted to `review-b2`/`E`; no self- or peer-approval

**Baseline note:** the RED evidence above is documented project history (header-vs-call-site and getter-echo corrections), not a synthetic subagent test. Re-run the pressure scenario with a fresh builder before broadening this skill beyond citation discipline.
