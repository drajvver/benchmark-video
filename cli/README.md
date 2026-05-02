# Video Benchmark CLI

Universal video encoding benchmark tool. Measures CPU encoding performance across x264, x265, VP9, and AV1 (SVT-AV1).

## Quick Start (Binary)

Download the pre-built binary for your platform from [GitHub Releases](https://github.com/yourusername/benchmark-video/releases):

```bash
# Linux / macOS
curl -L -o video-benchmark.zip "https://github.com/yourusername/benchmark-video/releases/latest/download/video-benchmark-linux-x64.zip"
unzip video-benchmark.zip
chmod +x video-benchmark
./video-benchmark info
./video-benchmark run

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://github.com/yourusername/benchmark-video/releases/latest/download/video-benchmark-windows-x64.zip" -OutFile "video-benchmark.zip"
Expand-Archive -Path "video-benchmark.zip" -DestinationPath "."
.\video-benchmark.exe info
.\video-benchmark.exe run
```

Binaries are fully self-contained — no ffmpeg installation required.

## Install from PyPI

For Python users who prefer `pip`:

```bash
pip install video-benchmark
video-benchmark info
video-benchmark run
```

> **Note:** The PyPI package requires ffmpeg to be installed separately or available in your PATH.

## Supported Platforms

| Platform | x64 | ARM64 |
|----------|-----|-------|
| Linux    | ✅  | ✅    |
| macOS    | ✅  | ✅    |
| Windows  | ✅  | 🚧    |

## Usage

```bash
# Show system information
video-benchmark info

# Run full benchmark (all codecs, all videos)
video-benchmark run

# Quick mode — 1080p videos only
video-benchmark run --quick

# Run specific codecs only
video-benchmark run --quick --codec x264,x265

# Save result to file instead of uploading
video-benchmark run --quick -o result.json

# Upload a saved result
video-benchmark upload result.json --server https://your-server.com

# Pre-download videos without encoding
video-benchmark download
```

## Building from Source

```bash
cd cli
pip install -r requirements.txt
pip install pyinstaller
python build/build.py --package
```

The build script automatically downloads static ffmpeg binaries and creates a single executable in `dist/`.

## Configuration

Videos are downloaded on first run and cached:
- Linux: `~/.cache/video-benchmark/`
- macOS: `~/Library/Caches/video-benchmark/`
- Windows: `%LOCALAPPDATA%\video-benchmark\Cache\`
