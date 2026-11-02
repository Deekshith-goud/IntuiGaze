---
name: cursor-safety-review
description: Review any change that can affect mouse movement, click intent, live computer control, camera failure, confidence thresholds, or emergency-stop behavior.
---

# Cursor safety review

- Verify explicit opt-in and visible active state.
- Verify independent emergency stop/escape route and no-actuation test mode.
- Test stale/invalid/low-confidence outputs, sudden prediction jumps, face/landmark loss, invalid calibration and exceptions.
- Ensure uncertain intent fails closed: no click.
- Test with a mocked cursor adapter; never click/type on the user's real desktop in automated tests.
- Review raw-frame/gaze logging and data retention.
- Check that smoother motion does not hide delayed control, and thresholds are justified by evaluation.

Output a checklist with test evidence and any release blockers. Any broken failsafe is a hard blocker regardless of aggregate model score.
