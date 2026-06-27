# Staging Bootstrap Report

- Target: hermes-staging-01 (Ubuntu 26.04 LTS)
- Generated: 2026-06-27
- Commits: 628fdfe, 004abec, a8549fc, 2533b82, 2017bc957, 0dc5c47 (feature branch feat/staging-bootstrap)
- IPv4: 157.180.125.174
- Hostname: hermes-staging-01
- Kernel: 7.0.0-15-generic
- cloud-init: done (DataSourceHetzner)

## What was done

### Bootstrap (scripts/bootstrap-staging.sh)
- OS + network sanity (Ubuntu 26.04 LTS, cloud-init done)
- Created `deploy` user (uid=1000, bash, locked password, docker group)
- Installed Docker Engine 29.6.1 + Compose plugin from official repo
- Created 2 GB swap at /swapfile
- Installed + configured UFW (22/80/443 allowed, default deny incoming)
- Installed + ran Fail2ban (sshd jail)
- Enabled unattended-upgrades
- Configured Docker log rotation (json-file, 10m/5)
- Created /opt/terrabits/{apps,backups,caddy} owned by deploy

### SSH Lockdown (scripts/lockdown-staging-ssh.sh)
- Created dedicated deploy key: ~/.ssh/deploy_staging_ed25519
- Added public key to /home/deploy/.ssh/authorized_keys (chmod 600, chown deploy)
- Set PermitRootLogin no
- Set PasswordAuthentication no
- Set PubkeyAuthentication yes
- Set AllowUsers deploy
- Set PermitEmptyPasswords no
- Set ChallengeResponseAuthentication no
- Used drop-in /etc/ssh/sshd_config.d/99-terrabits-lockdown.conf
- Validated with sshd -T (effective settings)
- Reloaded sshd without restart
- Backup saved to /root/bootstrap-backups/sshd_config.20260627T172534Z.bak

## Verification results

### Bootstrap smoke tests (13 tests)
| Check | Result |
| --- | --- |
| Ubuntu 26.04 | PASS |
| cloud-init done | PASS |
| docker --version | PASS |
| docker compose version | PASS |
| docker service active | PASS |
| fail2ban service active | PASS |
| swap /swapfile enabled | PASS |
| deploy user exists | PASS |
| deploy in docker group | PASS |
| UFW 22/80/443 ALLOW | PASS |
| sshd config valid | PASS |
| project dirs exist | PASS |
| daemon.json log rotation | PASS |

### SSH Lockdown tests (4 tests)
| Check | Result |
| --- | --- |
| deploy SSH works (whoami=deploy) | PASS |
| root SSH rejected (bogus key) | PASS |
| drop-in file exists | PASS |
| deploy docker access | PASS |

### Manual checks
| Check | Result |
| --- | --- |
| root SSH with staging_admin_ed25519 | BLOCKED (correct) |
| PermitRootLogin no | effective |
| PasswordAuthentication no | effective |
| PubkeyAuthentication yes | effective |
| AllowUsers deploy | effective |

## Rollback status
- Backup: /root/bootstrap-backups/sshd_config.20260627T172534Z.bak
- Drop-in: /etc/ssh/sshd_config.d/99-terrabits-lockdown.conf
- Rollback procedure: restore backup + remove drop-in + systemctl reload sshd

## Not done
- Redis install (excluded by policy)
- Heavy monitoring stack (excluded by policy)
- Hetzner Firewall / DNS / Cloudflare / GitHub Secrets untouched
- No paid resources created
- No push to remote

## Remaining manual review
- Verify Hetzner Firewall mirrors UFW rules (policy #8) — optional but recommended.
