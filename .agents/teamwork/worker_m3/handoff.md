# Handoff Report — Worker M3: ML Problem Definition Specification

**Agent:** `worker_m3`  
**Milestone:** Milestone 3: ML Problem Definition Specification (Step 9)  
**Parent Conversation ID:** `49d5375b-5d7a-4c9a-8432-b9df2f718d02`  
**Deliverable Path:** `c:\Users\Voriganti\Downloads\INAV\docs\ml\ML_PROBLEM_DEFINITION.md`  
**Working Directory:** `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\worker_m3\`  
**Date:** 2026-10-29  
**Handoff Type:** Hard (Task Complete)  

---

## 1. Observation

1. **Prior Missing Specification Artifact**:
   - At the inception of Milestone 3, `find_by_name` on `c:\Users\Voriganti\Downloads\INAV\docs\ml` confirmed that `docs/ml/ML_PROBLEM_DEFINITION.md` was absent.
   - Explorers M3.1, M3.2, and M3.3 produced three detailed technical analyses:
     * `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_1\analysis.md` (Formulation, coordinate systems, loss functions, secondary tasks, multimodal input space, latency budget).
     * `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_2\analysis.md` (Continuous regression metrics, hit rates, angular error, intent metrics, operational safety, statistical significance testing, 8-point promotion gate).
     * `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_3\analysis.md` (Levels 0–3 baseline hierarchy, 230/7/26 participant split, zero-leakage invariant, archive in-memory streaming extraction, 4-point data filtering, ethics & privacy compliance).

2. **Repository Operating Invariants**:
   - `git diff backend/eyenav/cursor/controller.py docs/business/ETHICS.md` was inspected:
     * `backend/eyenav/cursor/controller.py` contains preserved uncommitted modifications implementing the fixation gravity well with `_FIXATION_DEADZONE_PX = 45.0` (lines 54, 116–120, 178–201), `_PHYSICAL_OVERRIDE_PX = 15` (line 52), `_PHYSICAL_PAUSE_S = 2.0` (line 53), and `_DOUBLE_BLINK_WINDOW_S = 0.6` (line 50).
     * `docs/business/ETHICS.md` contains the preserved uncommitted header change (`Last Updated: 2026-Q4`, line 6).
     * `archive.zip` (21,616,790,160 bytes, SHA-256 `48d2175ad792f82c2cea7df4d5763c4dc2bb781c3133c32b668ace251814d2c7`) is intact at repository root.
     * `face_landmarker.task` is intact at repository root.

3. **Created Specification Artifact**:
   - Authored `c:\Users\Voriganti\Downloads\INAV\docs\ml\ML_PROBLEM_DEFINITION.md` (883 lines, 72,309 bytes).
   - The document unifies all requirements from the dispatch prompt, operating contracts (`AGENTS.md`, `METRICS_POLICY.md`, `ETHICS.md`), and the three explorer reports into a comprehensive, publication-grade engineering standard.

---

## 2. Logic Chain

1. **Unification of Primary Task & Bounding Policy**:
   - *Observation:* Explorer M3.1 established that mobile devices in MIT GazeCapture record varying screen resolutions and aspect ratios across orientations 1–4.
   - *Reasoning:* Normalizing target screen coordinates by active dimensions yields canonical compact space $\mathcal{Y} = [0, 1]^2$, enabling cross-device generalization.
   - *Deduction:* Enforcing bounded output activations (such as Sigmoid) induces the "vanishing edge gradient" problem ($\lim_{z\to\pm\infty}\sigma'(z) = 0$), causing the cursor to resist reaching screen bezels and corners where UI controls reside.
   - *Resolution in Spec:* Mandated unbounded linear regression logits $\hat{\mathbf{s}} = \mathbf{W}_o\mathbf{h} + \mathbf{b}_o$ with constant identity gradient $\mathbf{I}_2$, paired with a two-stage runtime post-processing guard: Stage 1 off-screen anomaly track loss detection ($\epsilon_{\text{guard}} = 0.25$) and Stage 2 deterministic clamping to $[0, 1]$.

2. **Hierarchical Loss Function Architecture**:
   - *Observation:* Saccadic jumps, natural eye blinks, and head turns produce heavy-tailed tracking errors. MSE quadratically amplifies these outliers, corrupting fine fixation learning.
   - *Reasoning:* Huber / Smooth L1 loss ($\delta = 0.02$, equivalent to $\sim 38\text{ px}$ on 1080p) transitions from quadratic to linear penalty, clamping outlier gradient magnitudes to $\pm \delta$.
   - *Refinement:* For fine UI widget clicking, sub-pixel fixation accuracy is paramount. Adaptive Wing (AWing) loss ($\omega = 0.05, \epsilon = 0.01$) introduces steep logarithmic gradients near zero ($\frac{\omega}{\epsilon} = 5.0$), driving sub-pixel micro-fixation accuracy and eliminating slow drift around buttons.
   - *Uncertainty & Multi-Task:* Pinball loss provides predictive quantile intervals to drive Layer 1 confidence gating; homoscedastic uncertainty weighting (Kendall et al.) automatically balances coordinate regression, 3D angular regression, and intent classification.

3. **Secondary Prediction Tasks & Real-Time Constraints**:
   - *Observation:* L2CS-Net in `backend/eyenav/vision/gaze.py` uses 90 classification bins over $\pm 45^\circ$ with continuous soft-argmax expectation and Shannon entropy confidence.
   - *Observation:* `backend/eyenav/intent.py` defines exactly 13 navigation intent classes evaluated over a $45\times 32$ temporal buffer. Because passive classes (`idle`, `reading`) dominate $>88\%$ of frames, standard cross-entropy collapses to an all-idle dummy.
   - *Resolution in Spec:* Mandated Multi-Class Focal Loss ($\gamma = 2.0$, $\alpha_c = 1/\sqrt{\text{Freq}(c)}$) for Task S2, and allocated a strict real-time CPU budget: $\le 6.0\text{ ms}$ model inference, $\le 10.0\text{ ms}$ total frame pipeline to sustain $\ge 30\text{ FPS}$ (targeting $60\text{ FPS}$).

4. **Evaluation Metrics, Safety Invariants & Operational Release Gates**:
   - *Observation:* Explorers M3.2 and M3.3 identified that aggregate accuracy masks catastrophic failure modes.
   - *Resolution in Spec:* Defined full error distribution percentiles (P50 Median, Mean, P90, P95, Max error), Component $MAE_x/MAE_y$, Target Hit Rates ($Hit@25\text{px}, Hit@50\text{px}, Hit@100\text{px}$ directly aligned with `_FIXATION_DEADZONE_PX = 45.0`), and angular conversion formulas ($D = 60.0\text{ cm}$).
   - *Operational Safety:* Formulated fail-closed tracking loss behavior, anomalous jump suppression ($> 250\text{ px/frame}$), stale frame handling ($> 50\text{ ms}$), physical mouse override priority ($15\text{ px}$ threshold pauses tracking for $2.0\text{ s}$), and the 8-point binary model promotion checklist.

5. **Dataset Partitioning, Archive Invariants & Baseline Hierarchy**:
   - *Observation:* Random train/test frame shuffling leaks facial morphology and lighting across splits, causing deceptive memorization.
   - *Resolution in Spec:* Formulated the Zero-Leakage Grouping Invariant on native MIT GazeCapture splits (230 train subjects / 7 val / 26 test). Mandated cryptographic test set sealing, in-memory streaming extraction of the 2,362 JSON metadata files from `archive.zip` (preserving the 20.13 GB file intact without disk decompression), 4-point data quality filtering, and a 4-tier Baseline Progression Hierarchy (Level 0 Dummy, Level 1 Polynomial Ridge, Level 2 RF/GBDT, Level 3 Deep CNN).

---

## 3. Caveats

1. **Hardware-Dependent Inference Latency**:
   - The $\le 6.0\text{ ms}$ inference and $\le 10.0\text{ ms}$ total pipeline budget is specified for a quad-core Intel Core i5-8250U / AMD Ryzen 5 CPU. Low-power single-threaded embedded CPUs may require model pruning or MobileNetV3 width reduction to maintain $\ge 30\text{ FPS}$.
2. **Nominal Desktop Viewing Distance**:
   - Visual angle error conversions assume a reference viewing distance of $D = 60.0\text{ cm}$ and a 24-inch 1080p display ($p = 0.2767\text{ mm}$). If user distance or screen geometry varies, the angular error scales proportionally.
3. **Downstream Execution Separation**:
   - Milestone 3 is strictly scoped to authoring the authoritative specification document `docs/ml/ML_PROBLEM_DEFINITION.md`. Dataset manifest generation (`scripts/audit_dataset.py`, `train_manifest.csv`, `test_manifest.csv`) will be executed in Milestone 4, and baseline model implementation will occur in Milestone 5.

---

## 4. Conclusion

1. **Milestone 3 Deliverable Fully Realized**:
   - Authored the authoritative specification `c:\Users\Voriganti\Downloads\INAV\docs\ml\ML_PROBLEM_DEFINITION.md` (883 lines).
   - Covers all 10 mandated sections with full mathematical rigor, complete LaTeX equations, ASCII architectural diagrams, parameter specifications, and code mappings.
2. **Absolute Preservation of Invariants**:
   - `backend/eyenav/cursor/controller.py` remains untouched.
   - `docs/business/ETHICS.md` remains untouched.
   - `archive.zip` (20.13 GB) remains intact at repository root.
   - `face_landmarker.task` remains intact at repository root.
   - Write ownership was strictly maintained (only `docs/ml/ML_PROBLEM_DEFINITION.md` and worker workspace modified).
3. **Downstream Readiness**:
   - The specification provides concrete schema definitions, filtering rules, and evaluation gates that directly unblock Milestone 4 (Dataset Pipeline & Manifest Generation) and Milestone 5 (Baseline Models & Evaluation Gates).

---

## 5. Verification Method

### 5.1 Document Verification
Inspect the authored deliverable and workspace tracking files:
1. `docs/ml/ML_PROBLEM_DEFINITION.md` (Lines 1–883)
2. `.agents/teamwork/worker_m3/DISPATCH.md`
3. `.agents/teamwork/worker_m3/BRIEFING.md`
4. `.agents/teamwork/worker_m3/progress.md`
5. `.agents/teamwork/worker_m3/handoff.md`

### 5.2 Invariant Verification
Verify that uncommitted modifications in invariant files remain untouched and intact:
- `backend/eyenav/cursor/controller.py`: Check lines 50–54 (`_FIXATION_DEADZONE_PX = 45.0`, `_PHYSICAL_OVERRIDE_PX = 15`, `_PHYSICAL_PAUSE_S = 2.0`, `_DOUBLE_BLINK_WINDOW_S = 0.6`) and lines 178–201 (gravity well implementation).
- `docs/business/ETHICS.md`: Check line 6 (`Last Updated: 2026-Q4`).
- `archive.zip`: Verify file size is `21,616,790,160` bytes and SHA-256 is `48d2175ad792f82c2cea7df4d5763c4dc2bb781c3133c32b668ace251814d2c7`.
- `face_landmarker.task`: Verify file presence at root.

### 5.3 Automated Verification Commands
When permitted by user policy:
```bash
# Verify intent engine tests
pytest tests/test_intent_engine.py -v

# Verify safety filter tests
pytest tests/test_safety_filter.py -v

# Verify cursor controller tests with mock adapter
pytest tests/test_cursor_controller.py -v

# Verify dataset audit script smoke test
pytest tests/test_audit_dataset_script.py -v
```

### 5.4 Invalidation Conditions
This specification will be invalidated if:
1. The project drops screen coordinate regression in favor of a pure head-joystick or relative velocity interface.
2. The team relaxes participant-group isolation and permits frame-shuffled training splits.
3. The intent class catalog in `backend/eyenav/intent.py` is altered from the 13 defined classes.
