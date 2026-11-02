# Workflow: implement and evaluate a model experiment

## Trigger
A task explicitly targets model training, fine-tuning, model comparison, or new features for gaze/intent prediction.

## Steps
1. Read the repository audit, data card, metric policy, previous experiment cards, and current baseline.
2. State one falsifiable hypothesis. Identify the target, prediction unit, model input/output shapes, primary metric, safety metrics, dataset version, split IDs, and acceptance criteria.
3. Build an experiment config with fixed seed, optimiser/model parameters (as applicable), preprocessing, training budget, early-stopping rule, and output directory. Do not embed machine-specific absolute paths in committed configs.
4. Run data/shape/label contract checks and a tiny overfit/smoke test. A tiny subset is for pipeline validation only, not performance claims.
5. Evaluate the existing baseline on the chosen validation split using the same preprocessing/evaluation code. Record baseline metrics before trying a candidate.
6. Train a simple, suitable candidate first. For structured landmark/head-pose features, compare against the current polynomial/regression baseline; only use a CNN/video model if inputs and labels justify it and compute is available.
7. Save a checkpoint only with its config, code revision, data/split identifiers or hashes, preprocessing version, seed, and dependencies recorded.
8. Evaluate validation data; report regression error distribution or per-class/event metrics, latency, throughput, memory, and error cases. Keep the test set sealed.
9. Inspect errors by participant/session/device/lighting/glasses/head pose/face visibility when metadata and privacy rules allow. Investigate suspiciously perfect results for leakage or duplicate overlap.
10. Tune using validation data only. Freeze model and thresholds, then evaluate the final test set once for the planned comparison.
11. Complete `docs/ml/EXPERIMENT_CARD_TEMPLATE.md` and the model evaluation report. Store large/private outputs outside Git.
12. Test inference compatibility, failsafe paths, stale/low-confidence outputs, missing landmarks, camera loss, and dry-run cursor integration.

## Deliverables
- Reproducible config and run metadata.
- Baseline/candidate comparison table.
- Metrics and error slices.
- Model artefact plus provenance.
- Experiment card and known limitations.

## Exit gate
No promotion based solely on training loss, accuracy, one random split, or a tiny smoke run. No release if an absolute safety gate fails even when average regression metrics improve.
