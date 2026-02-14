# ScribeVault

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![GUI: PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://doc.qt.io/qtforpython/)

A desktop application for audio recording, transcription, and intelligent summarization with cost-optimized processing.

<!-- TODO: Add screenshot of main window here -->

## Features

- **Audio Recording** — Record from microphone with real-time level feedback, PyAudio with FFmpeg fallback, and checkpoint recovery for crash protection
- **Dual Transcription** — Choose between OpenAI Whisper API (cloud) or local Whisper models (offline, free)
- **Speaker Diarization** — Automatic speaker identification using audio clustering, with manual speaker labeling and renaming
- **AI Summarization** — Generate concise, detailed, or bullet-point summaries using OpenAI GPT models
- **Prompt Templates** — Built-in and custom prompt templates for re-summarizing recordings with different focus areas
- **Auto-Categorization** — GPT-powered automatic categorization of recordings (meeting, interview, lecture, note, call, presentation)
- **Export System** — Export transcriptions as plain text, Markdown, or SRT subtitle files with metadata
- **Vault Management** — SQLite-backed vault for organizing, searching, browsing, and managing recordings
- **Cost Optimization** — Real-time cost comparison between API and local processing, with per-minute and annual projections
- **Secure API Key Storage** — System keyring integration with encrypted fallback (Fernet/PBKDF2), never stored in plaintext
- **Theming** — Dark, light, and system theme support via Settings UI

## Architecture

ScribeVault follows a modular pipeline architecture. Each stage is independent and retryable.

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Record    │───▶│   Transcribe     │───▶│   Summarize     │───▶│  Vault Save  │
│ AudioRecorder│   │  WhisperService  │    │SummarizerService│    │ VaultManager │
└──────┬──────┘    └───────┬──────────┘    └────────┬────────┘    └──────┬───────┘
       │                   │                        │                    │
  Checkpoint          Diarization              Categorize            Export
  flush (WAV)      (DiarizationService)    (auto-category)     (TXT/MD/SRT)
```

### Module Responsibilities

| Module | Key Classes | Responsibility |
|--------|-------------|----------------|
| `src/audio/` | `AudioRecorder` | Recording via PyAudio or FFmpeg, periodic checkpoint flush for crash recovery, WAV output |
| `src/transcription/` | `WhisperService`, `DiarizationService`, `SpeakerService` | Whisper transcription (API or local), speaker diarization via audio clustering, speaker label parsing and renaming |
| `src/ai/` | `SummarizerService`, `PromptTemplateManager` | GPT summarization with configurable style, auto-categorization, custom prompt templates |
| `src/export/` | `TranscriptionExporter`, `MarkdownGenerator` | Export to TXT/MD/SRT formats, organized markdown summaries by date and category |
| `src/vault/` | `VaultManager` | SQLite database (WAL mode) for recording metadata, transcriptions, summaries, and pipeline state |
| `src/config/` | `SettingsManager`, `CostEstimator` | JSON-based settings, keyring/encrypted API key storage, model pricing and cost estimation |
| `src/gui/` | `ScribeVaultMainWindow`, `VaultDialog`, `SummaryViewerDialog`, `SettingsDialog`, `SpeakerPanel` | PySide6 UI with pipeline status panel, vault browser, summary viewer, settings, and speaker labeling |
| `src/utils/` | `retry_on_transient_error` | Retry decorator with exponential backoff for transient API errors |

### Processing Pipeline

1. **Record** — `AudioRecorder` captures audio via PyAudio (primary) or FFmpeg (fallback). During recording, audio frames are periodically flushed to a checkpoint WAV file (default: every 30 seconds). If the app crashes, `recover_checkpoints()` salvages partial recordings.

2. **Transcribe** — `WhisperService` sends the WAV file to OpenAI's Whisper API or processes it with a local Whisper model. If diarization is enabled, `DiarizationService` identifies speakers using audio feature extraction and hierarchical clustering (scipy), producing labeled segments.

3. **Summarize** — `SummarizerService` sends the transcript to OpenAI GPT for summarization (concise, detailed, or bullet-point style). `categorize_content()` auto-assigns a category. `PromptTemplateManager` enables re-summarization with custom or built-in templates (e.g., "Action Items", "Key Decisions").

4. **Store & Export** — `VaultManager` saves the recording, transcription, summary, and metadata to SQLite. `TranscriptionExporter` exports to TXT, Markdown, or SRT. `MarkdownGenerator` organizes summary files into `summaries/daily/` and `summaries/by-category/` directories.

## Quick Start

### Prerequisites

- **Python 3.8+**
- **FFmpeg** (required for audio processing)
- **PortAudio** (required for microphone recording)

Install system dependencies:

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg portaudio19-dev

# macOS
brew install ffmpeg portaudio

# Windows
choco install ffmpeg
# PortAudio is bundled with the PyAudio wheel on Windows
```

### Installation

```bash
git clone https://github.com/beekeeper-lab/ScribeVault.git
cd ScribeVault

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Alternatively, use the automated installer:

```bash
python3 install.py
```

Or platform-specific scripts: `./setup.sh` (Linux/macOS) or `setup.bat` (Windows).

### Running

```bash
python main.py
```

### API Key Setup

ScribeVault stores API keys securely in your system keyring — **not** in `.env` files.

1. Launch the app: `python main.py`
2. Open **Settings** (gear icon)
3. Enter your OpenAI API key in the API Key field
4. Click **Save** — the key is stored in your system keyring (macOS Keychain, Windows Credential Manager, or Linux Secret Service)

If keyring is unavailable, the key is encrypted with Fernet (PBKDF2-derived key) and stored in the config directory. The app also reads `OPENAI_API_KEY` from the environment as a read-only fallback.

**Local-only mode:** If you only use local Whisper models for transcription and don't need AI summarization, no API key is required.

## Configuration

All configuration is managed through the **Settings UI** (gear icon in the toolbar). Settings are saved to `config/settings.json`.

| Setting | Options | Default |
|---------|---------|---------|
| Transcription service | `openai` (cloud) / `local` (offline) | `local` |
| Local Whisper model | `tiny`, `base`, `small`, `medium`, `large` | `base` |
| Compute device | `auto`, `cpu`, `cuda` | `auto` |
| Summarization model | `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo` | `gpt-4o-mini` |
| Summary style | `concise`, `detailed`, `bullet_points` | `concise` |
| Theme | `dark`, `light`, `system` | `dark` |
| Diarization | Enable/disable, speaker count (auto or 2-6), sensitivity | Enabled, auto |
| Audio preset | `voice`, `standard`, `high_quality` | `standard` |
| Checkpoint interval | 10–300 seconds | 30 seconds |

### Cost Comparison

| Service | Cost/Hour | Annual (1hr/day) |
|---------|-----------|------------------|
| Local Whisper | $0.00 | $0.00 |
| OpenAI Whisper API | ~$0.36 | ~$131 |

Summarization costs depend on the GPT model selected. The Settings UI shows real-time cost estimates.

## Usage

### Basic Workflow

1. Click **Start Recording** to begin capturing audio
2. Click **Stop Recording** when finished
3. The transcription appears automatically (with speaker labels if diarization is enabled)
4. If summarization is enabled, an AI summary is generated
5. The recording is saved to the vault

### Vault

Open the **Vault** dialog to browse, search, and manage recordings:

- **View** — Full transcription, summary, and metadata
- **Edit** — Modify title, description, and category
- **Delete** — Remove recordings with confirmation
- **Play Audio** — Listen to the original recording
- **Export** — Save as TXT, Markdown, or SRT
- **Re-transcribe / Re-summarize** — Regenerate with different settings or prompt templates

### Speaker Labels

When diarization is enabled, speakers are automatically identified (e.g., "Speaker 1", "Speaker 2"). Use the **Speaker Panel** to rename speakers to real names.

## Developer Guide

### Dev Environment Setup

```bash
git clone https://github.com/beekeeper-lab/ScribeVault.git
cd ScribeVault

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run a specific test file
pytest tests/test_vault_manager.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html for the report
```

### Code Quality

```bash
# Lint
flake8 src/ tests/

# Format
black src/ tests/
isort src/ tests/

# Type check
mypy src/
```

### Test Categories

| Category | Files | What it tests |
|----------|-------|---------------|
| Audio | `test_audio_recorder.py`, `test_audio_settings.py`, `test_checkpoint.py` | Recording, settings presets, checkpoint recovery |
| Transcription | `test_whisper_service.py`, `test_diarization.py`, `test_speaker_service.py` | Whisper API/local, diarization, speaker labels |
| Summarization | `test_summarizer.py`, `test_prompt_templates.py` | GPT summarization, prompt template management |
| Vault | `test_vault_manager.py`, `test_vault_delete_export.py` | SQLite CRUD, delete, export operations |
| Export | `test_transcription_exporter.py`, `test_export_utils.py`, `test_export_file_organization.py` | TXT/MD/SRT export, file security utilities |
| Security | `test_api_key_validation.py`, `test_path_validation.py`, `test_html_escape.py`, `test_secure_permissions.py` | API key validation, path traversal, HTML escaping, file permissions |
| Config | `test_cost_estimator.py`, `test_settings_diagnostics.py`, `test_logging_config.py` | Cost estimation, diagnostics, logging |
| Integration | `test_integration.py`, `test_retry.py`, `test_retry_integration.py` | End-to-end workflows, retry logic |
| UI | `test_pipeline_status.py`, `test_main_page_speaker.py`, `test_on_demand_processing.py` | Pipeline status tracking, speaker panel, on-demand re-processing |

## Project Structure

```
ScribeVault/
├── main.py                          # Application entry point
├── src/
│   ├── audio/
│   │   └── recorder.py              # AudioRecorder (PyAudio/FFmpeg, checkpoints)
│   ├── transcription/
│   │   ├── whisper_service.py        # WhisperService (API + local)
│   │   ├── diarization.py            # DiarizationService (speaker clustering)
│   │   └── speaker_service.py        # Speaker label parsing and renaming
│   ├── ai/
│   │   ├── summarizer.py             # SummarizerService (GPT summarization)
│   │   └── prompt_templates.py       # PromptTemplateManager (custom templates)
│   ├── export/
│   │   ├── transcription_exporter.py # Export to TXT, Markdown, SRT
│   │   ├── markdown_generator.py     # Organized markdown summaries
│   │   └── utils.py                  # Secure file operations
│   ├── vault/
│   │   └── manager.py                # VaultManager (SQLite storage)
│   ├── config/
│   │   ├── settings.py               # SettingsManager, CostEstimator
│   │   └── logging_config.py         # Logging setup
│   ├── gui/
│   │   ├── qt_main_window.py         # ScribeVaultMainWindow
│   │   ├── qt_app.py                 # Qt application setup
│   │   ├── qt_vault_dialog.py        # VaultDialog (vault browser)
│   │   ├── qt_summary_viewer.py      # SummaryViewerDialog
│   │   ├── qt_settings_dialog.py     # SettingsDialog
│   │   ├── speaker_panel.py          # SpeakerPanel (label editing)
│   │   ├── pipeline_status.py        # PipelineStatus tracking
│   │   ├── pipeline_status_panel.py  # Pipeline status UI panel
│   │   └── settings_diagnostics.py   # System diagnostics
│   ├── utils/
│   │   └── retry.py                  # Retry decorator with backoff
│   └── assets/                       # UI assets and resources
├── config/                           # User configuration files
├── tests/                            # pytest test suite
├── docs/                             # Documentation
│   └── CONFIGURATION.md              # Detailed configuration guide
├── requirements.txt                  # Production dependencies
└── requirements-test.txt             # Testing/dev dependencies
```

## Security

ScribeVault implements defense-in-depth security:

- **API Key Storage** — System keyring (primary), Fernet-encrypted config with PBKDF2-derived key (fallback), environment variable (read-only). Keys are never stored in plaintext files.
- **Path Validation** — All file operations validate paths against a base directory to prevent directory traversal attacks.
- **SQL Injection Prevention** — All database queries use parameterized statements (`?` placeholders). No string interpolation in SQL.
- **HTML Escaping** — Speaker names and transcription text are escaped before rendering in HTML views to prevent XSS.
- **File Permissions** — Sensitive files (vault database, config, checkpoints) are created with restrictive permissions (`0o600`/`0o700` on POSIX systems).
- **Input Sanitization** — Null bytes and unsafe characters are stripped from filenames and user input.

See [SECURITY.md](SECURITY.md) for the full security policy and reporting instructions.

## Troubleshooting

**Audio recording fails:**
- Verify your microphone is connected and not muted
- Check that PortAudio is installed (`portaudio19-dev` on Debian/Ubuntu)
- The app falls back to FFmpeg recording if PyAudio fails — ensure FFmpeg is installed
- Run `ffmpeg -version` to verify FFmpeg is in your PATH

**FFmpeg not found:**
- Install FFmpeg for your platform (see [Prerequisites](#prerequisites))
- Restart your terminal after installation so PATH updates take effect

**Local Whisper out of memory:**
- Use a smaller model (`tiny` or `base`) in Settings
- For GPU acceleration, install CUDA-compatible PyTorch: `pip install torch --index-url https://download.pytorch.org/whl/cu118`
- Close other memory-intensive applications

**API connection errors:**
- Open Settings and verify your API key is saved (the key source is displayed)
- Check your internet connection
- Ensure your OpenAI account has available quota

**Checkpoint recovery:**
- If the app crashed during recording, restart it — `AudioRecorder.recover_checkpoints()` automatically scans for orphaned checkpoint files and recovers them as playable WAV files

**Import errors on startup:**
- Ensure you activated the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style guidelines, and the pull request process.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
