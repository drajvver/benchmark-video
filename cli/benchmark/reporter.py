"""JSON result generation and formatting."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from benchmark.encoder import EncodeResult
from benchmark.presets import BENCHMARK_VERSION
from benchmark.system import SystemInfo


def generate_report(
    system_info: SystemInfo,
    encode_results: List[EncodeResult],
) -> dict:
    """Generate a standardized benchmark report."""
    return {
        "benchmark_version": BENCHMARK_VERSION,
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": {
            "os": system_info.os,
            "os_version": system_info.os_version,
            "arch": system_info.arch,
            "cpu_model": system_info.cpu_model,
            "cpu_cores": system_info.cpu_cores,
            "cpu_threads": system_info.cpu_threads,
            "ram_gb": system_info.ram_gb,
            "is_virtualized": system_info.is_virtualized,
            "virtualization_platform": system_info.virtualization_platform,
        },
        "results": [
            {
                "video": r.video,
                "codec": r.codec,
                "preset": r.preset,
                "crf": r.crf,
                "encode_time_seconds": r.encode_time_seconds,
                "fps": r.fps,
                "output_size_mb": r.output_size_mb,
            }
            for r in encode_results
        ],
    }


def save_report(report: dict, path: Path) -> None:
    """Save report to a JSON file."""
    with open(path, "w") as f:
        json.dump(report, f, indent=2)


def load_report(path: Path) -> dict:
    """Load a report from a JSON file."""
    with open(path) as f:
        return json.load(f)
