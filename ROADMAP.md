# IntuiGaze ML roadmap and task gates

This roadmap begins with audit and data readiness. It does not assume the dataset's format, number of subjects, labels, licence, or hardware requirements.

## Phase 0 — Establish a trustworthy baseline (P0)
- [ ] Map actual code path end-to-end and record files/interfaces.
- [ ] Run and record existing tests/lint/type checks before changes.
- [ ] Identify current gaze mapping model and all calibration, smoothing, confidence and click thresholds.
- [ ] Confirm how the model is persisted/loaded and how inference errors are handled.
- [ ] Reconcile Python runtime/package naming and duplicate/stale configuration.
- [ ] Create `docs/ml/REPOSITORY_AUDIT.md`.
**Gate:** current behavior is reproducible enough to compare against a candidate; safety path has an owner and tests.

## Phase 1 — Dataset intake and governance (P0)
- [ ] Confirm dataset source, licence, consent/use restrictions and intended use.
- [ ] Inventory files/bytes/manifest records without loading everything into RAM.
- [ ] Define sample unit, feature schema, target schema and label units.
- [ ] Audit missingness, ranges, duplicates, corrupt media, alignment and class balance.
- [ ] Identify participant/session/video/device grouping fields.
- [ ] Create data card and deterministic split manifests/hashes.
- [ ] Decide data retention and ignore rules without putting data in Git.
**Gate:** labels and units make sense; data provenance is known; split strategy supports the intended claim; leakage risks are resolved or explicitly limited.

## Phase 2 — Baseline protocol (P0)
- [ ] Implement a tiny pipeline smoke test with synthetic or approved sample data.
- [ ] Evaluate the existing polynomial/regression mapping baseline, if reproducibly available.
- [ ] Freeze primary metrics and acceptance criteria before candidate comparisons.
- [ ] Record runtime, memory, frame-rate and latency on named hardware.
- [ ] Validate per-subject/session aggregation and group split boundaries.
**Gate:** baseline results and run metadata can be reproduced.

## Phase 3 — Candidate experiments (P1)
- [ ] Select the model family based on input modality and label size: feature regression for landmark/head-pose features; image/video architecture only if its labels, data volume and compute justify it.
- [ ] Use train-only fitting for all learned preprocessing.
- [ ] Compare one change at a time against the baseline on identical validation splits.
- [ ] Track runs using experiment cards; start with one seed and add repeats/folds for credible uncertainty.
- [ ] Run error slices: participant/session, device/resolution, lighting, glasses/reflections, head pose, face visibility, calibration age, as available and privacy-permitted.
- [ ] Measure deployment cost: CPU/GPU/RAM, model size, cold start, steady-state latency and FPS.
**Gate:** candidate improves the declared primary objective without violating operational or safety constraints.

## Phase 4 — Event/intent model, if in scope (P1)
- [ ] Define blink/dwell/gesture event labels and matching tolerance.
- [ ] Quantify class balance and negative-event duration; avoid frame-wise leakage from the same event/session.
- [ ] Report per-class precision/recall/F1, macro-F1, confusion matrix and PR-AUC where appropriate.
- [ ] Measure false triggers per minute/hour, missed triggers and end-to-end click latency.
- [ ] Choose thresholds on validation data only and assess consequences for accessibility/usability.
**Gate:** click behavior satisfies pre-agreed false-trigger and missed-event requirements; all safety filters pass.

## Phase 5 — Closed-loop validation (P1)
- [ ] Use a dry-run cursor backend first.
- [ ] Test target acquisition, overshoot, jump rate, latency, jitter, stale predictions and reacquisition after face loss.
- [ ] Test emergency stop and corner escape independently of gaze inference.
- [ ] Run opt-in manual evaluation only with informed participants and controlled conditions.
**Gate:** no-actuation unit tests pass; real-control tests are deliberately authorised and supervised; failures fail safely.

## Phase 6 — Packaging and release (P2)
- [ ] Export the exact model + preprocessing + label/coordinate contract.
- [ ] Verify model artefact checksum and provenance; document licensing.
- [ ] Run a clean-environment load/inference smoke test.
- [ ] Verify backward compatibility, calibration profile compatibility and fallback behavior.
- [ ] Fill model card, evaluation report, changelog and limitations.
- [ ] Complete `.agent/workflows/05-release-gate.md`.
**Gate:** every mandatory release requirement is signed off. A high average metric cannot compensate for a failed safety gate.

## Priority definitions
- **P0:** data integrity, safety, reproducibility, metric validity, test leakage, runtime breakage.
- **P1:** model quality, generalisation, inference latency, usability, error analysis.
- **P2:** tooling convenience, dashboards, additional model trackers, visualisations.

## First concrete backlog
1. `[P0]` Repository audit report and clean baseline test run.
2. `[P0]` Dataset inventory + schema/label contract.
3. `[P0]` Data card + group-aware split plan.
4. `[P0]` Current model evaluation harness and baseline scorecard.
5. `[P0]` Safety tests with mocked cursor adapter.
6. `[P1]` Candidate model experiment with identical frozen splits.
7. `[P1]` Subgroup/error and latency analysis.
8. `[P2]` Reproducible experiment summaries/plots and model registry only if simple reports become insufficient.
