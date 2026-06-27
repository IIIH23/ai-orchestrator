#!/usr/bin/env bash
# Verify staging SSH lockdown. Run as root on the target VPS.
set -uo pipefail

pass_count=0
fail_count=0

if [ "$(id -u)" -ne 0 ]; then
  printf 'ERROR: this script must be run as root\n' >&2
  exit 1
fi

check() {
  local name="$1"
  shift

  if "$@" >/dev/null 2>&1; then
    printf 'PASS  %s\n' "$name"
    pass_count=$((pass_count + 1))
  else
    printf 'FAIL  %s\n' "$name"
    fail_count=$((fail_count + 1))
  fi
}

effective_setting_is() {
  local name="$1"
  local expected="$2"

  sshd -T 2>/dev/null |
    awk -v name="$name" -v expected="$expected" '
      tolower($1) == tolower(name) && tolower($2) == tolower(expected) {
        found = 1
      }
      END { exit !found }
    '
}

root_ssh_is_rejected() {
  ! ssh \
    -o BatchMode=yes \
    -o ConnectTimeout=5 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    root@127.0.0.1 whoami
}

check "sshd configuration is valid" sshd -t
check "PermitRootLogin is no" effective_setting_is PermitRootLogin no
check "PasswordAuthentication is no" effective_setting_is PasswordAuthentication no
check "PubkeyAuthentication is yes" effective_setting_is PubkeyAuthentication yes
check "deploy can run docker ps" sudo -u deploy -- docker ps
check "root SSH connection is rejected" root_ssh_is_rejected

printf '\nSummary: %d PASS, %d FAIL\n' "$pass_count" "$fail_count"
[ "$fail_count" -eq 0 ]
