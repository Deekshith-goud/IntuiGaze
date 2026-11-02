# ML readiness audit scorecard

Use this to score process/readiness, not to disguise model quality as one number. Score each area 0, half points, or full points with evidence. Mandatory gates below still block progression even if the points sum is high.

| Area | Max | Full-credit evidence |
|---|---:|---|
| Task and label contract | 10 | Prediction unit, target meaning/units, coordinate frame and intended use are explicit and tested |
| Data provenance and governance | 10 | Source/licence/consent, privacy handling, retention and access are documented |
| Data quality audit | 15 | Missingness/ranges/duplicates/corruption/alignment and exclusions are measured with a reproducible report |
| Split design and leakage prevention | 15 | Group-aware split matches claim; frozen test; transforms fit on train only; overlap audit documented |
| Baseline and metric validity | 15 | Existing baseline measured; regression/classification metrics fit the target; units and thresholds defined |
| Reproducibility and artefact lineage | 10 | Config, seed, code revision, data/split hash, environment and checkpoint checksum captured |
| Robustness/error analysis | 10 | Tail errors and relevant participant/session/device conditions inspected |
| Safety and fail-safe testing | 10 | No-actuation default, explicit opt-in, emergency stop, fail-closed click guard and failure tests pass |
| Runtime/deployment readiness | 5 | Latency, FPS, memory and target hardware requirements measured |
| **Total** | **100** | Evidence-based readiness summary |

## Interpretation
- `0–49`: not ready for model training claims; close data/contract gaps.
- `50–69`: exploratory experiments only; gaps must be tracked.
- `70–84`: controlled candidate experiments are reasonable; do not imply release readiness.
- `85–100`: readiness may be high, but release still requires every hard gate and a separate model evaluation.

## Mandatory hard stops (cannot be averaged away)
- Unknown/misunderstood labels or coordinate units.
- Unclear legal permission to use the data.
- Unresolved test leakage that invalidates the claim.
- Test data used to tune the final model/threshold.
- No trustworthy baseline or no task-appropriate evaluation.
- Broken emergency stop, unsafe click behavior, or live actuation in automated tests.
- Missing provenance for the release candidate.

Each awarded point must reference a file, command output, audit result or signed decision. An agent must not assign a score based on intention or unchecked TODOs.
