# Cursor actuation, user control, and privacy

- Real mouse actuation is an integration boundary. Default all automated tests, data processing, demonstrations, and model evaluation to no-actuation/dry-run mode.
- Require deliberate opt-in before enabling live cursor control. Make active state visible and provide an immediate emergency stop that is independent of the gaze model.
- Retain and test the repository's existing corner/escape failsafe. Any proposed replacement must be independently validated before the old path is removed.
- Filter invalid, stale, low-confidence, out-of-range, and discontinuous predictions before mapping them to cursor movement. Fail closed for click actions.
- Separate gaze estimation, intent detection, cursor smoothing, and OS-level actuation behind clear interfaces so each can be tested independently.
- A false positive click is a safety/interaction failure, not a minor average-metric issue. Report false activations per unit time and test the click guard under uncertainty.
- Do not log or transmit raw camera frames, crops, gaze traces, or participant identifiers by default. Prefer aggregate, de-identified diagnostics and configurable local retention.
- Never run an automated integration test that clicks, types, deletes, or changes the active user's desktop state.
- Document camera requirements, data processing, persistence, known limitations, and controls before distributing a build.
