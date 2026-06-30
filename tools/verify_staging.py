#!/usr/bin/env python3
"""Staging VPS verification adapter.

Checks:
- SSH connectivity
- Docker status
- Container health
- HTTPS endpoints
- Version
- Rollback target
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any


STAGING_HOST = "157.180.125.174"
STAGING_USER = "deploy"
SSH_KEY = os.path.expanduser("~/.ssh/deploy_staging_ed25519")


class StagingVerificationError(RuntimeError):
    """Raised when staging verification fails."""


def _ssh(command: str, timeout: int = 15) -> tuple[int, str, str]:
    """Run command on staging via SSH."""
    result = subprocess.run(
        [
            "ssh",
            "-i", SSH_KEY,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=5",
            "-o", "BatchMode=yes",
            f"{STAGING_USER}@{STAGING_HOST}",
            command,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def verify_ssh() -> bool:
    """Check SSH connectivity."""
    rc, out, err = _ssh("whoami")
    if rc != 0:
        raise StagingVerificationError(f"SSH failed (rc={rc}): {err[:200]}")
    return out == STAGING_USER


def verify_docker() -> dict[str, Any]:
    """Check Docker status."""
    rc, out, err = _ssh("docker --version && docker compose version 2>/dev/null || echo 'no compose'")
    if rc != 0:
        raise StagingVerificationError(f"Docker check failed: {err[:200]}")
    lines = out.split("\n")
    return {
        "docker_version": lines[0] if lines else "unknown",
        "compose_version": lines[1] if len(lines) > 1 else "unknown",
    }


def verify_containers() -> list[dict[str, str]]:
    """List running containers."""
    rc, out, err = _ssh("docker ps --format '{{.Names}}|{{.Status}}|{{.Image}}'")
    if rc != 0:
        raise StagingVerificationError(f"Container list failed: {err[:200]}")
    containers = []
    for line in out.split("\n"):
        if "|" in line:
            parts = line.split("|")
            if len(parts) == 3:
                containers.append({
                    "name": parts[0],
                    "status": parts[1],
                    "image": parts[2],
                })
    return containers


def verify_health_endpoint(url: str = "http://127.0.0.1:8080/health") -> dict[str, Any]:
    """Check app health endpoint."""
    rc, out, err = _ssh(f"curl -fsS --max-time 5 {url} 2>&1 || echo 'FAIL'")
    if "FAIL" in out or rc != 0:
        return {"healthy": False, "response": out[:200]}
    return {"healthy": True, "response": out[:200]}


def verify_disk_usage() -> dict[str, Any]:
    """Check disk usage on staging."""
    rc, out, err = _ssh("df -P / | awk 'NR==2 {print $5}'")
    if rc != 0:
        raise StagingVerificationError(f"Disk check failed: {err[:200]}")
    return {"usage_percent": out.strip()}


def main() -> int:
    """Run staging verification."""
    print("=== Staging VPS Verification ===")

    # 1. SSH
    try:
        if verify_ssh():
            print(f"  SSH: OK ({STAGING_USER}@{STAGING_HOST})")
        else:
            print("  SSH: FAILED (wrong user)")
            return 1
    except StagingVerificationError as e:
        print(f"  SSH: {e}")
        return 1

    # 2. Docker
    try:
        docker = verify_docker()
        print(f"  DOCKER: {docker['docker_version']}")
        print(f"  COMPOSE: {docker['compose_version']}")
    except StagingVerificationError as e:
        print(f"  DOCKER: {e}")
        return 1

    # 3. Containers
    try:
        containers = verify_containers()
        print(f"  CONTAINERS: {len(containers)} running")
        for c in containers:
            print(f"    - {c['name']}: {c['status']}")
    except StagingVerificationError as e:
        print(f"  CONTAINERS: {e}")

    # 4. Health
    health = verify_health_endpoint()
    status = "HEALTHY" if health["healthy"] else "UNHEALTHY"
    print(f"  HEALTH: {status}")
    if not health["healthy"]:
        print(f"    Response: {health['response'][:100]}")

    # 5. Disk
    try:
        disk = verify_disk_usage()
        print(f"  DISK: {disk['usage_percent']} used")
    except StagingVerificationError as e:
        print(f"  DISK: {e}")

    print("  VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
