# Obsidian Bridge Decision

> Last updated: 2026-06-29

## Recommended: Private Git Repository

### Architecture

```
Windows PC (Obsidian) → Git push → Private GitHub repo → Hermes reads docs/obsidian/
                     ← Git pull ←                      ← writes docs/obsidian/
```

### Why Git

| Criteria | Git | Syncthing | Tailscale | MCP Bridge | n8n |
|----------|-----|-----------|-----------|------------|-----|
| Version history | ✅ | ❌ | ❌ | ❌ | ❌ |
| Conflict resolution | ✅ | ⚠️ | ⚠️ | ❌ | ❌ |
| Offline support | ✅ | ✅ | ❌ | ❌ | ❌ |
| Setup complexity | Low | Medium | High | High | High |
| Cost | Free | Free | Free | Free | Paid/Setup |
| Security | ✅ Private repo | ✅ LAN | ✅ VPN | ⚠️ Local | ⚠️ Web |

### Setup Steps

1. **Create private GitHub repo**: `IIIH23/obsidian-pulse-of-earth`
2. **Install Obsidian Git plugin** on Windows:
   - Settings → Community plugins → Browse → "Git" → Install → Enable
3. **Configure plugin**:
   - Repository: `https://github.com/IIIH23/obsidian-pulse-of-earth.git`
   - Branch: `main`
   - Auto pull interval: 5 minutes
   - Auto push on save: enabled
4. **Set up authentication**:
   - Generate GitHub PAT with `repo` scope
   - Store in Obsidian Git plugin settings
5. **Vault structure** (synced to repo):
   ```
   Pulse of Earth/
   ├── 00 Inbox/
   ├── Agent Logs/
   ├── Architecture/
   ├── Decisions/
   ├── Templates/
   └── Daily/
   ```

### Security

- ✅ Private repository (not publicly accessible)
- ✅ No secrets in vault (templates only)
- ✅ Git history for audit trail
- ✅ No Windows vault exposed to internet

### Alternative: Syncthing

If Git is too complex:
- Install Syncthing on Windows and Hermes VPS
- Sync vault folder directly
- No version history but simpler setup

## Owner Actions

1. Create private GitHub repo `IIIH23/obsidian-pulse-of-earth`
2. Install Obsidian Git plugin
3. Configure auto-sync
4. Add Hermes as collaborator (read-only)
