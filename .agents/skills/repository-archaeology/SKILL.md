---
name: repository-archaeology
description: Map IntuiGaze's actual architecture, tests, configs, packaging, and safety paths before implementation. Use at project start, after major changes, or when documentation and source disagree.
---

# Repository archaeology

## Procedure
1. Inspect `git status`, root files, relevant directories, `README.md`, `pyproject.toml`, runtime/dev requirements, tests, CI and docs.
2. Trace a real sample through input capture, feature extraction, prediction/calibration, filtering, intent detection, and cursor actuation.
3. Search for thresholds, coordinate conversions, model files, random seeds, filesystem writes, camera calls, mouse calls and logging.
4. Run baseline tests and lint without making edits. Record actual results.
5. Verify packaging/runtime contradictions rather than correcting them by assumption.

## Output
Produce `docs/ml/REPOSITORY_AUDIT.md` with evidence-backed file paths, actual vs documented behavior, known gaps, safety risks, and ranked tasks. Distinguish “verified”, “inferred”, and “unknown”.

## Do not
- Rewrite architecture during audit.
- assume the dataset schema.
- claim the model is trained or tested without evidence.
- run live mouse actuation.
