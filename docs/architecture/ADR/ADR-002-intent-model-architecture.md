# ADR-002 — Intent Recognition: Transformer vs. LSTM vs. TCN

**Status:** Accepted  
**Date:** 2024-Q4  
**Deciders:** ML Team  
**Tags:** model, intent, architecture  

---

## Context

The intent recognition module must classify user intent from a 1.5-second window of temporal gaze/blink/eyebrow features. The choice of temporal model architecture determines accuracy, latency, interpretability, and training data requirements.

## Decision Drivers

- **Accuracy**: ≥ 95% intent classification accuracy
- **Latency**: ≤ 50ms from gesture completion
- **Interpretability**: must be explainable to users and auditors
- **Training data efficiency**: limited labeled data for novel intent classes

## Considered Options

| Architecture | Acc (est.) | Latency | Interpretability | Data Efficiency |
|---|---|---|---|---|
| LSTM | ~88% | ~5ms | Low | Medium |
| GRU | ~87% | ~4ms | Low | Medium |
| Temporal CNN | ~91% | ~3ms | Medium | High |
| Tiny Transformer | ~95% | ~8ms | High (attention) | Medium-High |
| Mamba (SSM) | ~94% | ~6ms | Medium | Limited tooling |
| Ensemble (TCN+LSTM) | ~93% | ~8ms | Low | High |

## Decision Outcome

**Chosen Option: Tiny Temporal Transformer (4-layer, 128-dim)**

Justification:
1. Attention mechanism provides inherent interpretability (which frames drove the prediction)
2. Global context capture is essential for intents that develop over 1-3 seconds
3. 8ms inference is well within the 50ms intent latency budget
4. Transformer attention visualizations can be shown to users for trust-building
5. Strong inductive bias toward the "what matters in this sequence" question

LSTM/GRU rejected: Lower accuracy, no interpretability, no attention mechanism.
TCN rejected: Fixed receptive field problematic for variable-duration intents.
Mamba rejected: Limited production tooling at time of decision (2024).

## Consequences

### Positive
- Attention maps enable per-prediction explanations
- Global context suitable for long-duration intents (reading: 2-3 seconds)
- Transfer learning from pre-trained temporal models possible

### Negative
- Requires more training data than recurrent models
- More complex to implement than LSTM baseline
- Attention is O(n²) — but for n=45 frames, this is trivial

### Risks
- ONNX export of custom attention may require testing → Mitigation: use standard PyTorch MultiheadAttention (ONNX opset 12+)

## Validation

- [ ] Intent accuracy ≥ 95% on EyeNav test set
- [ ] Attention visualization shows meaningful patterns
- [ ] Latency ≤ 50ms on target hardware

## References

- Vaswani et al. (2017). Attention is All You Need. NeurIPS.
- ML Architecture Document: ../ML_ARCHITECTURE.md
