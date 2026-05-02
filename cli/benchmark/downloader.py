"""Video and asset download/caching."""

import hashlib
import os
import platform as sys_platform
from pathlib import Path
from typing import Dict, Optional

import requests
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn

from benchmark.presets import VideoSource


def get_cache_dir() -> Path:
    """Get platform-appropriate cache directory."""
    system = sys_platform.system()
    if system == "Linux":
        base = os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")
        return Path(base) / "video-benchmark"
    elif system == "Darwin":
        return Path.home() / "Library" / "Caches" / "video-benchmark"
    elif system == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "video-benchmark" / "Cache"
    else:
        return Path.home() / ".cache" / "video-benchmark"


def verify_checksum(path: Path, expected_sha256: str) -> bool:
    """Verify file SHA-256 checksum."""
    if not expected_sha256:
        return True  # Skip if no checksum provided
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest().lower() == expected_sha256.lower()


def download_file(
    url: str,
    dest: Path,
    description: str = "Downloading",
) -> None:
    """Download a file with resume support and progress bar."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    headers = {}
    existing_size = 0
    if dest.exists():
        existing_size = dest.stat().st_size
        headers["Range"] = f"bytes={existing_size}-"
    
    response = requests.get(url, headers=headers, stream=True, timeout=30)
    response.raise_for_status()
    
    total_size = int(response.headers.get("content-length", 0))
    if "content-range" in response.headers:
        # Resume: total is in the Content-Range header
        content_range = response.headers["content-range"]
        total_size = int(content_range.split("/")[1])
    else:
        total_size += existing_size
    
    mode = "ab" if existing_size > 0 else "wb"
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
    ) as progress:
        task = progress.add_task(description, total=total_size)
        progress.update(task, completed=existing_size)
        
        with open(dest, mode) as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    progress.advance(task, len(chunk))


def download_video(
    video: VideoSource,
    force: bool = False,
) -> Path:
    """Download and cache a benchmark video."""
    cache_dir = get_cache_dir()
    filename = Path(video.url).name or f"{video.name.replace(' ', '_')}.mp4"
    dest = cache_dir / filename
    
    if dest.exists() and not force:
        if verify_checksum(dest, video.sha256):
            return dest
        else:
            dest.unlink()
    
    if not video.url:
        raise ValueError(f"No URL configured for video: {video.name}")
    
    download_file(video.url, dest, f"Downloading {video.name}")
    
    if not verify_checksum(dest, video.sha256):
        dest.unlink()
        raise ValueError(f"Checksum mismatch for {video.name}")
    
    return dest


def download_all_videos(
    videos: Dict[str, VideoSource],
    quick_mode: bool = False,
    force: bool = False,
) -> Dict[str, Path]:
    """Download all required videos and return paths."""
    paths = {}
    for key, video in videos.items():
        if quick_mode and video.resolution != "1080p":
            continue
        try:
            paths[key] = download_video(video, force=force)
        except Exception as e:
            print(f"[red]Failed to download {video.name}: {e}[/]")
    return paths
