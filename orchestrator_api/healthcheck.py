"""Container health probe for the local Orchestrator API."""

from __future__ import annotations

import json
import os
import sys
import urllib.request


def main() -> int:
    port = os.getenv("ORCHESTRATOR_PORT", "8080")
    url = f"http://127.0.0.1:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            payload = json.load(response)
    except Exception as exc:
        print(f"healthcheck failed: {exc}", file=sys.stderr)
        return 1

    if response.status != 200 or payload.get("status") != "ok":
        print(f"unhealthy response: HTTP {response.status} {payload}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
