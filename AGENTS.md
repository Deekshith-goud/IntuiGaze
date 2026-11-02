# IntuiGaze — Agent Operating Contract

## Mission
Improve IntuiGaze, an experimental gaze-controlled computer-navigation project, without compromising user control, privacy, scientific validity, or the existing working baseline.

## Before changing code
1. Inspect the relevant source, tests, configuration, and recent local changes. Never infer the actual implementation from README text alone.
2. Read this file and the applicable `.agent/rules/` files. Use the relevant workflow in `.agent/workflows/` for multi-step work.
3. Identify the smallest change that solves the task. State assumptions, files to change, failure modes, and verification plan before broad refactors.
4. Preserve the current architecture unless measurements or tests justify changing it. Avoid unrelated renaming and dependency churn.

## Engineering requirements
- Follow the repository's established Python version, import layout, naming, type, lint, and test conventions after verifying them.
- Add or update tests for behavior changes. Prefer deterministic unit tests; gate camera, GPU, desktop mouse, and long-running tests behind explicit markers or flags.
- Never claim tests passed unless you ran them; distinguish failures caused by the patch from existing/environment failures.
- Never change thresholds, filters, dwell timings, calibration behavior, or cursor acceleration merely to make a demo look smoother without a measured evaluation and a documented reason.
- Do not run code that controls the actual mouse or clicks on the desktop during automated tests. Use mock/stub cursor adapters and dry-run mode.

## ML/data requirements
- Treat dataset schema, labels, subject identifiers, licences, collection consent, and intended deployment as unknown until inspected.
- Keep raw data and private derived data outside Git; never upload it to an API or third-party service unless explicitly authorised.
- For large data, prefer streaming/sharding, metadata-first inspection, reproducible manifests, and disk-backed indexes over loading all data into memory.
- Establish train/validation/test partitions before fitting transforms or selecting features. Split by participant/session/device as appropriate to the generalisation claim. Keep the final test set sealed until model-selection decisions are complete.
- Use a simple, honest baseline before a complex model. Store configuration, data manifest/hash, split definition, random seed, code revision, metrics, and artifact path for each run.
- Match metrics to the target: gaze coordinates/direction are regression; blink/dwell/intent are classification or event detection. Report error distributions and operational failure rates, not one headline number.
- Do not fabricate dataset size, scores, thresholds, citations, model lineage, or completed audit results.

## Safety, privacy, and access
- Mouse control must be opt-in, visibly active, interruptible, and disabled by default in tests. Keep an independent physical escape gesture/edge failsafe and test it separately.
- Low-confidence or stale gaze estimates must fail safely: no click, no abrupt cursor jump, and a clear recovery path.
- Store face/gaze traces and calibration profiles locally by default. Minimise retention and avoid logging raw frames, eye crops, identifiers, or coordinates tied to a person unless required and documented.
- Never weaken the emergency stop, confidence gate, or click guard as an incidental fix.

## Finish criteria
A task is complete only when implementation, relevant tests, lint/type checks (where available), documentation, and a concise report agree. Report changed files, commands run, results, known limitations, and follow-up risks. If no tests were run, say so plainly.
