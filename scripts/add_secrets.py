#!/usr/bin/env python3
"""Manage GitHub environment secrets via API.

Reads token from GITHUB_TOKEN env var or --token flag.
Default mode: dry-run. Use --yes to apply changes.
"""
import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error


def get_token(args):
    """Resolve token from args or env."""
    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: No token. Use --token or set GITHUB_TOKEN.", file=sys.stderr)
        sys.exit(1)
    return token


def api(method, path, token, data=None, dry_run=False):
    """Make GitHub API call."""
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    if dry_run:
        print(f"  [DRY-RUN] {method} {url}")
        return {}

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()) if resp.status != 204 else {}
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()[:200], "status": e.code}


def encrypt_secret(public_key_b64, secret_value):
    """Encrypt secret using NaCl sealed box with environment public key."""
    from nacl import encoding, public

    public_key_bytes = encoding.Base64Encoder().decode(public_key_b64)
    public_key = public.PublicKey(public_key_bytes)
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def put_secret(token, owner, repo, env_name, secret_name, secret_value, dry_run):
    """Create or update an environment secret."""
    if not secret_value:
        print(f"  SKIP: {secret_name} (empty)")
        return

    key_path = f"/repos/{owner}/{repo}/environments/{env_name}/secrets/public-key"
    key_data = api("GET", key_path, token, dry_run=dry_run)

    if "key" not in key_data:
        print(f"  FAIL: {secret_name} (no public key: {key_data})")
        return

    encrypted_value = encrypt_secret(key_data["key"], secret_value)
    secret_path = f"/repos/{owner}/{repo}/environments/{env_name}/secrets/{secret_name}"
    data = {"encrypted_value": encrypted_value, "key_id": key_data["key_id"]}
    result = api("PUT", secret_path, token, data, dry_run)
    status = "OK" if "error" not in result else "FAIL"
    print(f"  {status}: {secret_name}")


def list_secrets(token, owner, repo, env_name, dry_run):
    """List secret names (no values)."""
    path = f"/repos/{owner}/{repo}/environments/{env_name}/secrets"
    result = api("GET", path, token, dry_run=dry_run)
    secrets = result.get("secrets", [])
    print(f"\n  Secrets in {env_name}:")
    for s in secrets:
        print(f"    - {s['name']} (created: {s.get('created_at', '?')})")


def main():
    parser = argparse.ArgumentParser(description="Manage GitHub environment secrets")
    parser.add_argument("--token", help="GitHub PAT (or GITHUB_TOKEN env var)")
    parser.add_argument("--owner", default="IIIH23")
    parser.add_argument("--repo", default="ai-orchestrator")
    parser.add_argument("--env", default="staging")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--yes", action="store_true", help="Apply changes")
    parser.add_argument("--put", nargs=2, metavar=("NAME", "VALUE"), action="append")
    parser.add_argument("--list", action="store_true", help="List secrets")
    args = parser.parse_args()

    dry_run = args.dry_run and not args.yes
    token = get_token(args)

    print(f"=== Secrets Manager (env={args.env}, dry-run={dry_run}) ===")

    if args.list:
        list_secrets(token, args.owner, args.repo, args.env, dry_run)

    if args.put:
        for name, value in args.put:
            put_secret(token, args.owner, args.repo, args.env, name, value, dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
