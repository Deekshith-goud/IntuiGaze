# Workflow: large-dataset intake and audit

## Trigger
Before using a new or existing large dataset for training, fine-tuning, or validation.

## Steps
1. **Locate and protect:** confirm dataset root and licence/consent. Keep raw data outside Git and do not upload data to external services. Record only safe metadata in reports.
2. **Inventory:** count files by extension, total bytes, folder distribution, and manifest records. Estimate storage, decode throughput, training throughput, and checkpoint capacity before full runs.
3. **Define sample unit:** frame, clip, calibration trial, participant-session, or event. Identify the unit represented by each manifest row.
4. **Inspect schema:** identify features, targets, IDs, timestamps, coordinate systems, screen resolution/DPI, frame references, camera/device metadata, labels and missing-value conventions.
5. **Validate labels:** check units/ranges, coordinate origin, target alignment, invalid sentinels, impossible values, timestamp order, duplicate rows/media, and label imbalance. Never discard rows silently; count and explain exclusions.
6. **Validate media references:** check missing files, corrupt/unreadable items on a bounded sample, inconsistent dimensions/frame rates, and failed decodes. Log counts and IDs/paths privately.
7. **Group leakage review:** identify participant/session/video/device groups and duplicate sources. Decide the required generalisation claim; create group-aware partitions where appropriate.
8. **Create data card:** fill `docs/ml/DATA_CARD_TEMPLATE.md`, including licence, collection, intended use, limitations, sensitive data, retention, and split strategy.
9. **Create split manifests:** save deterministic train/validation/test sample IDs or paths and hashes outside Git if identifying. Ensure no group overlap for the chosen evaluation.
10. **Create a bounded prototype:** read a small, representative slice and test the full transform end-to-end. Record memory and throughput before scaling.

## Deliverables
- Data card.
- Inventory/audit JSON.
- Schema and label contract.
- Leakage/split plan.
- Exclusion report.
- Storage and compute estimate.

## Exit gate
Do not train if the target meaning or units are unknown, licence/consent is unclear, test leakage is unresolved, or media/labels are misaligned. Do not treat total row count as a quality measure.
