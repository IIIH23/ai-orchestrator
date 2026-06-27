# Systemd Health Check Timer

> Last updated: 2026-06-27

## Service Unit

```ini
# /etc/systemd/system/pulse-health.service
[Unit]
Description=Pulse of Earth Health Check
After=docker.service

[Service]
Type=oneshot
User=deploy
Group=deploy
ExecStart=/opt/terrabits/scripts/check-health.sh
EnvironmentFile=/opt/terrabits/apps/pulse-of-earth/.env
StandardOutput=journal
StandardError=journal
```

## Timer Unit

```ini
# /etc/systemd/system/pulse-health.timer
[Unit]
Description=Run Pulse health check every 5 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
RandomizedDelaySec=30

[Install]
WantedBy=timers.target
```

## Enable

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pulse-health.timer
sudo systemctl status pulse-health.timer
```

## Logs

```bash
journalctl -u pulse-health.service -f
```
