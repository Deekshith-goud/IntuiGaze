# EyeNav — Deployment Strategy

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** DevOps + Platform Team  
**Last Updated:** 2024-Q4  

---

## 1. Overview

EyeNav ships in two primary deployment modes:

1. **Standalone Desktop App** — Direct installation on Windows/macOS/Linux. No server required. All inference runs locally.
2. **Server Mode** — FastAPI server with WebSocket streaming. Used for multi-client setups, research environments, or SDK integration.

Both modes share the same core Python inference pipeline (`backend/eyenav/`), ensuring no code divergence.

---

## 2. Platform Support Matrix

### Phase 1 (v1.0) — Target

| Platform | Mode | Package Format | Status |
|---|---|---|---|
| Windows 10/11 x64 | Standalone | PyInstaller EXE + installer | v1.0 |
| macOS 12+ Intel | Standalone | DMG + app bundle | v1.0 |
| macOS 12+ Apple Silicon | Standalone | Universal binary DMG | v1.0 |
| Ubuntu 20.04+ x64 | Standalone | AppImage + .deb | v1.0 |
| Docker (Linux) | Server mode | Docker image | v1.0 |

### Phase 2 (v1.5)

| Platform | Mode | Package Format | Status |
|---|---|---|---|
| Android 10+ | Mobile SDK | AAR library | v1.5 |
| iOS 15+ | Mobile SDK | Swift Package | v1.5 |
| Electron (desktop web apps) | JS SDK | npm package | v1.5 |
| Windows ARM64 | Standalone | EXE | v1.5 |

### Phase 3 (v2.0)

| Platform | Mode | Status |
|---|---|---|
| OpenXR (Meta Quest, Pico) | VR SDK | v2.0 |
| visionOS | Apple Vision Pro SDK | v2.0 |
| React Native | Cross-platform mobile | v2.0 |
| Flutter | Cross-platform mobile | v2.0 |

---

## 3. Desktop Packaging

### 3.1 Build Pipeline (PyInstaller)

```bash
# Build production executable (Windows)
pyinstaller \
  --onefile \
  --windowed \
  --icon=assets/icons/eyenav.ico \
  --add-data "models/*.onnx;models/" \
  --add-data "configs/defaults.yaml;configs/" \
  --name EyeNav \
  backend/eyenav/desktop_app.py
```

### 3.2 Windows Installer (NSIS / WiX)

```xml
<!-- WiX installer snippet -->
<Product Id="*" Name="EyeNav" Version="1.0.0"
         Manufacturer="EyeNav Inc." Language="1033">
  <Package InstallerVersion="200" Compressed="yes" />
  <Feature Id="Core" Level="1">
    <ComponentRef Id="MainExecutable" />
    <ComponentRef Id="Models" />
    <ComponentRef Id="DefaultConfig" />
  </Feature>
</Product>
```

### 3.3 macOS DMG

```bash
# Build app bundle
python setup.py py2app

# Create DMG
create-dmg \
  --volname "EyeNav" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --app-drop-link 425 120 \
  EyeNav.dmg \
  dist/EyeNav.app
```

### 3.4 Linux AppImage

```bash
# Build AppImage
linuxdeployqt dist/EyeNav -appimage
```

---

## 4. Docker Deployment (Server Mode)

### 4.1 Standard Deployment

```bash
# Single server instance
docker run -d \
  --name eyenav-server \
  -p 8765:8765 \
  -v /path/to/models:/app/models:ro \
  -v eyenav-profiles:/app/data/profiles \
  eyenav/server:latest
```

### 4.2 Full Stack (Development/Research)

```bash
# All services (server + monitoring + database)
cd deployment/docker/
docker-compose up -d

# Services started:
# - EyeNav Server:   http://localhost:8765
# - MLflow:          http://localhost:5000
# - Grafana:         http://localhost:3000
# - Prometheus:      http://localhost:9090
```

### 4.3 Kubernetes Deployment (Research/Enterprise)

```yaml
# deployment/k8s/eyenav-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: eyenav-server
  namespace: eyenav
spec:
  replicas: 2
  selector:
    matchLabels:
      app: eyenav-server
  template:
    metadata:
      labels:
        app: eyenav-server
    spec:
      containers:
      - name: eyenav-server
        image: eyenav/server:1.0.0
        ports:
        - containerPort: 8765
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
        readinessProbe:
          httpGet:
            path: /health
            port: 8765
          initialDelaySeconds: 10
          periodSeconds: 10
        volumeMounts:
        - name: models
          mountPath: /app/models
          readOnly: true
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: eyenav-models-pvc
```

---

## 5. Model Distribution

Models are large binary files (10–50MB each). They are distributed separately from the application code.

### 5.1 Distribution Strategy

| Environment | Method |
|---|---|
| Desktop app | Bundled in installer (encrypted) |
| Docker image | Baked into image layer |
| Research/dev | DVC pull from object storage |
| CI/CD | Cached between builds |

### 5.2 Model Integrity

All models ship with SHA256 checksums. The application verifies checksums at startup before loading any model:

```python
# backend/eyenav/model_loader.py
def verify_model(model_path: Path, expected_sha256: str) -> bool:
    """
    Verify model file integrity before loading.
    Raises ModelLoadError if checksum does not match.
    """
    sha256 = hashlib.sha256(model_path.read_bytes()).hexdigest()
    if sha256 != expected_sha256:
        raise ModelLoadError(
            f"Model integrity check failed: {model_path.name}. "
            "The model file may be corrupted. Re-install EyeNav."
        )
    return True
```

---

## 6. Release Channels

| Channel | Purpose | Update Frequency | Audience |
|---|---|---|---|
| Stable | Production releases | Quarterly | End users |
| Beta | Pre-release testing | Monthly | Beta testers |
| Nightly | Automated builds | Daily | Developers |
| Research | Special builds | Ad hoc | Research partners |

---

## 7. Auto-Update Mechanism (Desktop)

Desktop app checks for updates on launch (opt-in).

- Update check: HTTPS request to `https://api.eyenav.ai/updates/latest`
- Response: version number + download URL + SHA256 + release notes
- Download: Background download, install on restart
- Verification: SHA256 verification before installation
- Rollback: Previous version preserved for 30 days

Privacy: Update check sends only app version and OS. No user data.

---

## 8. Configuration Management

### 8.1 Config Precedence (highest to lowest)

1. Environment variables (`EYENAV_*`)
2. User profile config (`~/.eyenav/config.yaml`)
3. Application defaults (`configs/defaults.yaml`)

### 8.2 Enterprise Deployment

For institutional deployment (hospitals, schools):

```yaml
# Managed config pushed via MDM or Group Policy
# /etc/eyenav/managed.yaml
safety:
  thresholds:
    high_risk: 0.97  # Stricter in institutional settings
  cooldown_ms: 2000  # Longer cooldown
  emergency_stop_duration_ms: 5000

privacy:
  analytics_enabled: false  # Enforce off for HIPAA
  telemetry_enabled: false
```

---

## 9. Monitoring in Production

### 9.1 Server Mode Metrics (Prometheus)

Exposed at `/metrics`:
- `eyenav_pipeline_fps` — Current processing FPS
- `eyenav_intent_latency_ms` — Intent classification latency (histogram)
- `eyenav_false_positive_total` — Count of blocked commands
- `eyenav_confidence_mean` — Rolling mean confidence score
- `eyenav_active_sessions` — Number of connected clients

### 9.2 Crash Reporting (Desktop — Opt-in)

- Platform: Sentry (self-hosted for privacy)
- Data: Stack trace, OS version, app version, anonymous session ID
- No gaze data, no user identity
- Opt-in only, explicit consent at first launch

---

## 10. Deployment Checklist

Before any production release:

- [ ] All automated tests pass (green CI)
- [ ] Safety test suite: 100% pass
- [ ] Performance benchmark: all SRS-PERF-* pass
- [ ] ONNX model integrity: checksums verified
- [ ] Docker image: security scan (no critical CVEs)
- [ ] Code signing: EXE/DMG/AppImage signed
- [ ] Release notes written
- [ ] Upgrade path tested from previous version
- [ ] Rollback procedure tested
- [ ] Documentation updated
- [ ] Privacy policy reviewed (if data handling changes)
