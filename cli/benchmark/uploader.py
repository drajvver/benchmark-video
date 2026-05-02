"""Result upload to the benchmark server."""

from pathlib import Path
from typing import Optional

import requests


def get_token(base_url: str = "http://localhost:8000") -> Optional[str]:
    """Request an upload token from the server."""
    try:
        resp = requests.get(
            f"{base_url}/api/v1/token",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("token")
    except Exception:
        return None


def upload_result(
    report: dict,
    base_url: str = "http://localhost:8000",
    token: Optional[str] = None,
) -> bool:
    """Upload a benchmark result to the server."""
    if not token:
        token = get_token(base_url)
    if not token:
        print("[red]Failed to obtain upload token.[/]")
        return False
    
    try:
        resp = requests.post(
            f"{base_url}/api/v1/results",
            json=report,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        resp.raise_for_status()
        print(f"[green]Result uploaded successfully: {resp.json().get('id')}[/]")
        return True
    except requests.HTTPError as e:
        print(f"[red]Upload failed: {e.response.status_code} - {e.response.text}[/]")
        return False
    except Exception as e:
        print(f"[red]Upload failed: {e}[/]")
        return False


def upload_file(
    path: Path,
    base_url: str = "http://localhost:8000",
) -> bool:
    """Upload a result from a JSON file."""
    import json
    with open(path) as f:
        report = json.load(f)
    return upload_result(report, base_url)
