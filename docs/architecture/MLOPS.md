# EyeNav — MLOps Pipeline Design

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** MLOps Team  
**Last Updated:** 2024-Q4  

---

## 1. Overview

The EyeNav MLOps pipeline manages the complete lifecycle of all machine learning models:
- Training and experimentation
- Model evaluation and validation
- Registry and versioning
- Continuous integration for models
- Monitoring and drift detection
- Rollback mechanisms

---

## 2. Training Pipeline

### 2.1 Training Infrastructure

```
Data Sources
    ├── ETH-XGaze (gaze)
    ├── MPIIGaze (gaze)
    ├── GazeCapture (gaze, mobile)
    ├── RT-GENE (gaze + blink)
    ├── Eyeblink8 (blink benchmark)
    └── EPID (intent — proprietary)
            │
            ▼
DVC Pipeline (data versioning)
            │
            ▼
Preprocessing Jobs (Docker)
    ├── Normalization
    ├── Augmentation
    └── Train/Val/Test split
            │
            ▼
Training (PyTorch + Lightning)
    ├── Experiment tracking (MLFlow + W&B)
    ├── Checkpoint saving
    └── Early stopping
            │
            ▼
Evaluation Harness
    ├── Accuracy metrics
    ├── Latency benchmarks
    └── Bias evaluation (stratified)
            │
            ▼
ONNX Export + Optimization
            │
            ▼
Model Registry (MLFlow)
            │
            ▼
Deployment Pipeline
```

### 2.2 Experiment Tracking (MLFlow + W&B)

All experiments log:
- Hyperparameters (learning rate, batch size, model architecture)
- Training metrics (loss, accuracy, per-class metrics)
- Validation metrics per epoch
- Artifacts (model weights, ONNX exports, evaluation plots)
- Dataset version (DVC commit hash)
- Hardware info (GPU model, CUDA version)
- Training duration and resource usage

```python
# Example MLFlow logging (training script excerpt)
import mlflow

with mlflow.start_run(run_name="intent-transformer-v3"):
    mlflow.log_params({
        "model": "tiny_transformer",
        "n_layers": 4,
        "d_model": 128,
        "n_heads": 4,
        "learning_rate": 3e-4,
        "batch_size": 128,
        "window_ms": 1500,
        "dataset_version": dvc.get_rev("datasets/custom/epid/"),
    })
    
    for epoch in range(n_epochs):
        train_loss = train_epoch(model, loader)
        val_metrics = evaluate(model, val_loader)
        
        mlflow.log_metrics({
            "train_loss": train_loss,
            "val_accuracy": val_metrics.accuracy,
            "val_f1": val_metrics.f1,
            "val_precision": val_metrics.precision,
        }, step=epoch)
    
    mlflow.pytorch.log_model(model, "model")
    mlflow.log_artifact("model_exported.onnx")
```

---

## 3. Model Registry

### 3.1 Registry Structure (MLFlow)

```
Model Registry
├── eyenav-face-detection
│   ├── staging (blazeface-v2)
│   └── production (blazeface-v1)
├── eyenav-gaze
│   ├── staging (l2cs-mobilenetv3-v2)
│   └── production (l2cs-mobilenetv3-v1)
├── eyenav-blink
│   ├── staging (ear-cnn-v3)
│   └── production (ear-cnn-v2)
├── eyenav-intent
│   ├── staging (tiny-transformer-v1)
│   └── production (none — first deployment)
└── eyenav-eyebrow
    ├── staging (landmark-mlp-v1)
    └── production (landmark-mlp-v1)
```

### 3.2 Model Promotion Policy

A model may be promoted from `staging` to `production` only if:

1. ✅ Accuracy meets or exceeds current production model on held-out test set
2. ✅ Latency within budget on standard benchmark hardware
3. ✅ No regression in any demographic sub-group (bias evaluation)
4. ✅ ONNX export validated (output matches PyTorch within 1e-5)
5. ✅ Safety tests pass with new model
6. ✅ Manual review by ML lead
7. ✅ Signed off by safety review lead

---

## 4. Evaluation Pipeline

### 4.1 Automated Evaluation Suite

Run after every training job:

```bash
python training/evaluate.py \
  --model-path checkpoints/intent_v3.pth \
  --dataset datasets/custom/epid/test/ \
  --metrics accuracy precision recall f1 latency \
  --stratify-by age_group ethnicity glasses \
  --output-dir evaluation/results/intent_v3/
```

### 4.2 Metrics Tracked

**Gaze Models:**
- MAE (Mean Angular Error) in degrees — primary metric
- Max angular error (95th percentile)
- Latency (mean, p95, p99) on CPU
- Accuracy with/without glasses

**Blink Detection:**
- Precision, Recall, F1 for each blink type
- False positive rate per 100 frames
- Latency (mean, p95)

**Intent Recognition:**
- Per-class precision, recall, F1
- Overall accuracy
- Confusion matrix (visualized)
- False positive rate for command classes (safety metric)
- Latency (mean, p95)

### 4.3 Bias Evaluation

For every model, evaluate performance stratified by:
- Age group: <18, 18-35, 36-55, 55+
- Ethnicity: 6 groups (self-reported in dataset)
- Glasses: no glasses, thin frames, thick frames
- Lighting: bright, dim, mixed
- Camera quality: 720p, 1080p, 4K

**Acceptance criterion:** No group may perform >5% below overall accuracy.

---

## 5. ONNX Export & Optimization

### 5.1 Export Pipeline

```python
# scripts/export_onnx.py
import torch
import onnx
import onnxruntime as ort
from onnxsim import simplify

def export_and_validate(
    model: torch.nn.Module,
    dummy_input: torch.Tensor,
    output_path: str,
    opset_version: int = 17
) -> bool:
    """
    Export PyTorch model to ONNX and validate output matches.
    
    Returns True if validation passes within tolerance.
    """
    # Export
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        opset_version=opset_version,
        input_names=["input"],
        output_names=["logits", "attention"],
        dynamic_axes={"input": {0: "batch_size", 1: "sequence_length"}}
    )
    
    # Simplify (remove redundant operations)
    model_onnx = onnx.load(output_path)
    model_simplified, check = simplify(model_onnx)
    assert check, "ONNX simplification failed"
    onnx.save(model_simplified, output_path)
    
    # Validate: PyTorch vs ONNX output must match within 1e-5
    with torch.no_grad():
        torch_output = model(dummy_input).numpy()
    
    session = ort.InferenceSession(output_path)
    onnx_output = session.run(None, {"input": dummy_input.numpy()})[0]
    
    max_diff = abs(torch_output - onnx_output).max()
    
    if max_diff > 1e-5:
        raise ValueError(f"ONNX validation failed: max_diff={max_diff}")
    
    return True
```

### 5.2 Quantization (INT8)

For maximum CPU performance:

```python
from onnxruntime.quantization import quantize_dynamic, QuantType

quantize_dynamic(
    model_input="models/intent/tiny_transformer.onnx",
    model_output="models/intent/tiny_transformer_int8.onnx",
    weight_type=QuantType.QInt8
)
```

INT8 quantization typically:
- Reduces model size by 4x
- Improves CPU inference speed by 2-4x
- Accuracy impact: < 0.5% (empirically verified)

---

## 6. Monitoring & Drift Detection

### 6.1 Production Monitoring (Prometheus + Grafana)

Dashboard panels:
- Pipeline FPS (alert if < 25fps)
- Intent classification latency (alert if p95 > 50ms)
- Confidence distribution histogram (drift indicator)
- False positive block rate (safety metric)
- Command type distribution (drift indicator)
- Camera quality metrics (low FPS, dropped frames)

### 6.2 Concept Drift Detection

Monitor for changes in:
- Distribution of intent classifications (population drift)
- Average confidence scores decreasing (gaze model degradation)
- False positive rate increasing (safety drift)
- Latency increasing (resource contention)

Detection method: Page-Hinkley test on rolling window statistics.

Alert threshold: Statistically significant drift triggers review.

### 6.3 Model Rollback

```bash
# Rollback to previous production model
python scripts/rollback.py --model eyenav-intent --to-version 1

# This:
# 1. Downloads previous model version from registry
# 2. Updates deployment config
# 3. Restarts inference service
# 4. Verifies rollback via health check
# 5. Logs rollback event with reason
```

---

## 7. Continuous Training

When sufficient new labeled data is available (every 3 months or 100,000 new frames):

1. **Data validation**: Check new data against schema, run quality checks
2. **Bias assessment**: Ensure new data doesn't introduce imbalance
3. **Fine-tuning**: Update model on new data + replay buffer of old data
4. **Evaluation**: Full evaluation suite on updated test set
5. **Promotion**: Follow standard promotion policy
6. **Deployment**: Rolling deployment with canary testing

---

## 8. Tools

| Tool | Purpose | Version |
|---|---|---|
| MLFlow | Experiment tracking + Model registry | 2.11+ |
| Weights & Biases | Visualization, collaboration | Latest |
| DVC | Dataset versioning | 3.0+ |
| ONNX Runtime | Production inference | 1.17+ |
| Prometheus | Metrics collection | 2.50+ |
| Grafana | Metrics visualization | 10+ |
| Docker | Training environment | 25+ |
| PyTorch Lightning | Training framework | 2.2+ |
