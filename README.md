# Video Encoding Benchmark Platform

A universal video encoding benchmarking platform with a cross-platform CLI tool and a web-based leaderboard.

## Project Structure

```
.
├── cli/           # Python CLI benchmark tool
├── web/           # Web application
│   ├── backend/   # FastAPI + PostgreSQL
│   └── frontend/  # React + Vite + Tailwind
├── docker-compose.yml
└── README.md
```

## Quick Start

### CLI Tool

```bash
cd cli
uv pip install -e .
video-benchmark info       # Show system info
video-benchmark run        # Run benchmark
video-benchmark run --quick  # Quick mode (1080p only)
```

### Web Application

```bash
docker compose up -d
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## Supported Platforms

- Linux (x64, ARM64)
- macOS (x64, ARM64)
- Windows (x64, ARM64)

## Supported Codecs

- H.264 (x264)
- H.265 (x265)
- VP9
- AV1 (SVT-AV1)

## Features

- **Virtualization Detection**: Automatically detects if running in a VM
- **Standardized Results**: Fixed CRF/preset settings for fair comparison
- **Anonymous Uploads**: JWT token-based anti-spam
- **CPU Filtering**: Filter and compare results by CPU model
- **Leaderboards**: Aggregated stats with bare metal vs VM distinction
