#!/usr/bin/env python3
"""Video Encoding Benchmark CLI — main entry point."""

import json
from pathlib import Path
from typing import List, Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from benchmark.downloader import download_all_videos
from benchmark.encoder import run_full_benchmark
from benchmark.presets import CODEC_PRESETS, VIDEO_SOURCES
from benchmark.probe import probe_video
from benchmark.reporter import generate_report, save_report
from benchmark.system import get_system_info
from benchmark.uploader import upload_file, upload_result

app = typer.Typer(
    name="video-benchmark",
    help="Universal video encoding benchmark tool",
    no_args_is_help=True,
)
console = Console()


@app.command()
def run(
    quick: bool = typer.Option(
        False, "--quick", help="Run only 1080p videos (faster)"
    ),
    codec: Optional[List[str]] = typer.Option(
        None, "--codec", help="Filter codecs (can be used multiple times)"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Save result to file instead of uploading"
    ),
    upload: bool = typer.Option(
        True, "--upload/--no-upload", help="Upload results to server after running"
    ),
    server: str = typer.Option(
        "http://localhost:8000", "--server", "-s", help="Server base URL"
    ),
    force_download: bool = typer.Option(
        False, "--force-download", help="Re-download videos even if cached"
    ),
) -> None:
    """Run the video encoding benchmark."""
    print("[bold blue]Video Encoding Benchmark[/bold blue]")
    print()

    # Gather system info
    print("[yellow]Gathering system information...[/]")
    system_info = get_system_info()
    print(f"  OS: {system_info.os} {system_info.os_version} ({system_info.arch})")
    print(f"  CPU: {system_info.cpu_model}")
    print(f"  Cores: {system_info.cpu_cores} / Threads: {system_info.cpu_threads}")
    print(f"  RAM: {system_info.ram_gb} GB")
    if system_info.is_virtualized:
        print(f"  [red]Virtualized: {system_info.virtualization_platform or 'unknown'}[/]")
    else:
        print("  [green]Bare metal[/]")
    print()

    # Validate and normalize codecs
    selected_codecs = None
    if codec:
        # Support both multiple --codec flags and comma-separated values
        flattened = []
        for c in codec:
            flattened.extend([x.strip() for x in c.split(",")])
        selected_codecs = flattened
        invalid = [c for c in selected_codecs if c not in CODEC_PRESETS]
        if invalid:
            print(f"[red]Invalid codec(s): {', '.join(invalid)}[/]")
            print(f"Available: {', '.join(CODEC_PRESETS.keys())}")
            raise typer.Exit(1)

    # Download videos
    print("[yellow]Checking video assets...[/]")
    input_paths = download_all_videos(VIDEO_SOURCES, quick_mode=quick, force=force_download)
    if not input_paths:
        print("[red]No video assets available. Cannot proceed.[/]")
        raise typer.Exit(1)
    
    # Probe downloaded videos
    print("[yellow]Probing video files...[/]")
    video_probes = {}
    for key, path in input_paths.items():
        try:
            probe = probe_video(path)
            video_probes[key] = probe
            print(f"  [green]{VIDEO_SOURCES[key].name}[/]: {probe.width}x{probe.height}, {probe.duration_seconds:.1f}s, {probe.frames} frames")
        except Exception as e:
            print(f"  [red]Failed to probe {VIDEO_SOURCES[key].name}: {e}[/]")
    print()

    # Run benchmarks
    print("[yellow]Running benchmarks...[/]")
    results = run_full_benchmark(input_paths, video_probes, codecs=selected_codecs, quick_mode=quick)
    print()

    if not results:
        print("[red]No benchmark results produced.[/]")
        raise typer.Exit(1)

    # Generate report
    report = generate_report(system_info, results)

    # Display results
    table = Table(title="Benchmark Results")
    table.add_column("Video", style="cyan")
    table.add_column("Codec", style="green")
    table.add_column("CRF", justify="right")
    table.add_column("Time (s)", justify="right")
    table.add_column("FPS", justify="right")
    table.add_column("Size (MB)", justify="right")

    for r in results:
        table.add_row(
            r.video,
            r.codec,
            str(r.crf),
            f"{r.encode_time_seconds:.1f}",
            f"{r.fps:.1f}",
            f"{r.output_size_mb:.1f}",
        )
    console.print(table)
    print()

    # Save/upload
    if output:
        save_report(report, output)
        print(f"[green]Report saved to {output}[/]")
    elif upload:
        success = upload_result(report, base_url=server)
        if not success:
            fallback = Path("benchmark_result.json")
            save_report(report, fallback)
            print(f"[yellow]Result saved locally to {fallback} for manual upload.[/]")
    else:
        print(json.dumps(report, indent=2))


@app.command()
def upload(
    path: Path = typer.Argument(..., help="Path to benchmark result JSON file"),
    server: str = typer.Option(
        "http://localhost:8000", "--server", "-s", help="Server base URL"
    ),
) -> None:
    """Upload a previously saved benchmark result."""
    if not path.exists():
        print(f"[red]File not found: {path}[/]")
        raise typer.Exit(1)
    success = upload_file(path, base_url=server)
    if not success:
        raise typer.Exit(1)


@app.command()
def info() -> None:
    """Display system information."""
    system_info = get_system_info()
    table = Table(title="System Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("OS", f"{system_info.os} {system_info.os_version}")
    table.add_row("Architecture", system_info.arch)
    table.add_row("CPU Model", system_info.cpu_model)
    table.add_row("CPU Cores", str(system_info.cpu_cores))
    table.add_row("CPU Threads", str(system_info.cpu_threads))
    table.add_row("RAM", f"{system_info.ram_gb} GB")
    table.add_row("Virtualized", "Yes" if system_info.is_virtualized else "No")
    if system_info.is_virtualized:
        table.add_row("Platform", system_info.virtualization_platform or "unknown")
    console.print(table)


@app.command()
def download() -> None:
    """Pre-download all benchmark videos without encoding."""
    print("[yellow]Downloading video assets...[/]")
    download_all_videos(VIDEO_SOURCES, quick_mode=False, force=False)
    print("[green]All assets ready.[/]")


if __name__ == "__main__":
    app()
