# ML data governance and reproducibility

- Begin by documenting the prediction unit (frame, sequence, calibration session, or user session), input fields, target fields, collection process, licence/consent status, intended population, and exclusions.
- Do not assume the large dataset is automatically clean, representative, labelled, or licensed for this use. Audit it before preprocessing/training.
- Keep original data immutable. Write cleaned or derived assets to a new versioned location and record transformation code/config.
- Do not materialise the entire dataset in RAM unless a measured capacity analysis shows it is safe. Prefer streaming manifests, chunked readers, shards, memory-mapped arrays, or an indexed dataset API appropriate to the format.
- Store only paths or stable sample IDs in manifests; avoid copying source media into a second tree unless required. Keep raw data out of Git and remote logs.
- Verify label units, coordinate origin, screen resolution/scaling, frame timestamps, sample alignment, duplicate frames, missing labels, and impossible/out-of-range values.
- Detect duplicated or correlated samples before splitting. Related frames from the same participant/session/video must not straddle train and test when that would inflate generalisation.
- Use group-aware splits when the goal is generalisation to unseen participants, sessions, devices, or recording environments. Name the group unit explicitly. A random row split alone is not sufficient evidence of unseen-user performance.
- Freeze the final test partition before hyperparameter tuning. Never select a model, threshold, feature, calibration policy, or stopping epoch by repeatedly inspecting the test score.
- Fit normalisation, imputation, feature selection, dimensionality reduction, and learned preprocessing on training data only; apply the fitted transformation to validation/test/inference data.
- Record a dataset version/hash, split manifest, code revision, config, environment, seed, run ID, metrics, and artefact checksums for every reported experiment.
- If subject IDs are unavailable, state that cross-subject leakage could not be ruled out. Do not describe row-level test metrics as unseen-person performance.
