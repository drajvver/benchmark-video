"""Codec presets and benchmark configuration."""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class CodecPreset:
    name: str
    encoder: str
    crf_1080p: int
    crf_4k: int
    preset: str
    extra_flags: List[str]
    container: str = "mp4"


@dataclass(frozen=True)
class VideoSource:
    name: str
    resolution: str
    url: str
    sha256: str
    duration_seconds: int
    frames: int


# Standardized codec presets
CODEC_PRESETS: Dict[str, CodecPreset] = {
    "x264": CodecPreset(
        name="H.264 / x264",
        encoder="libx264",
        crf_1080p=23,
        crf_4k=24,
        preset="medium",
        extra_flags=["-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        container="mp4",
    ),
    "x265": CodecPreset(
        name="H.265 / x265",
        encoder="libx265",
        crf_1080p=28,
        crf_4k=30,
        preset="medium",
        extra_flags=["-pix_fmt", "yuv420p", "-tag:v", "hvc1", "-movflags", "+faststart"],
        container="mp4",
    ),
    "vp9": CodecPreset(
        name="VP9",
        encoder="libvpx-vp9",
        crf_1080p=31,
        crf_4k=33,
        preset="2",
        extra_flags=["-row-mt", "1", "-pix_fmt", "yuv420p", "-deadline", "good", "-cpu-used", "2"],
        container="webm",
    ),
    "av1": CodecPreset(
        name="AV1 / SVT-AV1",
        encoder="libsvtav1",
        crf_1080p=35,
        crf_4k=38,
        preset="6",
        extra_flags=["-pix_fmt", "yuv420p"],
        container="mp4",
    ),
}

VIDEO_SOURCES: Dict[str, VideoSource] = {
    "tos-1080p": VideoSource(
        name="Tears of Steel 1080p",
        resolution="1080p",
        url="https://bn-stream-e2e.b-cdn.net/tos_bench.mov",
        sha256="",
        duration_seconds=31,
        frames=722,
    ),
    "bbb-1080p": VideoSource(
        name="Big Buck Bunny 1080p",
        resolution="1080p",
        url="https://bn-stream-e2e.b-cdn.net/bbb.mp4",
        sha256="",
        duration_seconds=60,
        frames=1800,
    ),
    "game-1080p": VideoSource(
        name="Game 60fps",
        resolution="1080p",
        url="https://bn-stream-e2e.b-cdn.net/1080/game1_1920x1080_60.mkv",
        sha256="",
        duration_seconds=5,
        frames=300,
    ),
    "tos-4k": VideoSource(
        name="Tears of Steel 4K",
        resolution="4k",
        url="",  # To be filled when hosting final assets
        sha256="",
        duration_seconds=60,
        frames=1440,
    ),
}

BENCHMARK_VERSION = "1.0.0"
