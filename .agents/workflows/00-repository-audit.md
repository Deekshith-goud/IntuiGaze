# Workflow: repository audit before model work

## Trigger
At the beginning of the ML phase, before architectural refactors, or when the codebase appears inconsistent.

## Steps
1. Inspect `git status`, root tree, dependency files, test configuration, CI workflows, public interfaces, and existing documentation.
2. Map the actual pipeline: capture -> face/iris landmarks -> feature extraction -> calibration/mapping -> smoothing/confidence filter -> intent detection -> cursor actuator.
3. For each stage, identify implementation file, current test coverage, runtime assumptions, inputs/outputs, failure modes, and whether it touches OS-level state.
4. Find the current baseline model, calibration flow, intent thresholds, failsafe path, and how predictions are logged/evaluated.
5. Inspect naming/packaging contradictions. In particular, verify whether `eyenav` naming in packaging is intentional or stale before changing it; verify declared Python version consistency.
6. Run existing tests/lint without modifying source. Classify failures as baseline, environment, or likely defect.
7. Write `docs/ml/REPOSITORY_AUDIT.md` using the template below; include exact file paths and evidence, not assumptions.
8. Create a dependency map and a gap list ranked P0 safety/data-integrity, P1 reproducibility/correctness, P2 maintainability, P3 convenience.

## Deliverables
- Verified architecture map.
- Test/lint baseline.
- Current model and inference contract.
- Data/dataset unknowns.
- Safety/privacy gaps.
- Recommended smallest next changes.

## Exit gate
No training implementation starts until the prediction target, current baseline, data format/labels, split unit, and safety requirements are recorded. If one is unknown, the next task is to inspect or decide it, not guess.

## Suggested report skeleton

```markdown
# IntuiGaze repository audit
- Date / commit:
- Environment:
- Commands run and results:
## Verified pipeline
## Existing tests and gaps
## Current model and metrics
## Data facts and unknowns
## Safety and privacy review
## Packaging/config inconsistencies
## Prioritised tasks with acceptance criteria
```
