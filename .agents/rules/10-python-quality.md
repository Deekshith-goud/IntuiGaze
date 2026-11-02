# Python quality rules

- Inspect `pyproject.toml`, `requirements*.txt`, and nearby modules before changing packaging, runtime versions, lint rules, or dependency versions.
- Use the project's supported Python runtime; do not upgrade it to match a local tool preference without compatibility evidence.
- Keep functions focused, make state transitions explicit, and use type hints consistent with adjacent code.
- Prefer small testable functions around vision features, model mapping, intent detection, calibration state, and cursor actuation.
- Use deterministic random seeds for experiments and tests when supported. Tests must not require internet, camera access, GUI interaction, or GPU unless explicitly marked.
- Keep expensive model training out of unit tests. Test data contracts and small synthetic fixtures; run full training as an explicit experiment.
- Avoid broad exception swallowing, silent fallback behavior, hard-coded machine-specific paths, and hidden downloads of model weights.
- Keep lint configuration meaningful. Do not suppress a finding globally to make one file pass; use narrow, explained exceptions when unavoidable.
- Dependencies must be justified, pinned or bounded according to existing policy, and checked for licence/platform compatibility before adding.
