# Handoff Report — Explorer M3.2: Evaluation Metrics, Error Distributions & Operational Safety

**Document Path:** `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_2\handoff.md`  
**Date:** 2026-10-29  
**Agent:** `explorer_m3_2`  
**Parent Conversation ID:** `49d5375b-5d7a-4c9a-8432-b9df2f718d02`  
**Operating Contract:** `c:\Users\Voriganti\Downloads\INAV\AGENTS.md`  
**Handoff Type:** Hard (Task Complete)  

---

## 1. Observation

Direct investigation of the repository source code, configuration files, skill guides, and safety architectures revealed the following concrete implementation parameters:

### 1.1 Existing Safety Filter Architecture (`backend/eyenav/safety.py`)
- **Multi-Layer Enforcement:** Lines 11–41 document a 6-layer command verification system.
- **Fail-Safe Policy:** Lines 43–45 establish: *"If the safety filter itself fails (exception), the CONSERVATIVE action is taken: command is BLOCKED. The system fails SAFE."* Lines 160–170 catch all unexpected exceptions and return `VerifiedCommand(blocked=True, block_reason=BlockReason.SAFETY_FILTER_ERROR)`.
- **Confidence Gating & Risk Levels:** Lines 369–382 define risk tiers:
  - `critical_risk`: `{"emergency_call"}`
  - `high_risk`: `{"delete", "submit", "send", "shutdown"}`
  - `medium_risk`: `{"select", "click", "enter", "back", "forward"}`
  - `low_risk`: all other commands (e.g. `scroll_up`, `scroll_down`).
  Lines 384–405 compute adaptive thresholds starting from base thresholds in `config.py` (low: 0.85, medium: 0.92, high: 0.97, critical: 0.99) with $+0.05$ context penalties during reading/searching noise.
- **Dwell Time Constraints:** Lines 424–429 mandate dwell durations:
  - Medium risk: $600\text{ ms}$
  - High risk: $1,200\text{ ms}$
  - Critical risk: $2,000\text{ ms}$
- **Anti-Pattern Gate:** Lines 328–347 compute normalized Shannon entropy over intent probabilities; any prediction with normalized entropy $> 0.60$ is blocked with `BlockReason.ANTI_PATTERN`.
- **Context Validation:** Lines 277–296 block navigation/action commands if reading probability $> 0.30$ or searching probability $> 0.30$ (`BlockReason.CONTEXT_MISMATCH`).
- **Emergency Stop:** Lines 38–40 and 172–184 implement Layer 6 emergency stop triggered by 3-second continuous eye closure, keyboard shortcut, or manual trigger.

### 1.2 Cursor Controller & Deadzones (`backend/eyenav/cursor/controller.py`)
- **Fixation Deadzone Gravity Well:** Line 54 defines `_FIXATION_DEADZONE_PX = 45.0`. Lines 184–201 enforce that when the gaze state is fixation, the cursor is anchored to the fixation centroid unless the eye deliberately departs by $> 45.0\text{ px}$.
- **Physical Mouse Override Guard:** Lines 52–53 define `_PHYSICAL_OVERRIDE_PX = 15` and `_PHYSICAL_PAUSE_S = 2.0`. Lines 143–155 detect if the physical mouse moves $> 15\text{ px}$ from the last commanded position and pauses gaze tracking for $2.0\text{ seconds}$.
- **Double-Blink Click Gesture:** Lines 50–51 define `_DOUBLE_BLINK_WINDOW_S = 0.6` and `_CLICK_COOLDOWN_S = 1.0`. Lines 248–273 execute `pyautogui.click()` only on confirmed double-blinks within $0.6\text{ s}$ and outside the $1.0\text{ s}$ cooldown.
- **FailSafe Configuration:** Lines 45–46 configure `pyautogui.FAILSAFE = True` and `pyautogui.PAUSE = 0.0`.
- **Filtering & Lag Compensation:** Lines 88–96 instantiate `OneEuroFilter(min_cutoff=0.05, beta=0.001)` and `LagCompensationPredictor(prediction_horizon_ms=45.0)`.

### 1.3 Intent Engine Model Specifications (`backend/eyenav/intent.py`)
- **13 Intent Classes:** Lines 52–66 define `INTENT_CLASSES`: `idle`, `reading`, `selecting`, `scrolling_up`, `scrolling_down`, `searching`, `activation`, `deactivation`, `confirmation`, `cancellation`, `nav_back`, `nav_forward`, `nav_home`.
- **Command Mapping:** Lines 69–83 map intents to system actions (`selecting` $\to$ `select`, `confirmation` $\to$ `enter`, `cancellation` $\to$ `escape`, etc.).
- **Latency Target:** Line 24 and Line 120 establish the inference latency budget of $\le 8\text{ ms}$ on CPU for the Tiny Temporal Transformer over 45 frames $\times$ 32 dimensions.

### 1.4 Gaze Model & Latency Targets (`backend/eyenav/vision/gaze.py`)
- **Model:** L2CS-Net with MobileNetV3-Large backbone (lines 5–20).
- **Latency Budget:** Line 31 specifies $\le 6\text{ ms}$ on Intel Core i5-8250U without GPU.
- **Accuracy Targets:** Lines 28–30 establish target $\text{MAE} \le 3^\circ$ uncalibrated and $\le 1^\circ$ after calibration.

### 1.5 Dataset & Partition Structure (`docs/data/DATASET_CARD.md`, `explorer_survey_3/handoff.md`)
- `archive.zip` contains 263 subjects, 348,643 frames, and 2,362 JSON files.
- Partitioning: Train split = 230 subjects (289,591 frames), Val split = 7 subjects (13,340 frames), Test split = 26 subjects (46,438 frames).

---

## 2. Logic Chain

1. **Premise 1 (Policy against single composite scores):** `AGENTS.md` and `docs/ml/METRICS_POLICY.md` strictly prohibit ranking or releasing ML models based on a single "accuracy" or mean error headline number.
2. **Premise 2 (Heavy-tailed distribution of gaze errors):** Oculomotor saccades, blinks, and head turns produce heavy-tailed error distributions where the arithmetic mean is skewed by a small percentage of extreme outliers.
3. **Deduction 1 (Distributional reporting suite):** Continuous screen regression evaluation cannot be satisfied by MAE alone. The suite must report:
   - Median ($P50$) for typical user experience.
   - Mean for historical baseline comparison.
   - 90th percentile ($P90$) and 95th percentile ($P95$) for tail excursion boundaries.
   - Maximum error for worst-case tracking spikes.
   - Component $MAE_x$ and $MAE_y$ to expose vertical eyelid droop vs horizontal tracking anisotropy.
4. **Premise 3 (Discrete UI interaction semantics):** Accessibility navigation involves clicking buttons of finite size. Under Fitts' Law, target acquisition depends on falling within target radii. In `controller.py`, `_FIXATION_DEADZONE_PX = 45.0` establishes an active 45px gravitational capture radius.
5. **Deduction 2 (Target Hit Rate thresholds):** Predeclared hit rates are essential:
   - $Hit@25\text{px}$: Fine UI targets (small icons, window controls, 24–32px).
   - $Hit@50\text{px}$: Standard accessible targets (toolbar buttons, 48–64px).
   - $Hit@100\text{px}$: Coarse navigation blocks (on-screen keyboard keys, 96–128px).
6. **Premise 4 (Cross-display and angular comparability):** Screen resolutions vary between phones, tablets, and desktop displays (e.g., iPhone 568×320 vs 1080p desktop 1920×1080).
7. **Deduction 3 (Normalized diagonal & visual angle):**
   - Distance error must be normalized by screen diagonal ($e_{\text{diag}} = e_i / \sqrt{W^2 + H^2}$).
   - Visual angle error $\theta_{\text{deg}} = \arctan(d_{\text{cm}} / D) \times (180 / \pi)$ (at standard $D = 60\text{ cm}$) must be reported to bridge computer vision benchmarks with physical screen pixels ($1.0^\circ \approx 37.8\text{ px}$ on a 24" 1080p monitor).
8. **Premise 5 (Extreme class imbalance in intent):** Passive states (`idle`, `reading`, `searching`) account for $>88\%$ of interaction time, while active gestures (`selecting`, `activation`) account for $<2\%$. Accidental execution of a high-risk command (`delete`, `enter`, `select`) has catastrophic consequences compared to a recoverable missed intent.
9. **Deduction 4 (Classification & temporal metrics):**
   - Overall raw accuracy is banned; Macro-F1 and Balanced Accuracy are mandatory.
   - Per-class Precision, Recall, and F1-score must be accompanied by support and confusion matrices highlighting critical danger zones ($M_{\text{reading}, \text{selecting}} \le 0.1\%$).
   - Operational event metrics must measure dwell latency ($650\text{ ms} \pm 50\text{ ms}$) and false trigger rates ($< 1.0$ false command per hour of continuous reading).
10. **Premise 6 (Real-time responsiveness & safety latency):** To maintain sustained $30\text{ FPS}$, the end-to-end processing deadline is $33.3\text{ ms}$.
11. **Deduction 5 (Pipeline budget & operational thresholds):**
    - Latency budget is set to $\le 20.0\text{ ms}$ (leaving $13.3\text{ ms}$ headroom margin): Capture (5ms), FaceLandmarker (6ms), Gaze/Mapper (4ms), Intent (3ms), Safety/Filter (1ms), Actuation (1ms).
    - Frames older than $50\text{ ms}$ are declared stale and dropped.
    - Cursor jumps $> 250\text{ px/frame}$ outside saccades are clamped as anomalous jumps ($\text{AJR} \le 0.05\%$).
    - On tracking loss, cursor position freezes and clicks are inhibited (`fail-closed`).
12. **Premise 7 (Zero data leakage):** Grouped test partition contains 26 unseen subjects ($46,438$ frames).
13. **Deduction 6 (Statistical significance):** Model superiority must be established via non-parametric Wilcoxon signed-rank tests across per-subject medians ($p < 0.01$), 10,000-sample bootstrap 95% confidence intervals, and disaggregated slice analysis (orientation, device, eccentricity).

---

## 3. Caveats

1. **Hardware Specificity of Latency Budgets:** The $\le 20.0\text{ ms}$ pipeline latency budget is established on reference hardware (Intel Core i5 quad-core CPU, 1.6 GHz base). Platforms with single-threaded bottlenecks or thermal throttling may observe higher latencies requiring adaptive model down-scaling (e.g. fewer Transformer layers or MobileNetV3 width multipliers).
2. **Viewing Distance Assumptions in Angular Conversions:** Angular error calculations assume a nominal viewing distance of $D = 60.0\text{ cm}$ and reference 24-inch 1080p desktop geometry. If a user sits closer ($40\text{ cm}$) or farther ($80\text{ cm}$), the angular error corresponding to a given pixel displacement scales proportionally.
3. **No Direct Code Modifications in Source Tree:** In accordance with the Explorer archetype and Milestone 3 read-only investigation mandate, all specifications are written to `.agents/teamwork/explorer_m3_2/analysis.md` and this handoff. Downstream implementation into `docs/ml/ML_PROBLEM_DEFINITION.md` and test harnesses will be carried out by designated milestone workers.

---

## 4. Conclusion

1. **Comprehensive Regression Suite Formulated:** Defined exact mathematical equations for Screen Euclidean Distance Error (1080p reference and native pixels), Normalized Diagonal Error, Component $MAE_x / MAE_y$, Median (P50), Mean, P90, P95, Max Error, and Target Hit Rates ($Hit@25\text{px}, Hit@50\text{px}, Hit@100\text{px}$). Visual angle conversion formulas link physical gaze angle ($1.0^\circ \approx 37.8\text{ px}$ at 60cm) to screen coordinates.
2. **Classification & Event Detection Framework Defined:** Prohibited misleading overall accuracy; established Macro-F1, Balanced Accuracy, per-class Precision/Recall/F1, and confusion matrix analysis with an asymmetric cost matrix penalizing accidental clicks during reading. Mandated temporal event alignment ($\pm 200\text{ ms}$ matching window) and operational false trigger rates ($< 1.0\text{ event / hour}$ for high-risk commands).
3. **Operational Failure Modes & Safety Criteria Established:** Formulated strict rules for gaze tracking loss (freeze cursor, inhibit clicks, reset filters on reacquisition), sudden cursor jump suppression ($> 250\text{ px/frame}$ anomalous jump clamp), stale frame handling ($> 50\text{ ms}$ discarded), end-to-end latency budget ($\le 20.0\text{ ms}$ per frame to guarantee $\ge 30\text{ FPS}$), and 4 independent emergency stop mechanisms.
4. **Statistical Significance Testing Specified:** Specified subject-macro averaging across the 26 unseen test subjects, Wilcoxon signed-rank paired testing ($p < 0.01$), 10,000-sample bootstrap confidence intervals, and slice-based disaggregation across device orientations, devices, and gaze eccentricity.
5. **Artifacts Ready:** All specifications, tables, equations, and checklists have been compiled into `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_2\analysis.md`.

---

## 5. Verification Method

### 5.1 Document & File Inspection
Inspect the generated specifications and verify against repository code:
1. View analysis document:
   `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_2\analysis.md`
2. Verify alignment with `SafetyFilter` implementation:
   `c:\Users\Voriganti\Downloads\INAV\backend\eyenav\safety.py` (lines 11–49, 133–170, 214–348, 369–429)
3. Verify alignment with `GazeCursorController` implementation:
   `c:\Users\Voriganti\Downloads\INAV\backend\eyenav\cursor\controller.py` (lines 45–55, 88–96, 143–155, 184–201, 248–273)
4. Verify alignment with configuration thresholds:
   `c:\Users\Voriganti\Downloads\INAV\backend\eyenav\config.py` (lines 37–89)
5. Verify compliance with operating contract:
   `c:\Users\Voriganti\Downloads\INAV\AGENTS.md`
   `c:\Users\Voriganti\Downloads\INAV\docs\ml\METRICS_POLICY.md`

### 5.2 Verification Commands
To test the existing test suites and verify that the current baseline tests pass without error:
```bash
# 1. Run safety filter tests
pytest tests/test_safety_filter.py -v

# 2. Run cursor controller tests
pytest tests/test_cursor_controller.py -v

# 3. Run intent engine tests
pytest tests/test_intent_engine.py -v

# 4. Run full test suite with synthetic/mocked cursor
pytest tests/ -v
```

### 5.3 Invalidation Conditions
This evaluation specification will be invalidated if:
1. IntuiGaze transitions from an absolute screen-coordinate navigation model to a pure relative head-joystick or eye-joystick model.
2. The operating system interface changes to discard discrete widget targets in favor of a continuous trajectory tracking task.
3. The underlying dataset partitioning is changed from subject-grouped splits to random frame shuffling (violating leakage constraints).
