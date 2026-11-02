# Experiment card — [run ID]

## Hypothesis
- Question / hypothesis:
- What changes versus baseline:
- Success criteria (define before final test):

## Provenance
- Date / operator:
- Git commit:
- Python/runtime/OS/device:
- Dependencies/environment lock:
- Dataset version/hash:
- Split manifest/hash and group unit:
- Config path/hash:
- Random seed(s):
- Model/checkpoint path and SHA-256:

## Task contract
- Prediction task and unit:
- Input schema and preprocessing:
- Target schema/units:
- Baseline model:
- Candidate model:
- Primary metric:
- Guardrail/safety metrics:
- Selection/early stopping rule:

## Results
| Metric | Unit / definition | Baseline | Candidate | Delta | Group/sample count | Threshold / requirement |
|---|---|---:|---:|---:|---:|---|
| MAE | px / exact definition | | | | | |
| RMSE | px / exact definition | | | | | |
| Median Euclidean error | px | | | | | |
| P95 Euclidean error | px | | | | | |
| Target hit rate | tolerance defined in config | | | | | |
| False intent triggers | per minute/hour | | | | | |
| Missed intent events | rate | | | | | |
| End-to-end latency | ms, percentile specified | | | | | |
| Sustained throughput | FPS | | | | | |
| Peak memory | MB/GB, hardware specified | | | | | |

Remove rows that do not apply and add task-specific metrics rather than filling them with invented values.

## Robustness/error analysis
- Results by participant/session/device/resolution:
- Lighting, glasses/reflections, head pose and face-visibility slices where available:
- Error tails and failure examples:
- Leakage checks:
- Confidence intervals / fold or seed spread:

## Safety and deployment
- Dry-run/cursor adapter tests:
- Emergency stop / failsafe tests:
- Low-confidence and stale-prediction behavior:
- Camera/model failure behavior:
- Latency/model-size constraints:

## Decision
- Decision: `REJECT` / `REVISE` / `PROMOTE TO FURTHER VALIDATION` / `APPROVED FOR RELEASE REVIEW`
- Why:
- Limitations:
- Follow-up tasks:
- Reviewer/date:
