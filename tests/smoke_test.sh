#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for required_file in AGENTS.md ROADMAP.md; do
  if [[ ! -f "$repo_root/$required_file" ]]; then
    echo "Missing required file: $required_file" >&2
    exit 1
  fi
done

mapfile -d '' python_files < <(
  find "$repo_root" \
    -type d \( -name .venv -o -name venv -o -name .git \) -prune \
    -o -type f -name '*.py' -print0
)

pycache_dir="$(mktemp -d)"
trap 'rm -rf "$pycache_dir"' EXIT

for python_file in "${python_files[@]}"; do
  PYTHONPYCACHEPREFIX="$pycache_dir" python3 -m py_compile "$python_file"
done

echo "Smoke test passed: 2 required files found; ${#python_files[@]} Python file(s) compiled."
