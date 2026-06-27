#!/usr/bin/env bash
# Lock down staging SSH access. Run as root on the target VPS.
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"
}

if [ "$(id -u)" -ne 0 ]; then
  log "ERROR: this script must be run as root"
  exit 1
fi

if ! id deploy >/dev/null 2>&1; then
  log "ERROR: deploy user does not exist"
  exit 1
fi

backup_dir="/root/bootstrap-backups"
timestamp="$(date -u +'%Y%m%dT%H%M%SZ')"
backup_path="${backup_dir}/sshd_config.${timestamp}.bak"
dropin_dir="/etc/ssh/sshd_config.d"
dropin_path="${dropin_dir}/99-terrabits-lockdown.conf"
dropin_backup="${backup_path}.99-terrabits-lockdown.conf"
dropin_existed=0

restore_configuration() {
  log "Restoring previous SSH configuration"
  cp -a "$backup_path" /etc/ssh/sshd_config
  if [ "$dropin_existed" -eq 1 ]; then
    cp -a "$dropin_backup" "$dropin_path"
  else
    rm -f "$dropin_path"
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

log "Backing up /etc/ssh/sshd_config to ${backup_path}"
install -d -m 0700 "$backup_dir"
cp -a /etc/ssh/sshd_config "$backup_path"

if [ -e "$dropin_path" ]; then
  cp -a "$dropin_path" "$dropin_backup"
  dropin_existed=1
fi

log "Ensuring deploy SSH directory and authorized_keys permissions"
install -d -o deploy -g deploy -m 0700 /home/deploy/.ssh
touch /home/deploy/.ssh/authorized_keys
chown deploy:deploy /home/deploy/.ssh/authorized_keys
chmod 0600 /home/deploy/.ssh/authorized_keys

log "Writing SSH lockdown configuration"
install -d -m 0755 "$dropin_dir"
{
  printf '%s\n' \
    'PermitRootLogin no' \
    'PasswordAuthentication no' \
    'PubkeyAuthentication yes' \
    'PermitEmptyPasswords no' \
    'ChallengeResponseAuthentication no' \
    'UsePAM yes' \
    'AllowUsers deploy'
} > "$dropin_path"
chmod 0644 "$dropin_path"

# sshd uses the first value found for most settings. Include this file before
# the distro's wildcard includes so an earlier cloud-init drop-in cannot win.
sed -i '\|^[[:space:]]*Include[[:space:]]\+/etc/ssh/sshd_config\.d/99-terrabits-lockdown\.conf[[:space:]]*$|d' \
  /etc/ssh/sshd_config
sed -i '1i Include /etc/ssh/sshd_config.d/99-terrabits-lockdown.conf' \
  /etc/ssh/sshd_config

log "Validating SSH daemon configuration"
if ! sshd -t; then
  log "ERROR: SSH configuration is invalid"
  restore_configuration
  exit 1
fi

if ! effective_setting_is PermitRootLogin no ||
  ! effective_setting_is PasswordAuthentication no ||
  ! effective_setting_is PubkeyAuthentication yes ||
  ! effective_setting_is PermitEmptyPasswords no ||
  ! effective_setting_is KbdInteractiveAuthentication no ||
  ! effective_setting_is UsePAM yes ||
  ! effective_setting_is AllowUsers deploy; then
  log "ERROR: SSH lockdown settings are not effective"
  restore_configuration
  exit 1
fi

log "Reloading sshd without restarting active sessions"
systemctl reload sshd

log "SSH lockdown complete: root and password login are disabled; deploy key login is enabled"
