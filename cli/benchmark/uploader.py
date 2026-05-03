"""Result upload to the benchmark server."""

import hashlib
import hmac
import json
from pathlib import Path
from typing import Optional

import requests

_SERVER = "https://mc-6x0zte0wcd.bunny.run"
_HMAC_SECRET = "1ce4ece2b7cff2fa917edb12ea5febc49bcd4345892ae35b84f145609b1e55be"


def _sign(payload_bytes: bytes) -> str:
    return hmac.new(_HMAC_SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()


def get_token() -> Optional[str]:
    """Request an upload token from the server."""
    try:
        resp = requests.get(f"{_SERVER}/api/v1/token", timeout=10)
        resp.raise_for_status()
        return resp.json().get("token")
    except Exception:
        return None


def upload_result(report: dict, token: Optional[str] = None) -> bool:
    """Upload a benchmark result to the server."""
    if not token:
        token = get_token()
    if not token:
        print("[red]Failed to obtain upload token.[/]")
        return False

    payload_bytes = json.dumps(report, separators=(",", ":"), sort_keys=True).encode()

    try:
        resp = requests.post(
            f"{_SERVER}/api/v1/results",
            data=payload_bytes,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Benchmark-Signature": _sign(payload_bytes),
            },
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


def upload_file(path: Path) -> bool:
    """Upload a result from a JSON file."""
    with open(path) as f:
        report = json.load(f)
    return upload_result(report)
