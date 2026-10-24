# AGENT D — runtime validation handoff (hands-off City sessions)

Updated: 2026-10-24 12:35 Europe/Berlin. Owner-facing scope: **runtime evidence
only**. This document records what was observed in sealed sessions, what the
telemetry can and cannot prove, and the exact commands/bundles. It does **not**
award acceptance, does not change the Project Record ledger, and does not
modify the game tree.

## 1. Installed module at the time of the balance-regression phase

Owner/Lead installed a stock-block + weak-roster City module at 12:18:07:

- 1,072 files, 31 triggers, `native_roster_patch.invader_candidates = [894]`
  (weak wave-1 = original slow `trp_invader1` only),
  `defender_candidates = [981, 982, 983, 984]`
- `zombie_block = null` (**intentionally stock** — the owner rejected wooden
  shields in zombie hands; A's shield patch exists only in pipeline builds)
- aggregate module digest
  `bcab4e56381b58f8685268c660252ab8bbc57ff37c992a1f90aaa83b4dfb8827`
- `runtime_verified = false`

`A`'s later branch in this phase (`941ed5b`, merged `8f0d17a`) moves the
defender hold to the rear spawn line and fields 8 native defenders; main
`332560a` also stages weak generic bots to `894` only. A **final sealed
validation from that merged main is still pending** (blocked only by live owner
sessions and Lead coordination; nothing in this file should be read as its
result).

## 2. Accepted phase evidence (sealed owner sessions, installed module)

Evidence root: `_zom-main-merge/local/session/play-city/launches/`
(launcher receipts embed C's sealed summary; each flight is an 8-file verified
bundle).

### `09ac23eb7a2549f68238a86e1ec0b88e` — weak-wave1 (accepted phase record)
- `enemy_profile=weak-wave1`, `team2_bots=8`, `team0_bots=4`,
  `rotation_sha256=a8fc716f…4cc6`, `clean_stop`, loopback-only, join+mission
  observed, `evidence={verified:true, file_count:8}`, `runtime_verified=false`
- `waves.wave1.team1_classes = {native_zombie: 17}`, `troops_team1 = {894: 17}`
  → **wave 1 is the original slow Zombie only; no 907–911, no strong/mounted
  generic fill** (`horses_team1=0`; mounted telemetry unavailable)
- defenders: `weapon_modes={ranged:66}`, `ammo={positive:66, zero:0}`,
  `ranged_agents_team0=4`, `melee_fallback_team0=0` → **defenders kept firing**
  (ranged preference fixed); `defender_kills=6`, `defender_deaths=15`;
  movement `{moving:10, distinct_positions:44}`; `hold_behavior_observed=false`
- `no_player=true` in summary is a **last-heartbeat artefact**; composition shows
  the player joined/left (`player_joined`, `player_left` present).

### `61c47607444948d8825e3246bf500aed` — weak-wave1 (previous build)
- wave 1 natives `894:18` + weak generic `902..906` (2/3/3/4/4);
  defenders ranged 61/61 samples, ammo positive, kills 5 / deaths 15;
  clean_stop, 8-file verified. Kept as the pre-`894` staging comparison.

### `a2396dee…` — native-only (negative result, keep as evidence-gated experiment)
- `team2_bots=0`: team1 stayed **0** for the session, `waves.max=0`,
  `native_zombie_roster_not_observed`; defenders ranged 72/72 samples, 0 kills.
- Conclusion: native-only does **not** start the native wave with a player; it
  reproduces the original no-wave gating and is not a playable profile.

## 3. Earlier D-lane runtime evidence (kept for lineage, different builds)

Sealed bundles under `local/session/` (gitignored, machine-local):

- `ai-evidence-final-defenders`, `ai-evidence-final-noclient-defenders`,
  `ai-evidence-disc28e-troopfallback` — native defenders `981–984` spawn and are
  sampled (troop-id fallback); movement out of spawn proven, stable hold unproven.
- `ai-evidence-wave2c-attempt` — **wave 2 reached** (`waves.max=2`) with
  8 defenders + `set_player_respawn_as_bot 1`; native round reset otherwise caps
  wave 1 (A's lifecycle analysis).
- `ai-evidence-disc28c-nospam` — 0 engine-error lines, `group_convention=unknown`;
  divisions 5–7 remain unobservable (no fabricated divisions).
- `PLAYABLE_EVIDENCE.md`, `NIGHT_STATUS_D.md` — full attempt log and receipts.

## 4. Telemetry limits (do not over-read)

- `shield_telemetry_unavailable`: no verified read-only block/shield op; zombie
  blocking **cannot be asserted** by the probe, and the installed module is
  stock-block anyway. "Zombies block = 0" stays unverified.
- `mounted_telemetry_unavailable`: `mounted_team1`/`horse_ids_team1` are
  `null`; mounted enemies are only inferable from troop ordinals (908 has
  `itm_warhorse`), not from agent state.
- `action_telemetry_unavailable`: no current-action field.
- `group_convention_unknown` / `defender_division_unreadable`: division 5–7
  adoption and hold/post identity stay unobserved; `hold_behavior_observed`
  is always false by design.
- `defender_deaths` = observed alive-disappearance accounting (round reset does
  not count), **not** engine kill credit; `kills_*` are agent lifetime counters,
  not session kills or a victory claim.
- `no_player` reads the last heartbeat only — always read with
  `composition.mode`.
- Pure no-client mode has `no_probe_heartbeats` / `pre_round_only` (mission
  triggers pause until a round starts).

## 5. Reproduce (after owner sessions are quiet)

```powershell
# read-only plan against the installed module (no game, no install)
python -m launcher.play_city plan --enemy-profile weak-wave1

# sealed validation, reusing the installed module (never modifies game tree)
python -m launcher.play_city play --no-install --enemy-profile weak-wave1 `
  --max-minutes 3 --json

# one-shot D runner: auto-join clicks (no human input), mid-run screenshot,
# receipts/state saved to local/session/playcity_<tag>_*
python local/session/playcity_validate.py --profile weak-wave1 --max-minutes 3 --tag <tag>
```

Preconditions: **no Warband process running** (single loopback host on
127.0.0.1:7240); the launcher owns host/client lifecycle, recorder first,
signed stop and 8-file manifest verify. Screenshots: `local/session/playcity_*_mid.png`.

## 6. Open items for the final validation (Lead will schedule)

1. Rebuild/validate from merged main with A's rear defensive line + 8 defenders
   (`8f0d17a`/`332560a`) — **module-install decision belongs to Lead/owner**;
   D does not install while the owner is live.
2. Confirm at the new build: weak wave-1 (894 or staged), defenders ranged
   (weapon_mode/ammo), 8 native defenders spawn, rear-line positions/hold
   samples, wave progression, deaths/kills.
3. Keep native-only as a recorded negative; keep shield/mounted/action as
   unobservable fields, not zeros.
4. No ledger acceptance; the Project Record stays authoritative and untouched
   by this handoff.
