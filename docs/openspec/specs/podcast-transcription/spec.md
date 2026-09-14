# podcast-transcription Specification

## Purpose

Define verifiable, versioned transcript and WAV artifacts that preserve audio provenance and can resume after transfer between computers.

## Requirements

### Requirement: Generate traceable transcripts
The CLI SHALL transcribe verified local MP3 or M4A files using an explicitly selected MLX or faster-whisper backend and produce UTF-8 TXT, timestamped SRT and JSON containing raw segment text, display text, source SHA-256, model content fingerprint, engine version, language, generation time and reviewed=false. It SHALL preserve the spoken language and perform Traditional Chinese conversion only when requested. Invalid or nonfinite segment timestamps SHALL fail without a completion manifest.

#### Scenario: Traditional Chinese output
- **WHEN** the backend returns Simplified Chinese and Traditional output is requested
- **THEN** JSON preserves raw text and TXT/SRT use converted text, with reviewed=false


<!-- @trace
source: add-batch-collection-transcripts
updated: 2026-09-11
code:
  - content/README.md
  - Dockerfile
  - docs/research/2026-09-11-portable-validation.md
  - docs/research/README.md
  - podcasts.toml
  - .dockerignore
  - compose.yaml
  - docs/research/2026-09-11-downloader-validation.md
  - storysonic/catalog.py
  - compose.drive.yaml
  - README.md
  - requirements-cpu.lock
  - storysonic/engines.py
  - storysonic/processing.py
  - storysonic/__init__.py
  - storysonic/drive.py
  - Makefile
  - scripts/package.py
  - storysonic/__main__.py
  - uv.lock
  - scripts/install-gws.py
  - storysonic/download.py
  - pyproject.toml
  - scripts/run-mac.sh
  - docs/README.md
  - docs/deployment/README.md
  - scripts/setup-mac.sh
  - AGENTS.md
tests:
  - tests/test_engines.py
  - tests/test_companions.py
  - tests/test_deployment.py
  - tests/test_processing.py
  - tests/test_drive.py
  - tests/test_portable.py
  - tests/test_download.py
  - tests/test_cli.py
  - tests/test_catalog.py
-->

---
### Requirement: Resume portable derived artifacts
The CLI SHALL identify derived results by source hash and recipe, keep relative paths under content, verify every output hash before skipping, rebuild incomplete or corrupt results, and retain separate versions for changed recipes. Completion metadata SHALL be written last. An interrupted episode SHALL be restarted on rerun while verified completed episodes SHALL be skipped.

#### Scenario: Move to another computer
- **WHEN** content and identical model files are moved to a different absolute path and the same command is rerun
- **THEN** verified results are skipped without calling the ASR engine


<!-- @trace
source: add-batch-collection-transcripts
updated: 2026-09-11
code:
  - content/README.md
  - Dockerfile
  - docs/research/2026-09-11-portable-validation.md
  - docs/research/README.md
  - podcasts.toml
  - .dockerignore
  - compose.yaml
  - docs/research/2026-09-11-downloader-validation.md
  - storysonic/catalog.py
  - compose.drive.yaml
  - README.md
  - requirements-cpu.lock
  - storysonic/engines.py
  - storysonic/processing.py
  - storysonic/__init__.py
  - storysonic/drive.py
  - Makefile
  - scripts/package.py
  - storysonic/__main__.py
  - uv.lock
  - scripts/install-gws.py
  - storysonic/download.py
  - pyproject.toml
  - scripts/run-mac.sh
  - docs/README.md
  - docs/deployment/README.md
  - scripts/setup-mac.sh
  - AGENTS.md
tests:
  - tests/test_engines.py
  - tests/test_companions.py
  - tests/test_deployment.py
  - tests/test_processing.py
  - tests/test_drive.py
  - tests/test_portable.py
  - tests/test_download.py
  - tests/test_cli.py
  - tests/test_catalog.py
-->

---
### Requirement: Convert without replacing source audio
The convert command SHALL create 16 kHz mono PCM WAV from verified local audio, preserve original bytes, record the source SHA and conversion recipe, and reuse only verified outputs.

#### Scenario: Decoder failure
- **WHEN** ffmpeg fails on an episode
- **THEN** the CLI reports failure and does not create a completed conversion record

<!-- @trace
source: add-batch-collection-transcripts
updated: 2026-09-11
code:
  - content/README.md
  - Dockerfile
  - docs/research/2026-09-11-portable-validation.md
  - docs/research/README.md
  - podcasts.toml
  - .dockerignore
  - compose.yaml
  - docs/research/2026-09-11-downloader-validation.md
  - storysonic/catalog.py
  - compose.drive.yaml
  - README.md
  - requirements-cpu.lock
  - storysonic/engines.py
  - storysonic/processing.py
  - storysonic/__init__.py
  - storysonic/drive.py
  - Makefile
  - scripts/package.py
  - storysonic/__main__.py
  - uv.lock
  - scripts/install-gws.py
  - storysonic/download.py
  - pyproject.toml
  - scripts/run-mac.sh
  - docs/README.md
  - docs/deployment/README.md
  - scripts/setup-mac.sh
  - AGENTS.md
tests:
  - tests/test_engines.py
  - tests/test_companions.py
  - tests/test_deployment.py
  - tests/test_processing.py
  - tests/test_drive.py
  - tests/test_portable.py
  - tests/test_download.py
  - tests/test_cli.py
  - tests/test_catalog.py
-->