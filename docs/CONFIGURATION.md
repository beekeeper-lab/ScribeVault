# Configuration System Implementation

## Overview

ScribeVault now supports configurable transcription services with comprehensive cost estimation, allowing users to choose between OpenAI API and local Whisper processing based on their needs and budget.

## Features Implemented

### 1. Configuration Management (`src/config/settings.py`)
- **SettingsManager**: JSON-based configuration persistence
- **CostEstimator**: Detailed cost analysis and service comparison
- Automatic configuration file creation with sensible defaults
- Environment-based API key management

### 2. Enhanced Whisper Service (`src/transcription/whisper_service.py`)
- **Dual Mode Support**: OpenAI API and local Whisper models
- **Graceful Fallback**: Handles missing local packages elegantly
- **Device Detection**: Automatic CPU/CUDA detection for optimal performance
- **Model Selection**: Support for all Whisper model sizes (tiny to large)

### 3. Settings UI (`src/gui/qt_settings_dialog.py`)
- **Cost Comparison**: Side-by-side service comparison with detailed metrics
- **Visual Cost Breakdown**: Per-minute and per-hour cost estimates
- **System Information**: Hardware detection and availability status
- **Service Configuration**: Easy switching between API and local modes

### 4. Main Application Integration
- Updated main window with settings integration
- Dynamic service reinitialization when settings change
- Theme application from settings

## Cost Analysis

| Service | Cost per Minute | Cost per Hour | Annual Cost (1hr/day) |
|---------|----------------|---------------|----------------------|
| **OpenAI API** | $0.0060 | $0.36 | $131.40 |
| **Local Whisper** | $0.0001 | $0.01 | $3.65 |
| **Savings** | $0.0059 (98.3%) | $0.35 | $127.75 |

## Service Comparison

### OpenAI API
**Advantages:**
- ✅ Zero setup required
- ✅ Consistent performance
- ✅ No hardware requirements
- ✅ Latest model improvements
- ✅ Reliable service availability

**Considerations:**
- ⚠️ Ongoing costs ($0.006/minute)
- ⚠️ Requires internet connection
- ⚠️ Data sent to external service
- ⚠️ Rate limits apply

### Local Whisper
**Advantages:**
- ✅ Nearly free operation (~$0.0001/minute)
- ✅ Complete privacy (no data sharing)
- ✅ No internet required after setup
- ✅ No rate limits
- ✅ Multiple model sizes available

**Considerations:**
- ⚠️ Initial setup required (dependencies)
- ⚠️ Hardware requirements (CPU/RAM/GPU)
- ⚠️ Variable processing speed
- ⚠️ Storage space for models (39MB-3GB)

## Installation Guide

### For OpenAI API (Current Default)
1. Set environment variable: `export OPENAI_API_KEY="your-key-here"`
2. Already configured and ready to use

### For Local Whisper Processing
1. Install dependencies:
   ```bash
   pip install whisper>=1.1.10 torch>=2.0.0 numpy>=1.24.0
   ```

2. Configure in Settings:
   - Open ScribeVault Settings (⚙️ button)
   - Change "Transcription Service" to "local"
   - Select desired model size
   - Choose processing device (auto/cpu/cuda)
   - Save settings

## Hardware Requirements

### Minimum (CPU-only)
- **RAM**: 4GB+ available
- **Storage**: 1GB+ free space
- **CPU**: Modern multi-core processor
- **Model**: tiny/base recommended

### Recommended (GPU acceleration)
- **RAM**: 8GB+ available
- **VRAM**: 2GB+ dedicated graphics memory
- **GPU**: CUDA-compatible (NVIDIA)
- **Model**: small/medium for best balance

### High-performance
- **RAM**: 16GB+ available
- **VRAM**: 4GB+ dedicated graphics memory
- **GPU**: Modern NVIDIA RTX series
- **Model**: large for maximum accuracy

## Model Sizes and Performance

| Model | Size | VRAM | Speed | Accuracy | Best Use Case |
|-------|------|------|-------|----------|---------------|
| **tiny** | 39MB | ~1GB | Fastest | Good | Quick drafts, real-time |
| **base** | 74MB | ~1GB | Fast | Better | General use, good balance |
| **small** | 244MB | ~2GB | Medium | Very Good | Most applications |
| **medium** | 769MB | ~5GB | Slower | Excellent | Professional use |
| **large** | 1550MB | ~10GB | Slowest | Best | Maximum accuracy needed |

## Testing the System

Run the configuration test:
```bash
python test_config.py
```

Expected output:
- ✅ Settings management working
- ✅ Cost calculations accurate
- ✅ Service comparison data
- ✅ Local Whisper availability check
- ✅ Settings persistence verified

## Configuration Files

### Settings Location
- **File**: `config/settings.json`
- **Auto-created**: Yes, with defaults
- **Format**: Human-readable JSON

### Default Configuration
```json
{
  "transcription": {
    "service": "openai",
    "language": "auto",
    "local_model": "base",
    "device": "auto"
  },
  "summarization": {
    "service": "openai",
    "model": "gpt-4o-mini",
    "max_tokens": 150
  },
  "ui": {
    "theme": "dark",
    "auto_save": true
  }
}
```

## Migration Path

### Current Users (OpenAI API)
- No action required
- Existing functionality unchanged
- Can explore local option in Settings

### New Users
- Choose preferred service during setup
- Cost comparison helps decision making
- Easy switching between services

## Future Enhancements

### Planned Features
1. **Hybrid Mode**: Automatic service selection based on audio duration
2. **Cost Tracking**: Monitor actual usage and costs over time
3. **Model Caching**: Intelligent local model management
4. **Batch Processing**: Optimize local processing for multiple files
5. **Quality Comparison**: Side-by-side accuracy testing

### Additional Services
1. **Azure Speech Services**: Alternative cloud provider
2. **Google Speech-to-Text**: Another API option
3. **Custom Models**: User-trained Whisper variants

## Troubleshooting

### Local Whisper Issues
1. **Import Errors**: Run `pip install whisper torch`
2. **CUDA Errors**: Check GPU drivers and CUDA installation
3. **Memory Errors**: Try smaller model size or close other applications
4. **Slow Performance**: Consider GPU acceleration or smaller model

### API Issues
1. **Authentication**: Verify OPENAI_API_KEY environment variable
2. **Rate Limits**: Local processing has no limits
3. **Network**: Check internet connection for API services

### Settings Issues
1. **File Not Found**: Settings auto-recreate with defaults
2. **Invalid JSON**: Backup and reset to defaults
3. **Permission Errors**: Check write access to config directory
