---
name: test-quality
description: Build and run the right checks for IntuiGaze changes, including deterministic tests, static checks, integration boundaries, and optional hardware tests.
---

# Test quality

- Inspect existing test conventions and marker definitions first.
- Unit-test coordinate transforms, smoothing, validation/filtering, calibration math and intent state machines with synthetic fixtures.
- Include boundary and failure cases, not just happy paths.
- Mock camera, clock, filesystem where appropriate, and OS cursor APIs.
- Keep hardware/GPU/camera/slow suites explicitly marked and never run actuation by default.
- Run focused tests first, then the full suite, linter and type checks available in the repository.
- Report command exit codes and environment failures exactly; don't say “passed” when a test was skipped or not run.
