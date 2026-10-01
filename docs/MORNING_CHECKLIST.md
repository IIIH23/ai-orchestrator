1. ...

2. Створити репозиторій ...

3. Додати Deploy Key (Settings → Deploy Keys):
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGyZcdEHVOqRFccV7jnUfxMOTMG0zBWPJbrSgBGfl32o hermes-pulse-of-earth
(Allow read/write)

4. Додати новий GitHub PAT (з правами repo, workflow)

5. Cloudflare:地球-bit.staging.example.org A-record → 203.0.113.10 (DNS only)

6. Cloudflare: API token + Zone ID + 1 не Team Emails (нашранує)

7. Staging bootstrap: mkdir /opt/terrabits/{apps/pulse-of-earth,caddy,backups/{postgres,releases},scripts,shared/releases}
