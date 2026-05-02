"""FFprobe-based video probing."""

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VideoProbe:
    width: int
    height: int
    duration_seconds: float
    frames: int
    fps: float
    codec: str
    pix_fmt: str


def find_ffprobe() -> str:
    """Find ffprobe binary."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        return ffprobe
    # Check bundled location relative to this file
    exe_dir = Path(__file__).parent.parent
    bundled = exe_dir / "bin" / "ffprobe"
    if bundled.exists():
        return str(bundled)
    raise FileNotFoundError("ffprobe not found")


def probe_video(path: Path) -> VideoProbe:
    """Probe a video file for its properties."""
    ffprobe = find_ffprobe()
    cmd = [
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name,pix_fmt,r_frame_rate,nb_frames",
        "-show_entries", "format=duration",
        "-of", "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    data = json.loads(result.stdout)
    stream = data["streams"][0]
    fmt = data.get("format", {})

    width = int(stream.get("width", 0))
    height = int(stream.get("height", 0))
    duration = float(fmt.get("duration", stream.get("duration", 0)))

    # Parse frame count
    nb_frames = stream.get("nb_frames")
    if nb_frames and str(nb_frames).isdigit():
        frames = int(nb_frames)
    else:
        # Estimate from duration * fps
        fps = _parse_fps(stream.get("r_frame_rate", "0/1"))
        frames = int(duration * fps) if fps > 0 else 0

    fps = _parse_fps(stream.get("r_frame_rate", "0/1"))

    return VideoProbe(
        width=width,
        height=height,
        duration_seconds=duration,
        frames=frames,
        fps=fps,
        codec=stream.get("codec_name", "unknown"),
        pix_fmt=stream.get("pix_fmt", "unknown"),
    )


def _parse_fps(r_frame_rate: str) -> float:
    """Parse ffmpeg r_frame_rate string like '24000/1001'."""
    if "/" in r_frame_rate:
        num, den = r_frame_rate.split("/")
        return float(num) / float(den) if float(den) != 0 else 0.0
    return float(r_frame_rate)
