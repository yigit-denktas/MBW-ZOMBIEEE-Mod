# Fire modes and reticle: WSE2 surface evidence (task-59)

Observation date 2026-10-24. Read-only investigation; no game launch, no asset
copy, no acceptance claim.

## Manual single/burst/auto switching

**Current WSE2 1.1.5.4 Lua surface used by our probe** (`overlay/lua/main.lua`)
exposes mission/agent operations and `game.addTrigger`; it calls only
`game.agentsIt`, `game.addTrigger`, `game.const`, `game.gvar`,
`game.getCurTemplateId`, `game.getNumTriggers`, `game.multiplayer_is_server`,
and agent getters such as `agent_get_*`. A printable-string scan of the pinned
`mb_warband_wse2.exe` / `mb_warband_wse2_x64.exe` found **no `getKey`,
`onKey`, `registerKey` or equivalent input-binding symbol**, and the pinned
native header (`header_vee.py`) has **no mission-template opcode that reads
keyboard input**. There is also no native mission-template op to open a
presentation or read a presentation key event.

Consequence: a **live in-game key toggle is not implementable on the current
Warband/WSE2 surface** with the reviewed APIs. This is an engine/API limit, not
a tuning choice. Concrete UI path if owner requires live switching:

1. Upstream WSE2 Lua would need to expose a key/input callback (or a
   presentation-key API) in a future build; then a small Lua `presentation`
   overlay can cycle `single/burst/auto` and call the two agent modifiers.
2. Until then, the supported path is a **pre-game selection** written into the
   City build/receipt (e.g. `--fire-mode single|burst|auto|ai`), which changes
   the AI/player modifiers for that session without mid-session switching.

The current implementation therefore keeps the **AI wave-cycle policy**
(single -> burst -> auto by `wave_number % 3`) and records the mode arrays in
the receipt. No false claim of manual switching is made.

## Reticle / target icon width

The City module and the pinned original Beta 0.4 module contain **no
reticle/crosshair texture**; file search found only crossbow *sounds*
(`reload_crossbow_1.ogg`, etc.), no `Textures` reticle asset. Therefore the
on-screen reticle is supplied by the engine/game UI, not by a module texture
we can resize.

Item accuracy changes the **spread/aim statistic**, which tightens shot
dispersion; whether the visible reticle icon width follows that statistic is
**unverified and must be checked in-game by D** (before/after screenshots at the
same weapon/range). If the icon is fixed, the path is a **UI asset task**:
G/#40 author a narrower reticle texture (or a UI presentation override) with
documented ownership/licence, then D validates the exact installed asset. A is
not claiming the icon is narrowed by the accuracy delta alone.

## Corrections from C's cross-review (task-59)

- `2092`/`2094` set **accuracy/reload percentages only**. This build exposes
  **no engine fire-mode setter/getter**, so the `single/burst/auto` labels are
  **accuracy/reload tuning profiles**, not an actual single/burst/auto weapon
  mode switch. Receipt records `fire_mode_semantics`; D cannot validate an
  engine fire mode from these modifiers.
- The item-accuracy patch in `tools/firearm_balance.py` changes the built
  **global item table**, so it affects every user of the module, not only City
  survivors; receipt records `scope=global_item_table_not_city_only`. The
  City-scoped lever is the per-agent `2092` modifier.
- Higher `2094` = faster reload is an **assumption** from community headers
  (percent, 100 default, 0..1000); receipt records
  `reload_direction=unverified_percent_assumed_higher_is_faster`. D must
  validate reload/cadence intervals, not infer direction from the value.
- New/refilled bots read **100%** until the next 5 s tick (spawn transient);
  telemetry should show this as observed data, not a failure.
- **Pre-game selector implemented:** `tools/build.py --fire-mode
  {ai,single,burst,auto}` (default `ai`) selects the session tuning profile;
  receipt records `fire_mode` and `fire_mode_policy`. This is a pre-game
  session choice, not a mid-session key switch.

