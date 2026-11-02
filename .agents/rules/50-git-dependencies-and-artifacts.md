# Git, dependencies, and generated artefacts

- Inspect `git status --short` before edits and before committing. Preserve user changes; never reset, clean, or discard unknown files.
- Keep datasets, videos, face crops, checkpoints, caches, calibration profiles, run outputs, and environment-specific paths out of Git unless the maintainer explicitly decides otherwise and checks licensing/privacy/storage limits.
- Inspect existing ignore rules before adding new ones. Ignore only project-specific generated paths, not broad source patterns.
- Do not install or upgrade packages casually. Explain the need and verify supported Python/OS/CUDA combinations first.
- Keep `requirements.txt` for runtime dependencies and `requirements-dev.txt` for developer/test tools if that is the repository's existing convention.
- Do not introduce a second experiment tracker or configuration framework before checking whether the repository already has one. Start with a reproducible JSON/CSV report when sufficient.
- Never commit secrets, personal data, raw datasets, model weights of unclear origin, or artefacts with unknown licences.
