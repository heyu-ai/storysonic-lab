## ADDED Requirements

### Requirement: Deploy on Apple Silicon and Docker
The repository SHALL provide an installable CLI, a native Apple Silicon MLX setup script, a CPU Docker image and Compose configuration with external config, content and model-cache paths. Images and source archives SHALL exclude credentials, downloaded media, models and local virtual environments. Docker uploads SHALL consume credentials only through an explicitly mounted file.

#### Scenario: Fresh installation
- **WHEN** a user installs on a supported Mac or builds the CPU image
- **THEN** help and list commands run without downloading a model and deployment instructions specify a one-episode smoke run

### Requirement: Run observable resumable batches
Work commands SHALL accept exactly one show or all configured shows, retain a default limit of three episodes per show, require explicit all for unlimited episodes, emit JSON progress and final counts, continue after individual episode or feed failure and return nonzero on any failure. They SHALL prevent concurrent writers to the same content root and stop before starting new work below a configurable positive free-space reserve. Dry-run SHALL perform no writes, model downloads, ASR or Drive requests.

#### Scenario: One feed fails
- **WHEN** all-shows is selected and one feed is unavailable
- **THEN** remaining shows are processed and final status is nonzero

#### Scenario: Stop and move
- **WHEN** a running worker receives SIGINT or SIGTERM
- **THEN** it stops without treating partial results as complete and releases its content lock
