# Workflow: release and model promotion gate

A release is blocked by any failed mandatory gate below. A weighted score does not override a safety failure.

## Mandatory gates
- [ ] All relevant unit/integration tests pass, or pre-existing failures are explicitly isolated and approved.
- [ ] Lint/type checks pass according to the project policy.
- [ ] Dataset provenance, licence/consent, split design, and model provenance are documented.
- [ ] No train/validation/test group overlap that invalidates the stated generalisation claim.
- [ ] Frozen test evaluation is complete and has not been used for model/threshold selection.
- [ ] Primary regression/classification metrics and operational metrics are reported with units, sample counts, and grouping.
- [ ] No unexplained major regression in error tails, false activations, missed intent events, latency, or important subgroups.
- [ ] Emergency stop, opt-in, no-actuation test mode, confidence gate, and fail-closed click behavior pass tests.
- [ ] Camera loss, stale frame, invalid landmarks, invalid calibration and model-load failure fail safely.
- [ ] Runtime, memory, frame-rate and latency measurements match target-hardware requirements.
- [ ] Privacy, data retention, licence, dependency and artifact storage have been checked.
- [ ] README/changelog/model card/release notes explain changed behavior and limitations.

## Promotion decision
Record one: `PASS`, `PASS WITH DOCUMENTED LIMITATIONS`, or `BLOCKED`. Include approver/date, artefact checksum, version, evaluation report, unresolved risks, rollback path, and the exact baseline comparison. Never label an unevaluated model as production-ready.
