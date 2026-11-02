# EyeNav — Scripts Directory

## Purpose

Utility scripts for common development, operations, and research tasks. These are one-off or periodic scripts, not application code.

## Structure

```
scripts/
├── setup/
│   ├── install_dev.sh         # Full development environment setup
│   ├── install_models.sh      # Download pre-trained model weights
│   └── check_environment.py   # Verify all dependencies are correct
├── data/
│   ├── preprocess_gaze.py     # Preprocess gaze datasets (ETH-XGaze, MPIIGaze)
│   ├── preprocess_epid.py     # Preprocess EPID recordings
│   ├── split_dataset.py       # Create train/val/test splits
│   └── compute_statistics.py  # Dataset statistics (mean, std, class balance)
├── models/
│   ├── export_onnx.py         # Export PyTorch model to ONNX
│   ├── quantize_int8.py       # INT8 quantization for CPU optimization
│   ├── verify_onnx.py         # Verify ONNX output matches PyTorch
│   └── benchmark_model.py     # Benchmark a specific model's latency
├── deployment/
│   ├── build_all.sh           # Build all platform packages
│   ├── sign_release.sh        # Code sign release artifacts
│   └── upload_release.sh      # Upload to GitHub Releases
├── ops/
│   ├── monitor_dashboard.sh   # Open Grafana + Prometheus in browser
│   ├── backup_profiles.sh     # Backup all user profiles
│   └── rotate_secrets.sh      # Rotate API keys / secrets
└── README.md                  # This file
```

## Commonly Used Scripts

### Setup Development Environment

```bash
# Full setup from scratch
bash scripts/setup/install_dev.sh

# What it does:
# 1. Creates virtual environment
# 2. Installs pip dependencies
# 3. Installs pre-commit hooks
# 4. Downloads model files (dvc pull)
# 5. Runs test suite to verify
```

### Export Model to ONNX

```bash
python scripts/models/export_onnx.py \
  --model-class TinyTransformer \
  --checkpoint checkpoints/intent/best.pth \
  --output models/intent/tiny_transformer.onnx \
  --verify
```

### Preprocess ETH-XGaze Dataset

```bash
python scripts/data/preprocess_gaze.py \
  --dataset-root ~/datasets/eth-xgaze/ \
  --output datasets/processed/eth-xgaze/ \
  --normalize screen \
  --split 0.8 0.1 0.1
```

### Build All Platform Packages

```bash
# Build Windows EXE + macOS DMG + Linux AppImage
bash scripts/deployment/build_all.sh v1.0.0
```

## Script Standards

- All Python scripts: type annotations, docstrings, `if __name__ == "__main__"` guard
- All shell scripts: `set -euo pipefail`, error handling, usage string
- All scripts: `--help` flag required
- No scripts may modify production databases without explicit `--confirm` flag

## Responsibilities

- **All engineers:** Contribute scripts for repetitive tasks they encounter
- **DevOps:** Maintain deployment scripts and CI integration
- **ML Engineers:** Maintain data and model scripts
- **Principle:** Scripts go here, not in random project directories

## Future Improvements

- Makefile wrapping common scripts for discoverability
- Script catalog with descriptions (auto-generated from docstrings)
- Integration tests for critical scripts
