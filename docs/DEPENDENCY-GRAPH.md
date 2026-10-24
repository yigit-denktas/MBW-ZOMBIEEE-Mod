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
- The current frontier is `ZOM-DISC-42` (task-42 sealed validation), `ZOM-DISC-40` (standoff implementation), `ZOM-DISC-34` (wave-2 not observed), and the open required gates. F's M2 installer/release work is merged, and E's legal dossier is delivered but `ZOM-LEGAL-01` remains open, so `ZOM-REL-01` stays blocked.
- `ZOM-DISC-39` is evidence, not acceptance: sealed 8-file task-34 run with 8 defenders refilled, rear positions and wave-1 894 only; wave 2 stayed unobserved in the 3-minute window.
| ZOM-DISC-40 | Agent A — implementation; Agent D validation | owner standoff/explosives design note | active | ZOM-DISC-35 | ZOM-AI-02 | Blocks ZOM-AI-02/03 behavioral acceptance until sealed. |
| ZOM-DISC-41 | Agent D — sealed validation; owner retains acceptance | task-38 validation queue | done | ZOM-DISC-34, ZOM-DISC-35 | ZOM-QA-02 | Supports QA-02; wave-2 gate still unobserved. |
| ZOM-DISC-42 | Agent D — sealed validation; owner retains acceptance | task-42 validation queue | active | ZOM-DISC-40, ZOM-DISC-41 | ZOM-QA-02 | Final validation gate before standoff can be judged; supports QA-02. |
| ZOM-DISC-43 | Lead — UI/tracker integration | owner Pages/dependency-map feedback | done | — | ZOM-REC-03 | Supports REC-03 progress-view validation; no required credit. |
| ZOM-DISC-44 | Agent C — telemetry; Agent A implementation | task-42 sealed validation | active | ZOM-DISC-42 | ZOM-OBS-01 | Unblocks proof for speed/hold; without it those claims stay config-only. |
| ZOM-DISC-45 | Agent D — sealed validation; owner retains acceptance | task-42 sealed validation | active | ZOM-DISC-42 | ZOM-QA-02 | Supports QA-02 and WAVE-01; without it standoff/balance remain partially unproven. |
| ZOM-DISC-46 | Agent A — AI/balance; Agent D validation | task-42 sealed validation/owner balance feedback | active | ZOM-DISC-40, ZOM-DISC-42 | ZOM-WAVE-01 | Blocks WAVE-01 acceptance; depends on standoff validation and telemetry. |
| ZOM-DISC-47 | Agent A — implementation; Agent D validation | owner consolidation after task-42 | active | ZOM-DISC-40, ZOM-DISC-46 | ZOM-AI-02 | Primary balance lever; depends on standoff and KD work. |
| ZOM-DISC-48 | Lead — coordination; reviewers A/C/D/E/F/G | owner consolidation request | active | — | ZOM-REC-03 | Unblocks coordinated delivery; no required credit. |
| ZOM-DISC-49 | Agent C — research; Agent D validation | owner consolidation request | active | ZOM-DISC-44 | ZOM-OBS-01 | Improves telemetry proof and validation speed. |
| ZOM-DISC-50 | Agent F — release metadata; Agent E review | owner consolidation request | active | ZOM-DISC-37 | ZOM-REL-01 | Supports release gate; no acceptance alone. |
| ZOM-DISC-51 | Agent G — sourcing; Agent E licence review | owner consolidation request | active | — | ZOM-LEGAL-01 | Supports legal/release and future cosmetics layer. |
| ZOM-DISC-52 | Agent E — independent reviewer; Lead merges | owner consolidation request | active | ZOM-DISC-38, ZOM-DISC-50, ZOM-DISC-51 | ZOM-REC-03 | Blocks release/asset acceptance until reviewer signs off. |
| ZOM-DISC-53 | Agent A — gating; Agent D validation | D 600s wave-2 validation | active | ZOM-DISC-34 | ZOM-WAVE-01 | Blocks WAVE-01 balance; depends on task-34 visitor gating. |
| ZOM-DISC-54 | Agent A — AI/formation; C research; D validation | owner cohesion/formation feedback | active | ZOM-DISC-47 | ZOM-AI-03 | Blocks AI-03 hold/cohesion acceptance; depends on task-46 loadouts. |
| ZOM-DISC-55 | Agent A — AI/balance; D validation | owner live feedback 2026-10-24 | active | ZOM-DISC-46, ZOM-DISC-47 | ZOM-WAVE-01 | Blocks WAVE-01 behavior acceptance. |
| ZOM-DISC-56 | Agent A — wave/reinforcement; C telemetry; D validation | owner live feedback 2026-10-24 | active | ZOM-DISC-47, ZOM-DISC-54 | ZOM-WAVE-01 | Supports WAVE-01/QA-02 clarity. |
| ZOM-DISC-57 | Agent A — troops/loadout; G assets | owner live feedback 2026-10-24 | active | ZOM-DISC-47 | ZOM-AI-03 | Visual/representation support; no required credit alone. |
| ZOM-DISC-58 | Agent H — research; C/A review | owner live feedback 2026-10-24 | active | — | ZOM-AI-03 | Feeds long-term AI design; no runtime credit. |
| ZOM-DISC-59 | Agent C — probe; Agent D sealed run | task-45/46 seal triage | active | ZOM-DISC-34, ZOM-DISC-53 | ZOM-OBS-01 | Blocks gating/speed fix strategy; must run before more patches. |
