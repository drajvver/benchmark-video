"""FFmpeg execution and benchmark encoding logic."""

import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Callable

from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn

from benchmark.presets import CodecPreset, VideoSource
from benchmark.probe import VideoProbe


@dataclass
class EncodeResult:
    video: str
    codec: str
    preset: str
    crf: int
    encode_time_seconds: float
    fps: float
    output_size_mb: float


def find_ffmpeg() -> str:
    """Find bundled or system ffmpeg binary."""
    # Check bundled ffmpeg first (relative to executable)
    exe_dir = Path(__file__).parent.parent
    bundled_names = {
        "Linux": "ffmpeg",
        "Darwin": "ffmpeg",
        "Windows": "ffmpeg.exe",
    }
    import platform
    bundled_name = bundled_names.get(platform.system(), "ffmpeg")
    bundled_path = exe_dir / "bin" / bundled_name
    if bundled_path.exists():
        return str(bundled_path)
    
    # Fall back to system PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    
    raise FileNotFoundError(
        "ffmpeg not found. Please ensure ffmpeg is bundled or installed on your system."
    )


def verify_encoders(codecs: Optional[List[str]] = None) -> List[str]:
    """Verify that required ffmpeg encoders are available.
    
    Returns a list of missing encoder names. Empty list means all OK.
    """
    from benchmark.presets import CODEC_PRESETS
    
    ffmpeg_path = find_ffmpeg()
    selected = {k: v for k, v in CODEC_PRESETS.items() if not codecs or k in codecs}
    
    try:
        result = subprocess.run(
            [ffmpeg_path, "-encoders"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        encoders_output = result.stdout
    except Exception:
        return [p.encoder for p in selected.values()]
    
    missing = []
    for key, preset in selected.items():
        if preset.encoder not in encoders_output:
            missing.append(preset.encoder)
    
    return missing


def parse_ffmpeg_progress(line: str) -> Optional[float]:
    """Extract current time from ffmpeg stderr progress line."""
    # Look for time=HH:MM:SS.ms or time=SS.ms
    match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
    if match:
        h, m, s = match.groups()
        return int(h) * 3600 + int(m) * 60 + float(s)
    match = re.search(r"time=(\d+\.\d+)", line)
    if match:
        return float(match.group(1))
    return None


def parse_ffmpeg_fps(line: str) -> Optional[float]:
    """Extract FPS from ffmpeg stderr."""
    match = re.search(r"fps=\s*(\d+(?:\.\d+)?)", line)
    if match:
        return float(match.group(1))
    return None


def build_ffmpeg_args(
    ffmpeg_path: str,
    input_path: Path,
    output_path: Path,
    preset: CodecPreset,
    crf: int,
) -> List[str]:
    """Build ffmpeg command arguments."""
    args = [
        ffmpeg_path,
        "-y",
        "-i", str(input_path),
        "-c:v", preset.encoder,
        "-preset", preset.preset,
        "-crf", str(crf),
    ]
    
    # VP9 uses -crf differently (0-63), but libvpx-vp9 does accept -crf
    # SVT-AV1 uses -crf (0-63)
    # x264/x265 use -crf (0-51)
    
    args.extend(preset.extra_flags)
    args.append(str(output_path))
    return args


def run_benchmark_encode(
    input_path: Path,
    preset: CodecPreset,
    crf: int,
    video_source: VideoSource,
    video_probe: VideoProbe,
    progress_callback: Optional[Callable[[float, float], None]] = None,
) -> EncodeResult:
    """Run a single benchmark encode and return metrics."""
    ffmpeg_path = find_ffmpeg()
    
    # Create output file
    safe_name = video_source.name.replace(" ", "_").replace("/", "_")
    output_path = Path(tempfile.gettempdir()) / f"benchmark_{safe_name}_{preset.encoder}_{crf}.{preset.container}"
    
    args = build_ffmpeg_args(ffmpeg_path, input_path, output_path, preset, crf)
    
    start_time = time.monotonic()
    
    process = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    
    # Parse stderr for progress
    last_time = 0.0
    last_fps = 0.0
    duration = video_probe.duration_seconds if video_probe.duration_seconds > 0 else video_source.duration_seconds
    if process.stderr:
        for line in process.stderr:
            t = parse_ffmpeg_progress(line)
            if t is not None:
                last_time = t
            fps = parse_ffmpeg_fps(line)
            if fps is not None:
                last_fps = fps
            if progress_callback and duration > 0:
                progress = min(last_time / duration, 1.0)
                progress_callback(progress, last_fps)
    
    returncode = process.wait()
    encode_time = time.monotonic() - start_time
    
    if returncode != 0:
        if output_path.exists():
            output_path.unlink()
        raise RuntimeError(f"ffmpeg encode failed with return code {returncode}")
    
    output_size_mb = 0.0
    if output_path.exists():
        output_size_mb = output_path.stat().st_size / (1024 * 1024)
        output_path.unlink()
    
    # Calculate average FPS using probed frame count
    frames = video_probe.frames if video_probe.frames > 0 else video_source.frames
    avg_fps = frames / encode_time if encode_time > 0 else 0.0
    
    return EncodeResult(
        video=video_source.name,
        codec=preset.name,
        preset=preset.preset,
        crf=crf,
        encode_time_seconds=round(encode_time, 2),
        fps=round(avg_fps, 2),
        output_size_mb=round(output_size_mb, 2),
    )


def run_full_benchmark(
    input_paths: dict[str, Path],
    video_probes: dict[str, VideoProbe],
    codecs: Optional[List[str]] = None,
    quick_mode: bool = False,
) -> List[EncodeResult]:
    """Run benchmarks for all configured video/codec combinations."""
    from benchmark.presets import CODEC_PRESETS, VIDEO_SOURCES
    
    if codecs:
        selected_presets = {k: v for k, v in CODEC_PRESETS.items() if k in codecs}
    else:
        selected_presets = CODEC_PRESETS
    
    results: List[EncodeResult] = []
    
    # Build run list
    runs = []
    for video_key, video in VIDEO_SOURCES.items():
        if quick_mode and video.resolution != "1080p":
            continue
        for codec_key, preset in selected_presets.items():
            crf = preset.crf_1080p if video.resolution == "1080p" else preset.crf_4k
            runs.append((video_key, video, codec_key, preset, crf))
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("{task.fields[fps]:.1f} fps"),
    ) as progress:
        for video_key, video, codec_key, preset, crf in runs:
            input_path = input_paths.get(video_key)
            probe = video_probes.get(video_key)
            if not input_path or not input_path.exists():
                continue
            if not probe:
                continue
            
            task = progress.add_task(
                f"[cyan]{video.name}[/] → [green]{preset.name}[/]",
                total=1.0,
                fps=0.0,
            )
            
            def cb(p: float, fps: float):
                progress.update(task, completed=p, fps=fps)
            
            try:
                result = run_benchmark_encode(input_path, preset, crf, video, probe, cb)
                results.append(result)
                progress.update(task, completed=1.0, fps=result.fps)
            except Exception as e:
                progress.update(task, completed=1.0, fps=0.0)
                print(f"[red]Failed: {video.name} with {preset.name}: {e}[/]")
    
    return results
