## ADDED Requirements

### Requirement: Select podcast episodes

The CLI SHALL load configured shows, parse bounded HTTP(S) RSS feeds, deduplicate GUIDs, sort by publication date newest first, and apply title substring filtering followed by a positive limit of three by default or explicit all selection. Missing dates SHALL sort last. The CLI SHALL reject DTD/entity declarations, invalid show IDs and unsupported URL schemes.

#### Scenario: Filter and limit
- **WHEN** episodes dated September 1 and September 3 match the requested title and limit is one
- **THEN** only the September 3 episode is selected

#### Scenario: Explicit scope
- **WHEN** the user supplies limit zero or both limit and all
- **THEN** the CLI exits nonzero without downloading audio

### Requirement: Download complete MP3 files

The downloader SHALL stream MP3 enclosures into temporary files under content/podcaster-id/show-id, enforce the configured positive size limit and HTTP Content-Length, reject non-audio responses, and expose completed files only after validation. It SHALL remove incomplete temporary files on failure and retry GET at most three times. One failed episode SHALL cause nonzero batch status while allowing other selected episodes to finish.

#### Scenario: Interrupted transfer
- **WHEN** an MP3 response ends before its Content-Length
- **THEN** no completed MP3 or success manifest is created

### Requirement: Preserve download provenance and idempotency

Each complete download SHALL have a versioned manifest containing source URL, GUID, episode metadata, download timestamp, byte count, SHA-256, MD5 and a local basename. Repeating a download SHALL verify the existing file size and SHA-256 before skipping it; a corrupt file SHALL be downloaded again. Paths SHALL remain within the configured content root and symlink targets SHALL be rejected. The CLI SHALL prevent concurrent writes to the same content root using a process lock.

#### Scenario: Repeat a verified download
- **WHEN** an existing file matches its manifest size and SHA-256
- **THEN** the command reports skipped and performs no audio GET

### Requirement: Preview and exclude local media from Git

Dry-run SHALL show selected operations without content writes or Drive calls. Git ignore rules SHALL exclude generated content and MP3 files throughout the repository while retaining the content README. Unknown shows and empty selections SHALL produce actionable nonzero errors.

#### Scenario: Preview download and upload
- **WHEN** download is invoked with dry-run and upload enabled
- **THEN** the output describes the destination without creating files or invoking gws
