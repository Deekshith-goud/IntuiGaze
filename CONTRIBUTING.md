# Contributing to EyeNav

Thank you for your interest in contributing to EyeNav.

EyeNav is a production-grade research platform. All contributions must meet the quality bar described in this document.

---

## Code of Conduct

All contributors must follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Types of Contributions

We welcome:

- **Research contributions** — new model architectures, dataset expansions, benchmarks
- **Engineering contributions** — performance improvements, platform support, testing
- **Documentation contributions** — research summaries, guides, API docs
- **Accessibility contributions** — user testing, accessibility audits, specialized input device support
- **Dataset contributions** — new training data, annotation tools, preprocessing pipelines

---

## Development Philosophy

Before any contribution:

1. **Research first** — understand the state of the art before proposing changes
2. **Design before code** — write a design document for any significant change
3. **Test everything** — unit tests, integration tests, performance benchmarks
4. **Document everything** — every module must have full docstrings and a README

---

## Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR-USERNAME/eyenav.git
cd eyenav

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v
```

---

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Write or update documentation for your change
3. Add tests (unit + integration minimum)
4. Run the full test suite: `pytest tests/ -v`
5. Run linting: `ruff check . && mypy .`
6. Update `CHANGELOG.md`
7. Submit a Pull Request with a clear description
8. Reference any related issues or ADRs

---

## Commit Convention

Use Conventional Commits:

```
feat: add EAR-based blink detection module
fix: correct gaze normalization for high-DPI displays
docs: update dataset registry with ETH-XGaze v2
test: add integration test for intent recognition pipeline
refactor: extract temporal context window logic
perf: optimize pupil localization inference to <5ms
```

---

## Code Style

- Python: PEP 8 enforced by `ruff`
- Type annotations required for all function signatures
- Docstrings: Google style
- Maximum line length: 100 characters
- No magic numbers — use constants in `configs/`

---

## Research Contributions

For new model architectures or training strategies:

1. Create a document in `research/` describing:
   - Problem being solved
   - Literature review (minimum 5 relevant papers)
   - Proposed approach
   - Expected tradeoffs
   - Evaluation plan
2. Open a Discussion issue before implementing
3. Provide baseline comparison results

---

## Dataset Contributions

All dataset contributions must include:

- Dataset card (following `datasets/registry/DATASET_CARD_TEMPLATE.md`)
- License verification
- Preprocessing pipeline
- Bias assessment
- Privacy review

---

## Questions?

Open a GitHub Discussion or email research@eyenav.ai
