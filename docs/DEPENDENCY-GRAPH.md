# Work dependency graph

Generated from the authoritative `progress/ledger.json` on the current source snapshot. Required gates and the new discovered work are both shown. Solid arrows are hard dependencies (prerequisite → dependent); dashed arrows are support/unblock links into a required outcome. The required denominator is unchanged: discovered work is supplemental and cannot earn required credit.

**Interactive map:** [Project tracker → Dependencies & frontier](https://yigit-denktas.github.io/MBW-ZOMBIEEE-Mod/#dependency-graph). The map is generated from `progress/ledger.json`; click any node to open the matching task card.

## New discovered work (owner / while / effect)

| ID | Owner | Occurred while | State | Depends on | Supports | Graph effect |
| --- | --- | --- | --- | --- | --- | --- |
| ZOM-DISC-30 | Agent C — research/prototype; owner retains runtime acceptance | task-30 live owner test; survivors charging + sprint complaints | done | — | ZOM-AI-03 | Unblocks task-38 speed/hold implementation; supports ZOM-AI-02/ZOM-AI-03/ZOM-WAVE-01. |
| ZOM-DISC-31 | Agent E — provenance/credits; owner retains release acceptance | task-30/35 research sweep | done | — | ZOM-LEGAL-01 | Feeds task-35 synthesis and legal/attribution review. |
| ZOM-DISC-32 | Agent F — launcher/test harness; owner retains release acceptance | task-34 validation queue | done | ZOM-DISC-34 | ZOM-QA-01 | D pre-launch gate for wave/refill/hold validation. |
| ZOM-DISC-33 | Agent A — implementation; Agent D sealed it; owner retains acceptance | task-30 rear-line live owner test | active | ZOM-DISC-28 | ZOM-AI-03 | Keeps the AI squad alive; prerequisite for speed/hold tuning and wave survival. |
| ZOM-DISC-34 | Agent A — implementation; Agent D validating | task-34 wave-2 Fast Zombie wipe | active | ZOM-DISC-33 | ZOM-WAVE-01 | Blocks strong/mounted wave spikes; must pass before ZOM-WAVE-01 balance can be judged. |
| ZOM-DISC-35 | Agent A — implementation; Agent D validation | owner speed/charge complaints after task-30 | active | ZOM-DISC-30, ZOM-DISC-33, ZOM-DISC-34 | ZOM-AI-03 | Primary unblock for ZOM-AI-03 hold behavior and ZOM-WAVE-01 balance; depends on research + rear line + wave gating. |
| ZOM-DISC-36 | Agent C — telemetry; Agent D re-seal | task-38 preparation; no speed/order readback existed | done | ZOM-DISC-30 | ZOM-OBS-01 | Unblocks proof for task-38 and D&#x27;s final validation. |
| ZOM-DISC-37 | Agent F — implementation; owner retains release acceptance | M2 milestone review | active | ZOM-REC-01 | ZOM-WIN-02 | Supports ZOM-WIN-02/ZOM-WIN-03 and ZOM-REL-01; cannot close M2 alone. |
| ZOM-DISC-38 | Agent E — evidence; owner/legal acceptance | M4 legal/publication gate | active | — | ZOM-LEGAL-01 | Supports ZOM-LEGAL-01 and blocks ZOM-REL-01 until owner decisions/qualified review. |
| ZOM-DISC-39 | Agent D — sealed validation; owner retains acceptance | task-34 validation run | done | ZOM-DISC-33, ZOM-DISC-34 | ZOM-QA-02 | Supports ZOM-QA-02; waves.max=1 leaves wave-2 acceptance open. |

## How to read the frontier

- Start at the required milestone gates at the top. A gate is accepted only when its own criterion is met; a discovery node cannot substitute for it.
- A solid arrow means the dependent node is blocked until its prerequisite is at least resolved. `ZOM-DISC-35` (speed/hold patch) depends on research (`30`), rear line/refill (`33`) and wave gating (`34`).
- A dashed arrow is not acceptance: it is the discovered work opening or supporting a required outcome (for example `30 → ZOM-AI-03`, `34 → ZOM-WAVE-01`).
- The current frontier is `ZOM-DISC-35` (A implementing), `ZOM-DISC-34` (wave-2 not yet observed), `ZOM-DISC-37` (M2 installer/release) and `ZOM-DISC-38` (M4 legal gate). `ZOM-DISC-38` keeps `ZOM-REL-01` blocked.
- `ZOM-DISC-39` is evidence, not acceptance: sealed 8-file task-34 run with 8 defenders refilled, rear positions and wave-1 894 only; wave 2 stayed unobserved in the 3-minute window.
