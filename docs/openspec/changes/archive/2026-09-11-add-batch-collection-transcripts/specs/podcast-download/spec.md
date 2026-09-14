## ADDED Requirements

### Requirement: Collect M4A enclosures
The catalog and downloader SHALL include audio/mp4, audio/m4a and audio/x-m4a enclosures in addition to MP3. M4A downloads SHALL retain their MP4 container and .m4a extension, pass media header, Content-Length and size checks, and use the same provenance and retry contract as MP3. Existing v1 MP3 manifests SHALL remain readable. Git ignore rules SHALL exclude MP3, M4A and generated WAV media throughout the repository.

#### Scenario: M4A episode
- **WHEN** a feed includes an audio/x-m4a enclosure with a valid ftyp header
- **THEN** the downloader saves a verified .m4a file and records audio/mp4 as its media type
