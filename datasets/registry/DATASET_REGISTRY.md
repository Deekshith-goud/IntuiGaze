# EyeNav — Dataset Registry

**Document Version:** 1.0  
**Status:** Research Complete  
**Owner:** Dataset Engineering Team  
**Last Updated:** 2024-Q4  

---

## Overview

This registry documents all public datasets relevant to EyeNav's vision pipeline. Each dataset is evaluated for:
- Annotations available
- License and commercial usability
- Compatibility with EyeNav modules
- Known biases and limitations

---

## Summary Table

| Dataset | Primary Use | Size | License | Commercial? | EyeNav Module |
|---|---|---|---|---|---|
| MPIIGaze | Gaze estimation | 213,659 imgs | Creative Commons | Research only | Gaze |
| ETH-XGaze | Gaze estimation | 1,083,492 imgs | Academic non-commercial | Research only | Gaze |
| RT-GENE | Gaze + blink | 122,531 imgs | CC BY-NC-SA 4.0 | Research only | Gaze, Blink |
| GazeCapture | Mobile gaze | 2.5M frames, 1,474 subjects | MIT | ✅ Yes | Gaze |
| OpenEDS 2019 | VR gaze + seg | 12,759 imgs | CC BY-NC 4.0 | Research only | Gaze, Segmentation |
| OpenEDS 2020 | Gaze sequence | 91 subjects | CC BY-NC 4.0 | Research only | Gaze |
| UnityEyes | Synthetic gaze | 1M images | CC BY 4.0 | ✅ Yes | Gaze augmentation |
| 300-W | Facial landmarks | 600 imgs | Research | Research only | Landmarks |
| WFLW | Facial landmarks | 10,000 imgs | CC BY-NC-SA | Research only | Landmarks |
| AFLW | Face detection | 25,993 imgs | Research | Research only | Face detection |
| CEW | Eye detection | 4,824 imgs | Research | Research only | Blink |
| BioID | Face detection | 1,521 imgs | Restricted | Research only | Face detection |
| MUCT | Facial landmarks | 3,755 imgs | CC Attribution | ✅ Yes | Landmarks |
| TalkingFace | Video face | 5,000 frames | Research | Research only | Tracking |
| Eyeblink8 | Blink detection | 8 videos, ~20k frames | CC BY-NC-ND | Research only | Blink |
| ZJU-Gaze | Gaze + head | 12 subjects, video | Research | Research only | Gaze |
| Columbia Gaze | Discrete gaze | 5,880 imgs | Research | Research only | Gaze direction |
| CAVE Dataset | Gaze (lab) | 5 subjects, 16 angles | Research | Research only | Gaze calibration |
| TabletGaze | Mobile gaze | 51 subjects | CC BY-NC | Research only | Mobile gaze |
| EyeDiap | Gaze 3D | 16 subjects | Research | Research only | 3D gaze |

---

## Detailed Dataset Cards

---

### DS-001 — MPIIGaze

**Full Name:** Max Planck Institute for Informatics Gaze Dataset  
**Source:** Max Planck Institute for Informatics, Germany  
**Paper:** Zhang, X., et al. (2015). Appearance-Based Gaze Estimation in the Wild. CVPR 2015.  
**Download:** https://www.mpi-inf.mpg.de/departments/computer-vision-and-machine-learning/research/gaze-based-human-computer-interaction/appearance-based-gaze-estimation-in-the-wild/  

#### Description
First large-scale appearance-based gaze dataset collected in real, uncontrolled environments. Subjects used personal laptops in daily settings over multiple sessions.

#### Dataset Statistics
| Property | Value |
|---|---|
| Total Images | 213,659 |
| Subjects | 15 (7 male, 8 female) |
| Sessions per Subject | ~2,500 average |
| Image Resolution | 1280×720 (eye crops: 60×36) |
| Video | No (still images) |
| 3D Gaze Labels | Yes (gaze direction vectors) |
| 2D Screen Gaze | Yes (screen coordinates) |
| Head Pose | Yes |
| Facial Landmarks | 6 sparse points |

#### Annotation Types
- Gaze direction (3D unit vector)
- Gaze target (2D screen coordinates)
- Head pose (rotation matrix)
- Facial landmarks (6 points)
- Normalized eye images (LeNET normalization)

#### Strengths
- Real-world collection (not lab) — high ecological validity
- Multi-session per subject captures intra-person variability
- Established benchmark — extensively cited in gaze literature
- Normalization pipeline published and reproducible

#### Weaknesses
- Only 15 subjects — low diversity (ethnicity, age range)
- Small eye crop resolution (60×36) — limits fine-grained analysis
- Older collection (2015) — lower camera quality than modern webcams
- No glasses/contact lens annotations
- No lighting annotations

#### License
Creative Commons Attribution 4.0 (for academic use)  
**Commercial Use: No**

#### Preprocessing for EyeNav
```python
# Required transformations
# 1. Eye normalization (already applied in dataset)
# 2. Resize to 128×128 (upsample from 60×36)
# 3. Data augmentation: brightness, contrast, noise
# 4. Gaze vector normalization: normalize to unit sphere
# 5. Split: 14 subjects train / 1 subject test (leave-one-out)
```

#### EyeNav Compatibility
- **Module**: Gaze Estimation (training)
- **Role**: Foundational training set for appearance-based gaze model
- **Limitation**: Low diversity limits generalization — supplement with ETH-XGaze

---

### DS-002 — ETH-XGaze

**Full Name:** ETH Extended Gaze Dataset  
**Source:** ETH Zürich Computer Vision Lab  
**Paper:** Zhang, X., et al. (2020). ETH-XGaze: A Large Scale Dataset for Gaze Estimation Under Extreme Head Pose and Gaze Variation. ECCV 2020.  
**Download:** https://ait.ethz.ch/xgaze  

#### Description
Largest high-quality gaze dataset. Collected with a high-resolution camera system and includes extreme head poses and gaze targets. Critical for training appearance-based gaze models.

#### Dataset Statistics
| Property | Value |
|---|---|
| Total Images | 1,083,492 |
| Subjects | 110 (diverse ages, ethnicities) |
| Image Resolution | 6000×4000 (full face) |
| Eye Crop Resolution | 224×224 (high quality) |
| Video | No |
| Head Pose Range | ±80° yaw, ±80° pitch |
| Gaze Range | ±80° horizontal, ±80° vertical |
| 3D Gaze Labels | Yes |
| Head Pose Labels | Yes |

#### Annotation Types
- Gaze direction (3D unit vector, calibrated)
- Head pose (6-DOF)
- Facial landmarks (68 points)
- Normalized face images (ETH normalization)
- Lighting conditions (annotated)

#### Strengths
- Massive scale (1M+ images)
- Extreme head pose and gaze variation coverage
- High-quality 224×224 normalized eye crops
- Multi-ethnic subjects (though not perfectly balanced)
- State-of-the-art gaze models achieve 1.8° MAE on this dataset

#### Weaknesses
- Lab collection (controlled environment — less ecological validity)
- No glasses in dataset — significant limitation for EyeNav
- No fatigue annotation
- License restricts commercial training

#### License
Academic Non-Commercial Use Only  
**Commercial Use: No** (Research training only; derivative models may be used commercially per license terms — verify with ETH legal)

#### Preprocessing for EyeNav
```python
# 1. Use ETH normalization pipeline (provided with dataset)
# 2. Apply gaze augmentation: ±5° random perturbation
# 3. Glasses augmentation: overlay synthetic glasses on 30% of images
# 4. Split: 80/10/10 train/val/test (subject-independent)
```

#### EyeNav Compatibility
- **Module**: Gaze Estimation (primary training)
- **Role**: Primary benchmark and training dataset for L2CS-Net
- **Limitation**: No glasses — must augment

---

### DS-003 — GazeCapture

**Full Name:** GazeCapture (Eye Tracking for Everyone)  
**Source:** MIT / Apple  
**Paper:** Krafka, K., et al. (2016). Eye Tracking for Everyone. CVPR 2016.  
**Download:** https://gazecapture.csail.mit.edu/  

#### Description
First large-scale mobile gaze dataset collected via crowdsourcing. Subjects used iPhones/iPads to collect data through a dedicated iOS app.

#### Dataset Statistics
| Property | Value |
|---|---|
| Total Frames | ~2,500,000 |
| Subjects | 1,474 |
| Devices | iPhone, iPad (multiple models) |
| Ages | 5–75 (diverse) |
| Screen Distance | Variable (hand-held mobile) |
| Lighting | Uncontrolled (real-world) |
| Glasses | Naturally present (crowdsourced) |

#### Annotation Types
- 2D screen gaze coordinates (dot-following task)
- Face bounding box
- Eye bounding boxes
- Device pose (accelerometer)
- Device model

#### Strengths
- ✅ MIT License — **commercially usable**
- Largest subject pool (1,474) — best demographic diversity
- Real-world uncontrolled collection
- Mobile device variation
- Age diversity including children and elderly

#### Weaknesses
- Mobile-only (no desktop/laptop setting)
- iPhone front camera (~2–4MP, older models) — lower quality than modern webcams
- Only 2D screen gaze (no 3D gaze vectors)
- No head pose labels
- Crowdsourced = variable annotation quality

#### License
MIT License  
**Commercial Use: ✅ Yes**

#### EyeNav Compatibility
- **Module**: Gaze Estimation (mobile fine-tuning), training diversity
- **Role**: Critical for mobile deployment robustness and demographic diversity
- **Value**: Only large-scale commercially usable gaze dataset

---

### DS-004 — RT-GENE

**Full Name:** Real-Time Gaze Estimation in Natural Environments  
**Source:** Imperial College London  
**Paper:** Fischer, T., et al. (2018). RT-GENE: Real-Time Eye Gaze Estimation in Natural Environments. ECCV 2018.  
**Download:** https://zenodo.org/record/2529036  

#### Description
Collected with a mobile robot (ESMERALDA). The robot moves around interacting with subjects in natural environments. Includes both gaze estimation and head pose labels.

#### Dataset Statistics
| Property | Value |
|---|---|
| Total Images | 122,531 |
| Subjects | 15 |
| Collection | Mobile robot camera |
| Glasses | Mixed (some subjects wear glasses) |
| Gaze Labels | 3D |
| Blink Labels | Yes |

#### Annotation Types
- 3D gaze direction
- Head pose
- Eye blink ground truth
- Glasses annotation (binary)

#### Strengths
- Natural environments (not lab)
- Glasses annotation — valuable for EyeNav
- Blink labels (one of few datasets with blink GT)
- Multiple camera distances and angles

#### Weaknesses
- Robot-mounted camera introduces unusual viewpoints
- Only 15 subjects
- CC BY-NC-SA — research only

#### License
CC BY-NC-SA 4.0  
**Commercial Use: No**

#### EyeNav Compatibility
- **Module**: Gaze Estimation, Blink Detection
- **Role**: Blink ground truth for blink model training; glasses diversity supplement

---

### DS-005 — Eyeblink8

**Full Name:** Eyeblink8 Dataset  
**Source:** Brno University of Technology  
**Paper:** Drutarovsky, T., & Fogelton, A. (2014). Eye Blink Detection Using Variance of Motion Vectors.  
**Download:** http://www.fit.vutbr.cz/research/groups/graph/eyeblink8/  

#### Description
8 video sequences recorded for blink detection research. Each frame annotated with blink state.

#### Dataset Statistics
| Property | Value |
|---|---|
| Videos | 8 |
| Subjects | 4 |
| Total Frames | ~20,000 |
| Annotation | Per-frame: open/closed/beginning/ending |
| FPS | 25fps |
| Resolution | 640×480 |

#### Annotation Types
- Per-frame eye state: open, closing, closed, opening
- Blink events: onset, peak, offset frames

#### Strengths
- Precise temporal blink annotations
- Distinguishes blink phases (not just open/closed)
- Used as standard blink detection benchmark

#### Weaknesses
- Very small (4 subjects, 8 videos)
- Controlled environment
- No voluntary vs. involuntary distinction
- CC BY-NC-ND — no modifications allowed

#### License
CC BY-NC-ND 4.0  
**Commercial Use: No**

#### EyeNav Compatibility
- **Module**: Blink Detection (evaluation benchmark)
- **Role**: Cannot be modified, but serves as evaluation-only benchmark
- **Note**: Training set must come from other sources (RT-GENE, synthetic)

---

### DS-006 — OpenEDS 2019

**Full Name:** Open Eye Dataset (Facebook Reality Labs)  
**Source:** Facebook Reality Labs (Meta)  
**Paper:** Garbin, S.J., et al. (2019). OpenEDS: Open Eye Dataset. arXiv 2019.  
**Download:** https://research.fb.com/programs/openeds-challenge/  

#### Description
Collected from VR headset cameras (eye-facing cameras in Oculus Rift). Contains semantic segmentation labels for eye regions.

#### Dataset Statistics
| Property | Value |
|---|---|
| Images | 12,759 (labeled) + 252,690 (unlabeled) |
| Subjects | 152 |
| Collection Device | Oculus Rift (eye-facing IR camera) |
| Annotation | Pixel-level segmentation |
| Segments | Pupil, iris, sclera, background |

#### Annotation Types
- Pixel-level segmentation maps: pupil (1), iris (2), sclera (3), background (0)
- Gaze direction (for subset)
- Blink events (for subset)

#### Strengths
- Pixel-level eye segmentation — unique in scale
- Diverse subjects (152)
- Enables eye component segmentation models
- Near-infrared images (IR camera)

#### Weaknesses
- IR imagery (not RGB webcam) — domain gap
- VR context — very close camera-eye distance
- CC BY-NC — research only

#### License
CC BY-NC 4.0  
**Commercial Use: No**

#### EyeNav Compatibility
- **Module**: Eye Segmentation, Pupil Localization
- **Role**: Training data for eye region segmentation models (after domain adaptation from IR to RGB)

---

### DS-007 — UnityEyes

**Full Name:** UnityEyes Synthetic Gaze Dataset  
**Source:** University of Oxford  
**Paper:** Wood, E., et al. (2016). Learning an Appearance-Based Gaze Estimator from One Million Synthesised Images. ETRA 2016.  
**Download:** https://www.cl.cam.ac.uk/research/rainbow/projects/unityeyes/  

#### Description
One million photorealistic synthetic eye images generated using Unity 3D with ground truth gaze, landmarks, and blink state. Created specifically for training gaze estimation models.

#### Dataset Statistics
| Property | Value |
|---|---|
| Images | 1,000,000 |
| Subjects | Synthetic (diverse appearance) |
| Gaze Labels | Full 3D gaze vectors |
| Landmark Labels | 18 eye landmarks |
| Blink Labels | Yes |
| Lighting | 100+ lighting configurations |
| Glasses | Yes (virtual) |
| Resolution | 120×80 (eye crops) |

#### Annotation Types
- 3D gaze direction (ground truth)
- Eye region landmarks
- Blink state
- Lighting direction
- Glasses on/off

#### Strengths
- ✅ CC BY 4.0 — **commercially usable**
- 1M images with perfect ground truth (no annotation error)
- Includes glasses variations
- Diverse lighting conditions
- Infinite generation possible (Unity scene available)

#### Weaknesses
- Synthetic → real domain gap (photorealism is good but not perfect)
- No iris color diversity (limited to 3D model skins)
- Older generation (2016) — newer synthetic tools superior
- Must use domain adaptation when training on UnityEyes for real cameras

#### License
CC BY 4.0  
**Commercial Use: ✅ Yes**

#### EyeNav Compatibility
- **Module**: Gaze Estimation (data augmentation), Blink Detection (augmentation)
- **Role**: Supplement real data; especially valuable for rare conditions (glasses, extreme poses)
- **Strategy**: Mix 30% UnityEyes with real data; apply domain adaptation

---

## Preprocessing Pipeline

### Standard Preprocessing for All Gaze Datasets

```python
class GazeDatasetPreprocessor:
    """
    Standard preprocessing pipeline for EyeNav gaze training datasets.
    
    Normalization follows the protocol of Zhang et al. (2018):
    "Revisiting Data Normalization for Appearance-Based Gaze Estimation"
    """
    
    def normalize_gaze(self, gaze_3d: np.ndarray) -> np.ndarray:
        """
        Apply camera normalization to face/eye images for appearance-based gaze.
        
        Steps:
        1. Rotate head to face camera (rectify face orientation)
        2. Scale to standard distance (d=60cm)
        3. Extract normalized eye patch
        
        Returns: normalized eye patch (128×128) + normalized gaze vector
        """
        ...
    
    def apply_augmentation(self, image: np.ndarray) -> np.ndarray:
        """
        Apply data augmentation for training robustness.
        
        Augmentations:
        - Brightness: ±30% random
        - Contrast: ±20% random
        - Gaussian noise: σ~U(0, 0.02)
        - Random erasing: 10% probability (simulate occlusion)
        """
        ...
```

---

## Dataset Strategy Summary

### Phase 1 (Current) — Research Training
Use: ETH-XGaze (primary) + MPIIGaze + GazeCapture + RT-GENE + UnityEyes

### Phase 2 — Intent Training
Use: EyeNav Proprietary Dataset (see [DATASET_SPEC.md](../custom/DATASET_SPEC.md))

### Phase 3 — Commercial Deployment
Use: GazeCapture (MIT) + UnityEyes (CC-BY) + EyeNav Proprietary

All research-only datasets (ETH-XGaze, MPIIGaze, etc.) used for training only — derivative models are not considered derivative works under their licenses (verify with legal counsel before commercial release).

---

## References

1. Zhang, X., et al. (2015). Appearance-Based Gaze Estimation in the Wild. CVPR 2015.
2. Zhang, X., et al. (2020). ETH-XGaze. ECCV 2020.
3. Krafka, K., et al. (2016). Eye Tracking for Everyone. CVPR 2016.
4. Fischer, T., et al. (2018). RT-GENE. ECCV 2018.
5. Wood, E., et al. (2016). UnityEyes. ETRA 2016.
6. Garbin, S.J., et al. (2019). OpenEDS. arXiv.
7. Zhang, X., et al. (2018). Revisiting Data Normalization for Appearance-Based Gaze Estimation. ETRA 2018.
