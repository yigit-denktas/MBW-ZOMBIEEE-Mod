# City firearm accuracy profile - 2026-10-24 (task-22)

**Agent A - built-module stat profile only; no runtime/gameplay acceptance.**

## Owner request

"Firearms slightly more accurate, especially during sustained/serial fire." Modest
allowlisted buff, leave single-shot guns and non-firearms unchanged, default build
profile, patch only the built module.

## What was inspected

Compiled `item_kinds1.txt` header stats are flattened; for each item:

- `flags` token index = `4 + 2 * mesh_count`;
- `value` = `flags + 2`;
- **`accuracy` = `value + 6`**, followed by `difficulty`, `spd_rtng`,
  `shoot_speed`, and `max_ammo` (validated against Native bow/crossbow source
  stats: hunting bow acc 0/dif 0/spd 100/shoot 52, crossbow spd 43/shoot 66/ammo 1).

Pinned-module firearm values (`accuracy`): Beretta 92FS 73, SW5904 73, Browning
Cynergy 85, Remington 700 99, M82 0, M249 85, FAMAS 95, AK47 80, MP5 80,
HK MP5K 85, HK MP7 88, P90 89, M16A2 87, UZI 75, flintlock pistol 65.
The full-automatic weapons share one item-flag mask (`422212472471569`): M249,
FAMAS, AK47, FN SCAR-L, MP5, HK MP5K, HK MP7, P90, Mk12 SPR, M16A2.

## Profile

- **`default` (on):** automatic-flag group only, `accuracy += clamp(round(old*0.10), 5, 10)`
  (+8..+10 points on 80..97 values).
- **`stock`:** byte-identical copy of the original item table.
- Derived from the automatic flag mask anchored on `itm_m16a2` + `itm_mp5` (must
  share the mask); single-shot guard items Remington 700, Browning Cynergy,
  Beretta 92FS, SW5904 must exist and must *not* share the mask, otherwise the
  build fails closed. Item count, other tokens, all other item rows, factions,
  troops, missions and scripts are unchanged.

## Build

```text
py -3 tools\build.py --archive <owned RAR> --out <Modules\ZOMBIEEE_Remaster> \\
    --experimental-defenders 4 --city-guardposts --wave-reinforcements \\
    --tactical-recovery --defender-loadouts balanced-ai
```

`--firearm-accuracy stock` disables the profile. Receipt
`firearm_accuracy = {profile, changed[10], untouched_item_count, sha256_before,
sha256_after, runtime_verified=false}`.

## Offline evidence

- Tool tests: 9 (synthetic table parser/allowlist/guards/stock/rejections +
  original-asset apply/unchanged checks).
- Branch suite: all tests pass; chain verification reproduces the City chain
  with `item_kinds1.txt` as the fourth intentional original change.
- Built module verified: `changed_count=10`, `untouched_item_count=674`.
- **Not validated in gameplay:** recoil feel, sustained-fire accuracy, AI
  marksmanship. Runtime/D evidence required; no acceptance claimed.
