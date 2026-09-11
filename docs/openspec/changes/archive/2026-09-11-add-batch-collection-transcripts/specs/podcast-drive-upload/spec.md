## ADDED Requirements

### Requirement: Upload verified transcript companions
The explicit include-transcripts option SHALL upload complete verified TXT, SRT and JSON artifacts under the configured podcaster/show/transcripts/episode/recipe hierarchy, preserving audio upload identity. The uploader SHALL query artifact identity before create, reject duplicates and conflicts, verify remote size and MD5 by readback, and record success only after verification. Missing completed transcripts SHALL produce a nonzero error when inclusion is requested.

#### Scenario: Repeat companion upload
- **WHEN** the same completed transcript is uploaded again
- **THEN** existing matching files are verified and skipped without creating duplicates or confusing the original audio lookup
