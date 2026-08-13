# EyeNav — Safety System Design

**Document Version:** 1.0  
**Status:** Approved — Safety Critical  
**Owner:** Safety Engineering Team  
**Last Updated:** 2024-Q4  
**Classification:** Internal — Safety Critical Document  

---

## 1. Why Safety Is the #1 Priority

In any eye navigation system, **false positive commands are the primary failure mode**.

A false positive occurs when the system executes a command the user did not intend.

### Consequences of False Positives

| Scenario | Consequence | Severity |
|---|---|---|
| Accidental "Delete" during document editing | Data loss | Critical |
| Accidental "Back" during form fill | Lost data | High |
| Accidental "Select" on wrong UI element | Navigation error | Medium |
| Accidental command during reading | Interruption | Low |
| Accidental "Emergency services" call (future) | Safety risk | Critical |
| Accidental financial transaction | Financial harm | Critical |

For accessibility users who rely on EyeNav as their **only** interaction method, accidental commands have no undo path available through eye navigation — they must rely on a caregiver or cannot recover at all.

**False positive rate target: ≤ 0.1% per session**  
(At 100 intentional actions per hour, this means ≤ 0.1 accidental actions per hour — i.e., 1 per 10 hours of use)

---

## 2. Safety Architecture (Multi-Layer)

The safety system is designed in 6 independent layers. A command must pass ALL layers to execute.

```
Intent Prediction
        │
        ▼
┌───────────────────────────────────────┐
│  Layer 1: Confidence Threshold Gate   │ ← Block if confidence < threshold
└───────────────────────────────────────┘
        │ (pass)
        ▼
┌───────────────────────────────────────┐
│  Layer 2: Cooldown / Rate Limiter     │ ← Block if same command too recent
└───────────────────────────────────────┘
        │ (pass)
        ▼
┌───────────────────────────────────────┐
│  Layer 3: Context Validation          │ ← Block if context mismatch
└───────────────────────────────────────┘
        │ (pass)
        ▼
┌───────────────────────────────────────┐
│  Layer 4: Dwell Confirmation          │ ← Require dwell for high-risk cmds
└───────────────────────────────────────┘
        │ (pass)
        ▼
┌───────────────────────────────────────┐
│  Layer 5: Anti-Pattern Detection      │ ← Block known false-trigger patterns
└───────────────────────────────────────┘
        │ (pass)
        ▼
┌───────────────────────────────────────┐
│  Layer 6: Emergency Stop Check        │ ← Block ALL if emergency stop active
└───────────────────────────────────────┘
        │ (pass)
        ▼
   Command Executed
```

---

## 3. Layer 1 — Confidence Threshold Gate

### Design

Each intent prediction comes with a confidence score `c ∈ [0, 1]`.

A command executes only if `c ≥ θ`, where `θ` is the confidence threshold.

### Threshold Configuration

| Risk Level | Default θ | Configurable Range | Examples |
|---|---|---|---|
| Low risk | 0.85 | 0.70–0.95 | Scroll, cursor move |
| Medium risk | 0.92 | 0.85–0.99 | Select, click |
| High risk | 0.97 | 0.95–0.99 | Delete, send, submit |
| Critical risk | 0.99 | 0.99 only | Close app, shutdown |

### Adaptive Thresholds

The threshold automatically increases in conditions that increase false positive risk:
- **Eye fatigue detected**: `θ += 0.03`
- **Low-light camera conditions**: `θ += 0.02`
- **High saccade rate (user scanning)**: `θ += 0.04`
- **Post-blink settling period (100ms)**: `θ += 0.05`

### Implementation

```python
def confidence_gate(prediction: IntentPrediction, context: Context) -> bool:
    """
    Layer 1: Confidence threshold gate.
    
    Returns True if the prediction passes the confidence threshold.
    
    This is a safety-critical function. Do not modify without safety review.
    """
    base_threshold = config.thresholds[prediction.risk_level]
    adaptive_adjustment = compute_adaptive_adjustment(context)
    effective_threshold = min(0.99, base_threshold + adaptive_adjustment)
    
    return prediction.confidence >= effective_threshold
```

---

## 4. Layer 2 — Cooldown / Rate Limiter

### Design

After a command executes, the same command is blocked for a minimum cooldown period.

### Cooldown Table

| Command | Cooldown | Reason |
|---|---|---|
| Scroll Up/Down | 300ms | Natural repeated use |
| Select/Click | 800ms | Prevents double-click false positives |
| Back/Forward | 1200ms | Higher risk |
| Delete | 2000ms | Irreversible |
| Enter/Submit | 1500ms | Irreversible |
| Menu Open | 600ms | |
| Emergency Stop | N/A — disables all | |

### Inter-Command Suppression

In addition to same-command cooldown, there is a global inter-command minimum spacing of 200ms to prevent rapid fire from any source.

---

## 5. Layer 3 — Context Validation

### Design

Commands are validated against the current application context. A scroll command while a dialog box is active is suspicious.

### Context Rules (Examples)

```yaml
context_rules:
  - when: "active_window_type == modal_dialog"
    block_commands: [scroll_up, scroll_down, back, forward]
    reason: "Scrolling in modal dialogs is high-ambiguity"
    
  - when: "gaze_velocity > 200 deg/sec"
    block_commands: [select, click, enter]
    reason: "High saccade velocity = scanning, not selecting"
    
  - when: "reading_intent_probability > 0.7"
    block_commands: [all except idle]
    reason: "User is reading — suppress all commands"
    
  - when: "blink_rate > 20 per minute"
    escalate_threshold: 0.03
    reason: "High blink rate = fatigue or distress"
```

---

## 6. Layer 4 — Dwell Confirmation

### Design

High-risk commands require the user to maintain gaze (dwell) on the target for a defined period before execution.

This prevents commands triggered by accidental gaze landing on a button.

### Dwell Parameters

| Command Risk | Dwell Time | Visual Feedback |
|---|---|---|
| Low | None | None |
| Medium | 600ms | Progress ring |
| High | 1200ms | Progress ring + audio cue |
| Critical | 2000ms | Full confirmation dialog |

### Visual Feedback Design

During dwell, a circular progress indicator appears around the gaze target:
- 0%: No indicator
- 25%: Quarter arc
- 50%: Half arc (+ color shift toward green)
- 75%: Three-quarter arc
- 100%: Command executes (brief flash confirmation)

If gaze breaks during dwell, the progress resets to 0% immediately.

The animation is designed to provide clear feedback without being distracting:
- Located at gaze position, not at screen edge
- Transparent background (does not obscure content)
- Accessible: described by screen reader on execution

---

## 7. Layer 5 — Anti-Pattern Detection

### Design

Certain gaze patterns are known to be involuntary or ambiguous. These are detected and used to suppress commands.

### Known False-Trigger Patterns

| Pattern | Description | Response |
|---|---|---|
| Post-saccadic suppression | 50–100ms after a large saccade, fixation is unstable | Block selection for 100ms post-saccade |
| Blink-end overshooting | Eye reopening after blink causes momentary overshooting | Block 80ms after blink open |
| Reading saccade | Rapid small saccades across text lines | Suppress all non-reading intents |
| Microsaccade burst | High-frequency tiny fixation corrections | Increase threshold temporarily |
| Optokinetic nystagmus | Involuntary eye movement from scrolling content | Suppress commands during active scroll |
| Photophobia blink | Rapid multiple blinks from glare | Do not interpret as blink commands |

### Detection Algorithm

```python
class AntiPatternDetector:
    """
    Detects known false-trigger gaze patterns to prevent accidental commands.
    
    This is a rule-based system (not ML) for maximum reliability and
    interpretability.
    """
    
    def detect_reading_saccade(self, gaze_history: np.ndarray) -> bool:
        """
        Detects reading pattern (horizontal saccades < 1° amplitude, 
        leftward return saccades).
        Returns True if reading pattern detected.
        """
        ...
    
    def detect_post_saccadic_instability(self, gaze_history: np.ndarray) -> bool:
        """
        Detects post-saccadic instability window (50-150ms after large saccade).
        """
        ...
    
    def detect_blink_artifact(self, ear_history: np.ndarray) -> bool:
        """
        Detects 80ms post-blink artifact window.
        """
        ...
```

---

## 8. Layer 6 — Emergency Stop

### Design

A dedicated emergency stop mechanism disables ALL command execution.

### Activation

| Trigger | Threshold | Notes |
|---|---|---|
| Sustained eye closure | > 3 seconds | Disables all commands |
| Repeated rejection | User explicitly cancels 3 times | Disables for 30 seconds |
| Manual keyboard override | Win+F9 (configurable) | Instant disable |
| Voice override (optional) | "Stop eye nav" | For multi-modal users |

### Deactivation

| Method | Recovery |
| Eye reopen | 500ms gaze confirmation to re-enable |
| Specific gesture | User-defined re-activation gesture |
| Timeout | 60 seconds (configurable, auto re-enable) |
| Keyboard | Same key as activation |

### Emergency Stop State Machine

```
ACTIVE
  │ (3s eye closure)
  ▼
EMERGENCY_STOP
  │ (eye reopen + 500ms confirmation gaze)
  │ OR (60s timeout)
  │ OR (keyboard override)
  ▼
ACTIVE
```

---

## 9. Fatigue Monitoring

EyeNav continuously monitors for signs of user fatigue:

### Fatigue Indicators

| Signal | Normal Range | Fatigue Threshold | Action |
|---|---|---|---|
| Blink rate | 12–20 per minute | > 25 or < 8 | Increase threshold |
| EAR mean | 0.30–0.40 | < 0.22 | Increase threshold + alert |
| Saccade amplitude | Varies | Reduced by 20%+ | Increase threshold |
| Session duration | — | > 2 hours | Recommend break |
| Gaze drift rate | < 0.5° per minute | > 2° per minute | Recalibration needed |

### Fatigue Response Protocol

1. **Level 1 (Early)**: Increase all thresholds by 5%, show subtle indicator
2. **Level 2 (Moderate)**: Increase by 10%, show break recommendation
3. **Level 3 (Severe)**: Increase by 20%, mandate 5-minute break for non-medical users
4. **Level 4 (Critical)**: Disable command execution, require manual restart

---

## 10. Audit and Logging

Every command execution and every block event is logged (privacy-safe):

```json
{
  "event_type": "command_executed",
  "timestamp": 1700000000.123,
  "execution_id": "a1b2c3d4-...",
  "command": "scroll_down",
  "intent": "scrolling",
  "confidence": 0.94,
  "layers_passed": ["confidence", "cooldown", "context", "anti_pattern", "emergency_stop"],
  "gaze_data": null,
  "session_id": "hashed-session-id"
}
```

Note: `gaze_data` is always null in logs — raw gaze is never persisted.

---

## 11. Safety Test Cases

### Mandatory Test Suite

```
T-SAFE-001: Single blink does not trigger command (30fps, 100 trials)
T-SAFE-002: Reading text does not trigger scroll (10 minutes, 3 texts)
T-SAFE-003: Involuntary blink does not trigger (photophobia simulation)
T-SAFE-004: High saccade rate does not trigger select
T-SAFE-005: 3-second eye closure triggers emergency stop
T-SAFE-006: Emergency stop blocks all commands
T-SAFE-007: Post-fatigue false positive rate within spec
T-SAFE-008: Glasses do not cause systematic false positives
T-SAFE-009: Rapid head movement does not cause false selection
T-SAFE-010: Dark environment does not cause false positives
```

---

## 12. Failure Mode Analysis

| Failure | Probability | Effect | Mitigation |
|---|---|---|---|
| Confidence model calibration drift | Medium | FP rate increase | Continuous monitoring; recalibration prompt |
| EAR threshold mismatch (new glasses) | High | Blink FP | Per-session EAR calibration |
| Camera lighting change | High | Gaze drift | Lighting change detection; threshold increase |
| Model adversarial input | Low | Unpredictable | Input validation; anomaly detection |
| Safety layer code bug | Low | Critical | Formal verification of safety layer logic |
| OS integration failure | Medium | Command drop | Fallback mode; user notification |

---

## References

1. Soukupová, T., & Čech, J. (2016). Real-time Eye Blink Detection using Facial Landmarks.
2. Rayner, K. (1998). Eye Movements in Reading and Information Processing. *Psychological Bulletin*.
3. Engbert, R., & Kliegl, R. (2003). Microsaccades Uncover the Orientation of Covert Attention. *Vision Research*.
4. Jacob, R.J.K. (1990). What You Look At Is What You Get: Eye Movement-Based Interaction Techniques. *CHI 1990*.
5. Majaranta, P., et al. (2009). Fast Gaze Typing with an Adjustable Dwell Time. *CHI 2009*.
