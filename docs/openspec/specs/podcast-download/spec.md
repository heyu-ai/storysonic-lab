# podcast-download Specification

## Purpose

Define bounded selection and verified local collection of public podcast MP3 and M4A episodes, preserving source provenance and enabling safe repeat runs without committing media to Git.

## Requirements

### Requirement: Select podcast episodes

The CLI SHALL load configured shows, parse bounded HTTP(S) RSS feeds, deduplicate GUIDs, sort by publication date newest first, and apply title substring filtering followed by a positive limit of three by default or explicit all selection. Missing dates SHALL sort last. The CLI SHALL reject DTD/entity declarations, invalid show IDs and unsupported URL schemes.

#### Scenario: Filter and limit
- **WHEN** episodes dated September 1 and September 3 match the requested title and limit is one
- **THEN** only the September 3 episode is selected

#### Scenario: Explicit scope
- **WHEN** the user supplies limit zero or both limit and all
- **THEN** the CLI exits nonzero without downloading audio


<!-- @trace
source: add-podcast-download-drive
updated: 2026-09-11
code:
  - docs/research/2026-09-11-downloader-validation.md
  - content/README.md
  - podcasts.toml
  - storysonic/catalog.py
  - storysonic/download.py
  - docs/research/README.md
  - storysonic/drive.py
  - AGENTS.md
  - storysonic/__main__.py
  - README.md
  - storysonic/__init__.py
  - Makefile
  - pyproject.toml
tests:
  - tests/test_catalog.py
  - tests/test_download.py
  - tests/test_drive.py
  - tests/test_cli.py
-->

---
### Requirement: Download complete MP3 files

The downloader SHALL stream MP3 enclosures into temporary files under content/podcaster-id/show-id, enforce the configured positive size limit and HTTP Content-Length, reject non-audio responses, and expose completed files only after validation. It SHALL remove incomplete temporary files on failure and retry GET at most three times. One failed episode SHALL cause nonzero batch status while allowing other selected episodes to finish.

#### Scenario: Interrupted transfer
- **WHEN** an MP3 response ends before its Content-Length
- **THEN** no completed MP3 or success manifest is created


<!-- @trace
source: add-podcast-download-drive
updated: 2026-09-11
code:
  - docs/research/2026-09-11-downloader-validation.md
  - content/README.md
  - podcasts.toml
  - storysonic/catalog.py
  - storysonic/download.py
  - docs/research/README.md
  - storysonic/drive.py
  - AGENTS.md
  - storysonic/__main__.py
  - README.md
  - storysonic/__init__.py
  - Makefile
  - pyproject.toml
tests:
  - tests/test_catalog.py
  - tests/test_download.py
  - tests/test_drive.py
  - tests/test_cli.py
-->

---
### Requirement: Preserve download provenance and idempotency

Each complete download SHALL have a versioned manifest containing source URL, GUID, episode metadata, download timestamp, byte count, SHA-256, MD5 and a local basename. Repeating a download SHALL verify the existing file size and SHA-256 before skipping it; a corrupt file SHALL be downloaded again. Paths SHALL remain within the configured content root and symlink targets SHALL be rejected. The CLI SHALL prevent concurrent writes to the same content root using a process lock.

#### Scenario: Repeat a verified download
- **WHEN** an existing file matches its manifest size and SHA-256
- **THEN** the command reports skipped and performs no audio GET


<!-- @trace
source: add-podcast-download-drive
updated: 2026-09-11
code:
  - docs/research/2026-09-11-downloader-validation.md
  - content/README.md
  - podcasts.toml
  - storysonic/catalog.py
  - storysonic/download.py
  - docs/research/README.md
  - storysonic/drive.py
  - AGENTS.md
  - storysonic/__main__.py
  - README.md
  - storysonic/__init__.py
  - Makefile
  - pyproject.toml
tests:
  - tests/test_catalog.py
  - tests/test_download.py
  - tests/test_drive.py
  - tests/test_cli.py
-->

---
### Requirement: Preview and exclude local media from Git

Dry-run SHALL show selected operations without content writes or Drive calls. Git ignore rules SHALL exclude generated content and MP3 files throughout the repository while retaining the content README. Unknown shows and empty selections SHALL produce actionable nonzero errors.

#### Scenario: Preview download and upload
- **WHEN** download is invoked with dry-run and upload enabled
- **THEN** the output describes the destination without creating files or invoking gws

<!-- @trace
source: add-podcast-download-drive
updated: 2026-09-11
code:
  - docs/research/2026-09-11-downloader-validation.md
  - content/README.md
  - podcasts.toml
  - storysonic/catalog.py
  - storysonic/download.py
  - docs/research/README.md
  - storysonic/drive.py
  - AGENTS.md
  - storysonic/__main__.py
  - README.md
  - storysonic/__init__.py
  - Makefile
  - pyproject.toml
tests:
  - tests/test_catalog.py
  - tests/test_download.py
  - tests/test_drive.py
  - tests/test_cli.py
-->

---
### Requirement: Collect M4A enclosures
The catalog and downloader SHALL include audio/mp4, audio/m4a and audio/x-m4a enclosures in addition to MP3. M4A downloads SHALL retain their MP4 container and .m4a extension, pass media header, Content-Length and size checks, and use the same provenance and retry contract as MP3. Existing v1 MP3 manifests SHALL remain readable. Git ignore rules SHALL exclude MP3, M4A and generated WAV media throughout the repository.

#### Scenario: M4A episode
- **WHEN** a feed includes an audio/x-m4a enclosure with a valid ftyp header
- **THEN** the downloader saves a verified .m4a file and records audio/mp4 as its media type

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