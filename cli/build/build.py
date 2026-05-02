#!/usr/bin/env python3
"""Cross-platform build script for video-benchmark CLI.

Downloads static ffmpeg binaries and builds a single executable via PyInstaller.
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).parent.parent.resolve()
BIN_DIR = REPO_ROOT / "bin"

# Static ffmpeg download URLs (BtbN = full codecs including SVT-AV1)
FFMPEG_DOWNLOADS = {
    "linux-x64": {
        "url": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz",
        "archive": "tar.xz",
        "extract": "tar",
        "strip": 0,
        "binaries": ["ffmpeg", "ffprobe"],
    },
    "linux-arm64": {
        "url": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz",
        "archive": "tar.xz",
        "extract": "tar",
        "strip": 0,
        "binaries": ["ffmpeg", "ffprobe"],
    },
    "macos-x64": {
        "url": "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
        "archive": "zip",
        "extract": "zip",
        "strip": 0,
        "binaries": ["ffmpeg", "ffprobe"],
        "extra_urls": {
            "ffprobe": "https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip",
        },
    },
    "macos-arm64": {
        "url": "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip",
        "archive": "zip",
        "extract": "zip",
        "strip": 0,
        "binaries": ["ffmpeg", "ffprobe"],
        "extra_urls": {
            "ffprobe": "https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip",
        },
    },
    "windows-x64": {
        "url": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
        "archive": "zip",
        "extract": "zip",
        "strip": 0,
        "binaries": ["ffmpeg.exe", "ffprobe.exe"],
    },
    "windows-arm64": {
        "url": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
        "archive": "zip",
        "extract": "zip",
        "strip": 0,
        "binaries": ["ffmpeg.exe", "ffprobe.exe"],
    },
}


def get_target() -> str:
    """Auto-detect target platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "darwin":
        system = "macos"
    if machine in ("amd64", "x86_64"):
        machine = "x64"
    elif machine in ("arm64", "aarch64"):
        machine = "arm64"
    return f"{system}-{machine}"


def download_file(url: str, dest: Path) -> None:
    """Download a file with simple progress."""
    print(f"Downloading: {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=300) as response:
        total = int(response.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 65536
        with open(dest, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    mb = downloaded // 1024 // 1024
                    total_mb = total // 1024 // 1024
                    print(f"\r  {pct}% ({mb} / {total_mb} MB)", end="", flush=True)
    print()


def extract_archive(archive: Path, dest: Path, method: str) -> None:
    """Extract an archive."""
    print(f"Extracting {archive.name}...")
    dest.mkdir(parents=True, exist_ok=True)
    if method == "tar":
        subprocess.run(["tar", "-xf", str(archive), "-C", str(dest)], check=True)
    elif method == "zip":
        with zipfile.ZipFile(archive, "r") as z:
            z.extractall(dest)
    print("Done extracting.")


def find_files(root: Path, names: list[str]) -> dict[str, Path]:
    """Find binaries recursively."""
    found = {}
    for name in names:
        for path in root.rglob(name):
            if path.is_file() and os.access(path, os.X_OK):
                found[name] = path
                break
    return found


def download_ffmpeg(target: str) -> None:
    """Download and extract ffmpeg for the target platform."""
    if target not in FFMPEG_DOWNLOADS:
        raise ValueError(f"Unsupported target: {target}. Supported: {list(FFMPEG_DOWNLOADS.keys())}")

    info = FFMPEG_DOWNLOADS[target]
    cache_dir = REPO_ROOT / ".build_cache"
    cache_dir.mkdir(exist_ok=True)

    archive_name = f"ffmpeg-{target}.{info['archive']}"
    archive_path = cache_dir / archive_name

    if not archive_path.exists():
        download_file(info["url"], archive_path)
    else:
        print(f"Using cached: {archive_path}")

    extract_dir = cache_dir / f"ffmpeg-{target}"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_archive(archive_path, extract_dir, info["extract"])

    binaries = find_files(extract_dir, info["binaries"])

    # Download extra binaries (e.g., ffprobe from separate URL on macOS)
    for extra_name, extra_url in info.get("extra_urls", {}).items():
        if extra_name in binaries:
            continue
        extra_archive = cache_dir / f"ffmpeg-{target}-{extra_name}.{info['archive']}"
        if not extra_archive.exists():
            download_file(extra_url, extra_archive)
        extra_extract = cache_dir / f"ffmpeg-{target}-{extra_name}"
        if extra_extract.exists():
            shutil.rmtree(extra_extract)
        extract_archive(extra_archive, extra_extract, info["extract"])
        extra_found = find_files(extra_extract, [extra_name])
        binaries.update(extra_found)

    missing = set(info["binaries"]) - set(binaries.keys())
    if missing:
        raise FileNotFoundError(f"Could not find binaries: {missing}")

    BIN_DIR.mkdir(exist_ok=True)
    for name, src in binaries.items():
        dest = BIN_DIR / name
        shutil.copy2(src, dest)
        os.chmod(dest, 0o755)
        print(f"  -> {dest}")


def build_binary(target: str, onefile: bool = True) -> None:
    """Build the executable with PyInstaller."""
    print(f"\nBuilding video-benchmark for {target}...")

    system = platform.system()
    ffmpeg_binary = "ffmpeg.exe" if system == "Windows" else "ffmpeg"
    ffmpeg_path = BIN_DIR / ffmpeg_binary

    if not ffmpeg_path.exists():
        print("Downloading static ffmpeg...")
        download_ffmpeg(target)

    # Verify we have the required binaries
    required = ["ffmpeg", "ffprobe"] if system != "Windows" else ["ffmpeg.exe", "ffprobe.exe"]
    for name in required:
        if not (BIN_DIR / name).exists():
            print(f"WARNING: {name} not found in {BIN_DIR}")

    separator = ";" if system == "Windows" else ":"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "video-benchmark",
        "--clean",
        "--noconfirm",
    ]
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    if (REPO_ROOT / "bin").exists():
        cmd.extend(["--add-data", f"bin{separator}bin"])
    if (REPO_ROOT / "assets").exists():
        cmd.extend(["--add-data", f"assets{separator}assets"])

    cmd.append(str(REPO_ROOT / "benchmark" / "main.py"))

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=REPO_ROOT, env=env, check=True)

    dist_dir = REPO_ROOT / "dist"
    print(f"\nBuild complete. Output: {dist_dir}")


def package(target: str) -> None:
    """Package the built binary into a zip."""
    dist_dir = REPO_ROOT / "dist"
    system = platform.system().lower()
    binary_name = "video-benchmark.exe" if system == "windows" else "video-benchmark"
    binary = dist_dir / binary_name

    if not binary.exists():
        raise FileNotFoundError(f"Binary not found: {binary}")

    zip_name = f"video-benchmark-{target}.zip"
    zip_path = dist_dir / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(binary, binary_name)
    size_mb = zip_path.stat().st_size // 1024 // 1024
    print(f"Packaged: {zip_path} ({size_mb} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build video-benchmark CLI")
    parser.add_argument("--target", default=get_target(), help="Target platform")
    parser.add_argument("--download-ffmpeg", action="store_true", help="Only download ffmpeg")
    parser.add_argument("--no-onefile", action="store_true", help="Build as directory")
    parser.add_argument("--package", action="store_true", help="Package into zip")
    args = parser.parse_args()

    if args.download_ffmpeg:
        download_ffmpeg(args.target)
        return

    build_binary(args.target, onefile=not args.no_onefile)

    if args.package:
        package(args.target)


if __name__ == "__main__":
    main()
