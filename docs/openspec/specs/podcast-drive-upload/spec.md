# podcast-drive-upload Specification

## Purpose

Define explicit uploads of verified local podcast audio into a chosen Google Drive folder, organized by podcaster and show with remote integrity checks and duplicate prevention.

## Requirements

### Requirement: Route uploads by podcaster

The uploader SHALL accept a Google Drive folder ID or folder URL, verify the writable destination folder, and organize files into podcaster and show subfolders using stable configured IDs in their names. It SHALL support shared-drive metadata and paginated child lookup. Ambiguous duplicate folders SHALL cause an error without choosing an arbitrary destination.

#### Scenario: Shared-drive destination
- **WHEN** the root folder belongs to a shared drive
- **THEN** metadata and file operations use shared-drive support and create or reuse the matching podcaster and show folders beneath that root


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
### Requirement: Verify uploads and avoid duplicates

The uploader SHALL verify the local file against its manifest before network writes, identify remote episodes with appProperties, and verify remote size and MD5 using metadata readback. Matching existing files SHALL be skipped. Conflicting content or duplicate episode matches SHALL fail without overwriting or deleting remote data. Successful or skipped uploads SHALL record their remote ID and verified time in the local manifest only after readback succeeds.

#### Scenario: Retry after uncertain upload outcome
- **WHEN** a prior upload created the remote file but did not save local upload status
- **THEN** a retry finds and verifies the remote file and reports skipped without creating another copy

#### Scenario: Remote mismatch
- **WHEN** the matching remote episode has a different MD5 or size
- **THEN** the command returns an error and leaves the existing remote file unchanged


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
### Requirement: Explicit upload and observable failures

Downloading SHALL NOT upload unless the user supplies the upload option. A separate upload command SHALL operate on verified local manifests. Drive integration SHALL use the authenticated gws CLI through argument arrays, without storing credentials in the repository. Missing credentials, permission errors, timeouts and verification failures SHALL produce nonzero status and SHALL NOT record upload success. Dry-run SHALL NOT invoke gws.

#### Scenario: Authentication failure
- **WHEN** gws reports invalid_grant
- **THEN** the CLI reports the authentication failure with re-login guidance and preserves the local download for retry

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
### Requirement: Upload verified transcript companions
The explicit include-transcripts option SHALL upload complete verified TXT, SRT and JSON artifacts under the configured podcaster/show/transcripts/episode/recipe hierarchy, preserving audio upload identity. The uploader SHALL query artifact identity before create, reject duplicates and conflicts, verify remote size and MD5 by readback, and record success only after verification. Missing completed transcripts SHALL produce a nonzero error when inclusion is requested.

#### Scenario: Repeat companion upload
- **WHEN** the same completed transcript is uploaded again
- **THEN** existing matching files are verified and skipped without creating duplicates or confusing the original audio lookup

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