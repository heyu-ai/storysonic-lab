## ADDED Requirements

### Requirement: Route uploads by podcaster

The uploader SHALL accept a Google Drive folder ID or folder URL, verify the writable destination folder, and organize files into podcaster and show subfolders using stable configured IDs in their names. It SHALL support shared-drive metadata and paginated child lookup. Ambiguous duplicate folders SHALL cause an error without choosing an arbitrary destination.

#### Scenario: Shared-drive destination
- **WHEN** the root folder belongs to a shared drive
- **THEN** metadata and file operations use shared-drive support and create or reuse the matching podcaster and show folders beneath that root

### Requirement: Verify uploads and avoid duplicates

The uploader SHALL verify the local file against its manifest before network writes, identify remote episodes with appProperties, and verify remote size and MD5 using metadata readback. Matching existing files SHALL be skipped. Conflicting content or duplicate episode matches SHALL fail without overwriting or deleting remote data. Successful or skipped uploads SHALL record their remote ID and verified time in the local manifest only after readback succeeds.

#### Scenario: Retry after uncertain upload outcome
- **WHEN** a prior upload created the remote file but did not save local upload status
- **THEN** a retry finds and verifies the remote file and reports skipped without creating another copy

#### Scenario: Remote mismatch
- **WHEN** the matching remote episode has a different MD5 or size
- **THEN** the command returns an error and leaves the existing remote file unchanged

### Requirement: Explicit upload and observable failures

Downloading SHALL NOT upload unless the user supplies the upload option. A separate upload command SHALL operate on verified local manifests. Drive integration SHALL use the authenticated gws CLI through argument arrays, without storing credentials in the repository. Missing credentials, permission errors, timeouts and verification failures SHALL produce nonzero status and SHALL NOT record upload success. Dry-run SHALL NOT invoke gws.

#### Scenario: Authentication failure
- **WHEN** gws reports invalid_grant
- **THEN** the CLI reports the authentication failure with re-login guidance and preserves the local download for retry
