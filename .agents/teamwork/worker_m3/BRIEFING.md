# BRIEFING — 2026-10-29T18:16:00Z

## Mission
Author the comprehensive, publication-grade specification document `docs/ml/ML_PROBLEM_DEFINITION.md` unifying synthesized findings from Explorers M3.1, M3.2, and M3.3.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\worker_m3
- Original parent: 49d5375b-5d7a-4c9a-8432-b9df2f718d02
- Milestone: Milestone 3: ML Problem Definition Specification

## 🔒 Key Constraints
- Exclusive write ownership: `docs/ml/ML_PROBLEM_DEFINITION.md` and `.agents/teamwork/worker_m3/`.
- DO NOT modify any other files in the repository.
- Preserve invariants:
  * `backend/eyenav/cursor/controller.py` MUST remain untouched.
  * `docs/business/ETHICS.md` MUST remain untouched.
  * `archive.zip` MUST remain intact at repository root.
  * `face_landmarker.task` MUST remain intact at repository root.
- MANDATORY INTEGRITY: No cheating, no hardcoding, genuine publication-grade specification.

## Current Parent
- Conversation ID: 49d5375b-5d7a-4c9a-8432-b9df2f718d02
- Updated: 2026-10-29T18:16:00Z

## Task Summary
- **What to build**: Author `docs/ml/ML_PROBLEM_DEFINITION.md` covering all 10 core sections unifying findings from Explorers M3.1, M3.2, and M3.3.
- **Success criteria**: Publication-grade mathematical rigor, complete LaTeX formulation, ASCII topology diagrams, exact alignment with repository code and operating contracts (`AGENTS.md`, `METRICS_POLICY.md`, `ETHICS.md`), all invariants preserved.
- **Interface contracts**: `docs/ml/METRICS_POLICY.md`, `docs/business/ETHICS.md`, `AGENTS.md`.

## Key Decisions Made
- Primary task formulated as continuous regression $f(X) \to (\hat{x}_{\text{norm}}, \hat{y}_{\text{norm}}) \in [0, 1]^2$.
- Sigmoid activation mathematically rejected due to asymptotic vanishing gradients at screen bezels ($\lim_{z\to\pm\infty}\partial\hat{y}/\partial z = 0$); adopted unbounded linear logits with two-stage post-processing guard ($\epsilon_{\text{guard}} = 0.25$ anomaly detection + $[0, 1]$ deterministic clamping).
- Loss functions specified: Huber/Smooth L1 ($\delta = 0.02$) and Adaptive Wing ($\omega = 0.05, \epsilon = 0.01$) over MSE; Pinball loss for uncertainty; homoscedastic uncertainty weighting for multi-task loss.
- Secondary tasks defined: S1 (3D gaze direction, L2CS-Net 90-bin soft-argmax, Shannon entropy confidence), S2 (13-class temporal intent over 45x32 buffer, Multi-Class Focal Loss with $\gamma = 2.0$).
- Multimodal input space specified: 5 modalities ($\mathbf{I}_L, \mathbf{I}_R$ mirrored, $\mathbf{I}_F, \mathbf{G}, \mathbf{L}$) with $\le 6.0\text{ ms}$ model inference and $\le 10.0\text{ ms}$ total pipeline budget.
- Comprehensive metric policy codified: Euclidean px (1080p reference and native), normalized diagonal error, component $MAE_x, MAE_y$, full distribution percentiles (P50, Mean, P90, P95, Max), Hit@25px, Hit@50px, Hit@100px, angular conversion formula ($D = 60\text{ cm}$).
- Operational safety criteria: fail-closed on tracking loss, anomalous jump suppression ($> 250\text{ px/frame}$), stale frame handling ($> 50\text{ ms}$ discard), 4 emergency escape mechanisms.
- Baseline progression hierarchy defined: Levels 0–3 (Center Dummy, Polynomial Ridge, RF/GBDT, Deep Appearance CNN).
- Zero-leakage grouping invariant formalized on 230 train / 7 val / 26 test split with cryptographically sealed test set and in-memory streaming extraction of `archive.zip`.
- Model promotion checklist codified as an 8-point binary verification gate.

## Change Tracker
- **Files modified**:
  * `docs/ml/ML_PROBLEM_DEFINITION.md`: Created comprehensive 883-line authoritative specification document.
- **Build status**: Verification checks passed. All repository invariants verified intact.
- **Pending issues**: None.

## Quality Status
- **Build/test result**: Invariants verified intact (`controller.py`, `ETHICS.md`, `archive.zip`, `face_landmarker.task`).
- **Lint status**: Clean Markdown formatting with validated LaTeX syntax and ASCII diagrams.
- **Tests added/modified**: Authoritative specification document created for Milestone 3.

## Loaded Skills
- Source: None required
- Local copy: None
- Core methodology: Publication-grade documentation, minimal change principle, invariant preservation

## Artifact Index
- `docs/ml/ML_PROBLEM_DEFINITION.md` — Authoritative specification document
- `.agents/teamwork/worker_m3/DISPATCH.md` — Task assignment log
- `.agents/teamwork/worker_m3/BRIEFING.md` — Agent briefing & working memory
- `.agents/teamwork/worker_m3/progress.md` — Progress and liveness tracker
- `.agents/teamwork/worker_m3/handoff.md` — Final handoff report
