# Dataset License, Provenance, and Ethical Safeguards

**Document Date:** October 29, 2026  
**Dataset:** MIT GazeCapture (`archive.zip`)  
**Auditor:** Antigravity (AI Coding Assistant)  

---

## 1. Provenance & Citation

The dataset is derived from the landmark academic dataset **GazeCapture**:

- **Title:** Eye Tracking for Everyone
- **Authors:** Kyle Krafka, Aditya Khosla, Petr Kellnhofer, Harini Kannan, Suchendra Bhandarkar, Wojciech Matusik, Antonio Torralba
- **Affiliation:** Massachusetts Institute of Technology (MIT CSAIL) & University of Georgia
- **Publication:** IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2016
- **Website:** https://gazecapture.csail.mit.edu/
- **Repository / Kaggle Origin:** Mirror of the official GazeCapture dataset packaged as `archive.zip` (263 subjects, 348,643 frames).

---

## 2. Licensing Terms

- **License:** **MIT License**
- **Commercial Usability:** ✅ **Permitted**. Unlike academic-only datasets (e.g. MPIIGaze, ETH-XGaze, RT-GENE which are CC BY-NC), MIT GazeCapture is released under the permissive MIT License, enabling both research and commercial application development.
- **Redistribution:** Permitted with attribution notice.

---

## 3. Ethical Safeguards and Privacy Protocols

1. **Informed Consent:** Original participants consented to mobile front-camera recording during visual dot-tracking tasks via Amazon Mechanical Turk.
2. **Local Storage Guarantee:**
   - Raw face frames (`.jpg`) and facial crops must remain strictly local on disk.
   - Raw frames, eye crops, subject identifiers, and coordinates must **never** be committed to Git or pushed to any external cloud repository.
   - Raw frames must **never** be sent to third-party APIs, LLM endpoints, or external cloud vision services.
3. **Derived Model Governance:**
   - Preprocessing scripts and feature extraction pipelines must store only mathematical embeddings, landmark coordinates, and model weights in version-controlled or exportable artifacts.
   - Individual facial images must not be bundled into published model packages.

