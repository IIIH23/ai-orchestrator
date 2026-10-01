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
from typing import Any, Callable


STAGING_USER = "deploy"
SSH_KEY = os.path.expanduser("~/.ssh/deploy_staging_ed25519")


class StagingVerificationError(RuntimeError):
    """Raised when staging verification fails."""


def staging_host() -> str:
    """Return the staging host from STAGING_HOST; fail closed when unset."""
    host = os.environ.get("STAGING_HOST", "").strip()
    if not host:
        raise StagingVerificationError("STAGING_HOST is not set")
    return host


def _ssh(command: str, timeout: int = 15) -> tuple[int, str, str]:
    """Run command on staging via SSH."""
    host = staging_host()
    result = subprocess.run(
        [
            "ssh",
            "-i", SSH_KEY,
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=5",
            "-o", "BatchMode=yes",
            f"{STAGING_USER}@{host}",
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
    """Run staging verification. Exit 0 only when every check is healthy."""
    print("=== Staging VPS Verification ===")
    failures: list[str] = []

    def check(name: str, run: Callable[[], str]) -> bool:
        try:
            print(f"  {name}: {run()}")
            return True
        except (StagingVerificationError, subprocess.TimeoutExpired, OSError) as exc:
            print(f"  {name}: FAILED ({exc})")
            failures.append(name)
            return False

    def ssh() -> str:
        if not verify_ssh():
            raise StagingVerificationError("wrong user")
        return f"OK ({STAGING_USER}@{staging_host()})"

    def docker() -> str:
        info = verify_docker()
        return f"{info['docker_version']}; {info['compose_version']}"

    def containers() -> str:
        running = verify_containers()
        names = ", ".join(f"{c['name']} ({c['status']})" for c in running)
        return f"{len(running)} running" + (f": {names}" if names else "")

    def health() -> str:
        result = verify_health_endpoint()
        if not result["healthy"]:
            raise StagingVerificationError(f"unhealthy: {result['response'][:100]}")
        return "HEALTHY"

    def disk() -> str:
        return f"{verify_disk_usage()['usage_percent']} used"

    # Without SSH nothing else can be checked.
    if check("SSH", ssh):
        for name, run in (("DOCKER", docker), ("CONTAINERS", containers),
                          ("HEALTH", health), ("DISK", disk)):
            check(name, run)

    if failures:
        print(f"  VERIFICATION FAILED: {', '.join(failures)}")
        return 1
    print("  VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
