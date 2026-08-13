# EyeNav — Pipeline Diagrams

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** Architecture Team  
**Last Updated:** 2024-Q4  

This document contains all requested system diagrams using Mermaid notation.

---

## 1. Overall System Architecture

```mermaid
graph TB
    subgraph Hardware
        CAM[Camera\n≥ 720p, ≥ 30fps]
        DISP[Display]
    end

    subgraph EyeNav Pipeline
        FD[Face Detection\nBlazeFace, 3ms]
        LM[Landmark Extraction\nFaceMesh 468pts, 6ms]
        
        subgraph Eye Analysis - Parallel
            GE[Gaze Estimation\nL2CS-Net, 6ms]
            BD[Blink Detection\nEAR+CNN, 4ms]
            PD[Pupil Detection\nMediaPipe Iris, 3ms]
            ED[Eyebrow Detection\nMLP, 2ms]
            HP[Head Pose\nSolvePnP, 2ms]
        end
        
        FA[Feature Assembly\n32-dim vector, 1ms]
        TB[Temporal Buffer\n45 frames × 32-dim]
        IE[Intent Engine\nTiny Transformer, 8ms]
        SF[Safety Filter\n6-layer, 1ms]
        OS[OS Integration\nSendInput / CGEvent]
    end

    subgraph Monitoring
        PROM[Prometheus Metrics]
        GRAF[Grafana Dashboard]
    end

    CAM --> FD
    FD --> LM
    LM --> GE
    LM --> BD
    LM --> PD
    LM --> ED
    LM --> HP
    GE --> FA
    BD --> FA
    PD --> FA
    ED --> FA
    HP --> FA
    FA --> TB
    TB --> IE
    IE --> SF
    SF --> OS
    OS --> DISP
    SF --> PROM
    PROM --> GRAF
```

---

## 2. Vision Pipeline (Stage by Stage)

```mermaid
flowchart TB
    C[Camera Frame\nBGR uint8, 1280×720]
    C --> FD

    subgraph Stage1 [Stage 1 - Face]
        FD[Face Detection\nBlazeFace\nOutput: BBox + score]
        FT[Face Tracking\nKalman filter\nSmooth between frames]
        FA[Face Alignment\n96×112 crop\nNormalized]
        FD --> FT --> FA
    end

    FA --> Stage2

    subgraph Stage2 [Stage 2 - Landmarks]
        LM[FaceMesh 468-point\nMediaPipe\nOutput: 3D landmark coords]
        ER[Eye Region Extract\nLeft + Right\n64×32 crops]
        EyBR[Eyebrow Region Extract\nLeft + Right]
        LM --> ER
        LM --> EyBR
    end

    Stage2 --> Stage3

    subgraph Stage3 [Stage 3 - Eye Analysis]
        ES[Eye Segmentation\nPupil, Iris, Sclera\nSoft segmentation mask]
        PL[Pupil Localization\nCenter + radius\nGeometric from segments]
        IL[Iris Localization\nIris limbus circle\nRobust edge detection]
        ER --> ES --> PL --> IL
    end

    Stage2 --> Stage4

    subgraph Stage4 [Stage 4 - Blink + Gaze + Pose]
        BL[Blink Detection\nEAR + CNN\n9 blink types]
        GZ[Gaze Estimation\nL2CS-Net\nyaw + pitch + screen coords]
        HP[Head Pose\nSolvePnP\nyaw, pitch, roll degrees]
        EW[Eyebrow State\nMLP\n5 states]
    end

    Stage3 --> Stage4
    Stage2 --> Stage4

    Stage4 --> FE

    subgraph FeatEng [Stage 5 - Feature Engineering]
        FE[Feature Assembly\n32-dimensional vector\nFrame-level representation]
        TC[Temporal Construction\n45-frame buffer\n1.5-second window]
        FE --> TC
    end

    TC --> IC

    subgraph IntentClass [Stage 6 - Intent + Safety]
        IC[Intent Classification\nTiny Temporal Transformer\n13 intent classes]
        CS[Confidence Scoring\nSoftmax probs + uncertainty]
        SR[Safety Rules\n6-layer gate]
        IC --> CS --> SR
    end

    SR --> EL

    subgraph ExecLayer [Stage 7 - Execution]
        EL[Command Execution\nOS Integration]
    end
```

---

## 3. ML Pipeline

```mermaid
flowchart LR
    subgraph Data
        DS[Datasets\nETH-XGaze, MPIIGaze,\nEPID, RT-GENE...]
        DVC[DVC Data Versioning]
        PP[Preprocessing\nNormalization\nAugmentation\nSplit]
        DS --> DVC --> PP
    end

    PP --> Training

    subgraph Training
        TR[PyTorch + Lightning\nModel Training]
        EX[Experiment Tracking\nMLFlow + W&B]
        CK[Checkpointing\nBest + Last]
        TR --> EX
        TR --> CK
    end

    CK --> Evaluation

    subgraph Evaluation
        EV[Evaluation Harness\nAccuracy + Latency]
        BI[Bias Evaluation\nStrat. by demographics]
        EV --> BI
    end

    BI --> Export

    subgraph Export
        ONNX[ONNX Export]
        QNT[INT8 Quantization]
        VAL[Validation\nPyTorch vs ONNX < 1e-5]
        ONNX --> QNT --> VAL
    end

    VAL --> Registry

    subgraph Registry
        MR[MLFlow Model Registry\nStaging → Production]
        PR[Promotion Policy\n7 criteria must pass]
        MR --> PR
    end

    PR --> Deployment

    subgraph Deployment
        DIST[Model Distribution\nInstaller / DVC / Docker]
        DIST --> Live
    end

    subgraph Monitoring
        Live[Production Inference]
        DR[Drift Detection\nPage-Hinkley test]
        AL[Alert\nFPR, Confidence, FPS]
        Live --> DR --> AL
        AL -->|Retrain trigger| Data
    end
```

---

## 4. Data Pipeline

```mermaid
flowchart TB
    subgraph Sources
        PUB[Public Datasets\nETH-XGaze, MPIIGaze,\nRT-GENE, GazeCapture, etc.]
        EPID[EPID Recording Sessions\n1000+ participants]
    end

    PUB --> PP1[Preprocessing\nDownload + verify + normalize]
    EPID --> ANN[Annotation\nAuto-label + human review]

    PP1 --> STORE
    ANN --> STORE

    subgraph STORE [Versioned Storage]
        DVC_STORE[DVC + Object Storage\nContent-addressed\nImmutable versions]
    end

    STORE --> SPLIT[Train/Val/Test Split\nStratified by user + condition]

    SPLIT --> TR_DATA[Training Data]
    SPLIT --> VAL_DATA[Validation Data]
    SPLIT --> TEST_DATA[Test Data\nHeld-out permanently]

    TR_DATA --> AUG[Data Augmentation\nBrightness, Contrast\nHead Pose, Glasses sim]
    AUG --> LOADER[DataLoader\nPyTorch\nPrefetch + cache]
    LOADER --> TRAINING[Training Jobs]

    TEST_DATA --> EVAL[Evaluation\nNever used for training]
```

---

## 5. Deployment Pipeline

```mermaid
flowchart LR
    DEV[Developer\nPush to branch]
    DEV --> PR[Pull Request]
    PR --> CI

    subgraph CI [GitHub Actions CI]
        LINT[Ruff Lint\n+ Mypy Types]
        TESTS[pytest\nUnit + Integration]
        SECURITY[bandit\n+ pip-audit]
        COVER[Coverage ≥ 80%]
        LINT --> TESTS --> SECURITY --> COVER
    end

    CI --> |Pass| REVIEW[Code Review\n+ Safety Lead Sign-off]
    REVIEW --> MERGE[Merge to main]

    MERGE --> BUILD

    subgraph BUILD [Release Build]
        WIN[Windows EXE\nPyInstaller + NSIS]
        MAC[macOS DMG\nPy2app]
        LIN[Linux AppImage\nlinuxdeployqt]
        DOCK[Docker Image\nMulti-stage]
        WIN & MAC & LIN & DOCK
    end

    BUILD --> SIGN[Code Signing\nEV Certificate]
    SIGN --> STAGE[Staging Deployment\nInternal testing]
    STAGE --> |Validation pass| GA[GA Release\nGitHub Releases\n+ Package Managers]
```

---

## 6. Monitoring Pipeline

```mermaid
flowchart LR
    subgraph Pipeline
        INFER[Inference\nEngine]
        SAFETY[Safety\nFilter]
    end

    INFER --> |Metrics| PROM_PUSH[Prometheus\nPushgateway]
    SAFETY --> |Metrics| PROM_PUSH

    PROM_PUSH --> PROM[Prometheus\nTime-series DB]
    PROM --> GRAF[Grafana\nDashboards]

    PROM --> ALERT[AlertManager\nThreshold alerts]
    ALERT --> |FPR > 0.15%| OPS[On-call Engineer\nPagerDuty]
    ALERT --> |Drift detected| ML[ML Team\nReview + Retrain]

    subgraph Dashboards
        FPS_PANEL[Pipeline FPS]
        LAT_PANEL[Latency p50/p95/p99]
        CONF_PANEL[Confidence Distribution]
        FPR_PANEL[False Positive Rate]
        CMD_PANEL[Command Distribution]
    end

    GRAF --> Dashboards
```

---

## 7. Feedback Pipeline

```mermaid
flowchart TB
    USER[User Interaction\nReal-world usage]
    USER --> |Commands executed| LOG[Audit Log\nLocal encrypted]
    USER --> |Optional telemetry\n(anonymized, opt-in)| ANON[Anonymization\nDifferential Privacy ε=1.0]
    ANON --> COLLECT[Collection\nTLS 1.3]
    COLLECT --> AGGREGATE[Aggregation\nRemove any PII]
    AGGREGATE --> ANALYSIS[Analysis\nDrift detection\nUser behavior patterns]
    ANALYSIS --> |Insights| PRODUCT[Product Team\nFeature prioritization]
    ANALYSIS --> |Data signals| ML[ML Team\nModel improvement]
    ML --> |New training data| DATASETS[EPID Dataset\nNew batch]
    DATASETS --> |Quarterly retrain| MODELS[Updated Models]
    MODELS --> |Rolling deployment| USER
```

---

## 8. Learning Pipeline (Personalization)

```mermaid
flowchart TB
    USER[New User]
    USER --> CALIB[Initial Calibration\n5-point, 30 seconds]
    CALIB --> PROFILE[User Profile\nCalibration params\nThreshold preferences]

    PROFILE --> PIPELINE[Active Pipeline\nPersonalized inference]

    PIPELINE --> |Per-session stats| MONITOR[Session Monitor\nConfidence trends\nFatigue indicators]

    MONITOR --> |Accuracy degraded| DRIFT_DETECT[Drift Detection\nGaze accuracy\nEAR baseline drift]

    DRIFT_DETECT --> |Recalibration needed| RECALIB_PROMPT[Recalibration Prompt\nIn-app notification]

    PIPELINE --> |Feedback| ONLINE_LEARN[Online Adaptation\nThreshold adjustment\nEAR baseline update]

    ONLINE_LEARN --> PROFILE

    subgraph Future
        FL[Federated Learning\nOn-device training\nNo data leaves device]
        META[Meta-learning\nFew-shot personalization\nNo explicit calibration]
    end
```
