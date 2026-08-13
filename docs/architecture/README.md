# EyeNav — Architecture Documentation

## Contents

| Document | Description |
|---|---|
| [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) | Full system architecture with candidate comparison |
| [ML_ARCHITECTURE.md](ML_ARCHITECTURE.md) | ML pipeline and model selection analysis |
| [VISION_PIPELINE.md](VISION_PIPELINE.md) | Detailed vision pipeline stage-by-stage |
| [SAFETY_SYSTEM.md](SAFETY_SYSTEM.md) | Multi-layer safety system design |
| [INTENT_ENGINE.md](INTENT_ENGINE.md) | Intent recognition engine design |
| [DATA_PIPELINE.md](DATA_PIPELINE.md) | Training and inference data flows |
| [MLOPS.md](MLOPS.md) | MLOps pipeline design |
| [ADR/](ADR/) | All Architecture Decision Records |

## Architecture Governance

All architecture decisions are recorded in ADRs before implementation begins.

ADR template: [ADR/ADR_TEMPLATE.md](ADR/ADR_TEMPLATE.md)

No significant architectural choice may be made without a corresponding ADR being approved.

## Key Principles

1. **Edge-first**: Primary inference runs on-device, no network required
2. **Modular**: Each pipeline stage is independently testable and replaceable
3. **Fail-safe**: System gracefully degrades, never crashes silently
4. **Observable**: All modules emit performance telemetry
5. **Configurable**: No hardcoded thresholds
