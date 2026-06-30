#!/usr/bin/env python3
"""Setup branch protection and environments via GitHub API.

Reads token from GITHUB_TOKEN env var or --token flag.
Supports --dry-run mode (default: dry-run).
Does NOT perform admin API changes without explicit --yes flag.
"""
import argparse
import json
import os
import pathlib
import sys
import urllib.request
import urllib.error


def get_token(args):
    """Resolve token from args, env, or fail."""
    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("ERROR: No token provided. Use --token or set GITHUB_TOKEN env var.", file=sys.stderr)
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
        error = e.read().decode()[:200]
        print(f"  ERROR {e.code}: {error}", file=sys.stderr)
        return {"error": error, "status": e.code}


def setup_branch_protection(token, owner, repo, dry_run, yes):
    """Configure branch protection for master."""
    path = f"/repos/{owner}/{repo}/branches/master/protection"
    data = {
        "required_status_checks": {
            "strict": True,
            "contexts": ["lint", "test"],
        },
        "enforce_admins": False,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 1,
        },
        "restrictions": None,
        "required_linear_history": False,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }

    if not yes:
        print("  WARNING: Branch protection changes require --yes flag.")
        return False

    result = api("PUT", path, token, data, dry_run)
    return "error" not in result


def create_environments(token, owner, repo, dry_run, yes):
    """Create staging and production environments."""
    if not yes:
        print("  WARNING: Environment creation requires --yes flag.")
        return False

    for env_name in ["staging", "production"]:
        path = f"/repos/{owner}/{repo}/environments/{env_name}"
        data = {
            "wait_timer": 0,
            "reviewers": [],
            "deployment_branch_policy": {
                "protected_branches": env_name == "production",
                "custom_branch_policies": True,
            },
        }
        api("PUT", path, token, data, dry_run)
    return True


def put_secret(token, owner, repo, env_name, secret_name, secret_value, dry_run):
    """Create or update an environment secret."""
    if not secret_value:
        print(f"  SKIP: {secret_name} (empty value)")
        return

    # Get environment public key
    key_path = f"/repos/{owner}/{repo}/environments/{env_name}/secrets/public-key"
    key_data = api("GET", key_path, token, dry_run=dry_run)

    if "key" not in key_data:
        print(f"  SKIP: {secret_name} (no public key)")
        return

    import base64
    from nacl import encoding, public

    public_key_bytes = encoding.Base64Encoder().decode(key_data["key"])
    public_key = public.PublicKey(public_key_bytes)
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    encrypted_value = base64.b64encode(encrypted).decode("utf-8")

    secret_path = f"/repos/{owner}/{repo}/environments/{env_name}/secrets/{secret_name}"
    data = {"encrypted_value": encrypted_value, "key_id": key_data["key_id"]}
    api("PUT", secret_path, token, data, dry_run)
    print(f"  OK: {secret_name}")


def main():
    parser = argparse.ArgumentParser(description="Setup GitHub branch protection + environments")
    parser.add_argument("--token", help="GitHub PAT (or GITHUB_TOKEN env var)")
    parser.add_argument("--owner", default="IIIH23")
    parser.add_argument("--repo", default="earth-pulse-poc")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview changes")
    parser.add_argument("--yes", action="store_true", help="Actually make changes")
    parser.add_argument("--setup-protection", action="store_true")
    parser.add_argument("--setup-environments", action="store_true")
    parser.add_argument("--put-secret", nargs=2, metavar=("SECRET_NAME", "SECRET_VALUE"))
    args = parser.parse_args()

    dry_run = args.dry_run and not args.yes
    if not dry_run and not args.yes:
        print("ERROR: Must pass --yes to make actual changes.")
        sys.exit(1)

    token = get_token(args)
    owner, repo = args.owner, args.repo

    print(f"=== GitHub Setup (dry-run={dry_run}) ===")

    if args.setup_protection:
        print("\n[Branch Protection]")
        setup_branch_protection(token, owner, repo, dry_run, args.yes)

    if args.setup_environments:
        print("\n[Environments]")
        create_environments(token, owner, repo, dry_run, args.yes)

    if args.put_secret:
        name, value = args.put_secret
        print(f"\n[Secret: {name}]")
        put_secret(token, owner, repo, "staging", name, value, dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()
