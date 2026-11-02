# Workflow: investigate a model or cursor regression

1. Reproduce with the same input, code revision, model artefact, config, screen resolution/DPI, and calibration profile (if safe and consented).
2. Determine layer: capture/frame timing, landmarks, feature extraction, coordinate transform, model prediction, smoothing, confidence filter, intent, or OS adapter.
3. Preserve the last-known-good baseline and compare intermediate outputs. Avoid changing multiple thresholds at once.
4. Check data/feature schema drift, coordinate units/origin, resize/crop transforms, stale frames, out-of-range values, calibration validity, and preprocessing parity.
5. Create a minimal synthetic regression test and a replay fixture without raw personal video where feasible.
6. Fix root cause; test the adverse/failure case and verify failsafe still works.
7. Rerun baseline and candidate on a frozen validation set. Report metric deltas and tail/false-trigger changes, not only qualitative video impressions.
8. Document root cause, fix, affected versions, test evidence, and any required recalibration.
