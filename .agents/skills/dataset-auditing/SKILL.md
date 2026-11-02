---
name: dataset-auditing
description: Safely inspect large gaze or intent datasets, manifests, labels, media references, leakage risks, and data quality before training.
---

# Dataset auditing

## Input contract
Ask the workflow to inspect data format, row/sample unit, input and target columns, subject/session grouping, coordinate units, media paths, licence and privacy conditions. If unknown, inventory first and do not train yet.

## Procedure
- Inventory extensions/counts/bytes; use streaming or bounded batches.
- Profile missingness, schema mismatch, label ranges, class imbalance, invalid/missing media, duplicates and timestamps as appropriate.
- Verify sample alignment: image/frame must match the label and timestamps; screen resolution, coordinate origin and scaling must be explicit.
- Identify participant/session/video/device groups and choose splits that match the desired generalisation claim.
- Preserve original data; write derived data to a versioned destination with transformation metadata.
- Keep raw media and identifying paths local. Report aggregate counts rather than row contents.

## Output
Data card, schema contract, audit report, exclusions, split plan, data version/hash, unresolved issues and go/no-go recommendation.

## Stop conditions
Unknown labels/units, unclear licence/consent, unresolved leakage, unaligned frame-label pairs, or unexplained data corruption.
