# Workflow: implement a non-ML feature or refactor

1. Inspect existing interfaces and tests; determine whether the feature belongs in vision extraction, calibration, mapping, intent, smoothing, or actuation.
2. Define observable acceptance criteria and safety implications before editing.
3. Keep code changes local to one layer where possible; avoid mixing model changes with OS cursor-control changes in one patch.
4. Add deterministic unit tests with synthetic inputs. Mock the camera and cursor backend; do not produce real clicks in tests.
5. Add failure-path tests: missing/invalid landmarks, low confidence, stale data, camera loss, invalid calibration, out-of-bounds coordinates, and emergency stop where applicable.
6. Update public docs/config examples and preserve backward compatibility where possible.
7. Run focused tests, complete test suite, lint/type checks supported by the repo, and a manual dry-run if relevant.
8. Summarise behaviour change, safety review, test evidence, and limitations.
