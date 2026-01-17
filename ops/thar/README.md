# THAR Server Operations

**Server:** THAR (protect.qb3.berkeley.edu)  
**Purpose:** Operational procedures and templates for ASMA Prototype on THAR

## Quick Start

### What's Running on THAR Right Now

- **Container:** `asma-proto-v10`
- **Local Port:** `8765` (host) → `5000` (container)
- **External URL:** `https://protect.qb3.berkeley.edu/asma/`
- **Health Endpoint:** `http://127.0.0.1:8765/health`
- **Expected Health Code:** `200`

### Systemd Units Enabled

- `container-asma-proto.service` - Auto-starts `asma-proto-v10` container
- `asma-watchdog.timer` - Health monitoring (runs every 2 minutes)

### Watchdog Schedule

- **Frequency:** Every 2 minutes
- **Healthy Code:** HTTP 200
- **Cooldown:** 10 minutes between recovery attempts
- **Recovery:** Restarts container via systemctl if unit enabled, else podman

### Verification Commands

```bash
# Container status
podman ps | grep asma-proto-v10

# Health check
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/health

# Systemd units
systemctl --user status container-asma-proto.service
systemctl --user status asma-watchdog.timer

# Watchdog logs
journalctl --user -u asma-watchdog.service -n 50
```

### Rollback Commands

```bash
# Disable auto-start
systemctl --user disable --now container-asma-proto.service

# Disable watchdog
systemctl --user disable --now asma-watchdog.timer

# Manual container control
podman start asma-proto-v10
podman stop asma-proto-v10
```

## Hardening Packets

### asma_hardening_20260116

**Date:** 2026-01-16  
**Status:** ✅ Production (deployed to dev and main)

**Contents:**
- Systemd user unit templates for auto-start
- Watchdog script and timer for health monitoring
- Installation and verification procedures
- Historical diagnostics from deployment

**Documentation:** [ops/thar/asma_hardening_20260116/README.md](asma_hardening_20260116/README.md)

## Architecture

### ASMA Prototype

- **Type:** Single-container FastAPI application
- **No Database:** Data loaded from CSV/JSONL files at startup
- **No Cache:** Stateless API
- **Container:** `asma-proto-v10` (FastAPI/Uvicorn)

### Network

```
Internet → nginx (port 443) → localhost:8765 → asma-proto-v10 (port 5000)
```

### Data Locations

- **Demo data:** `/opt/shared/spencerlong/asma-prototype/demo_data`
- **Alex's taxonomy files:** `/usr2/people/alex.styer/public_html` (read-only)
- **Watchdog cooldown:** `/usr2/people/spencerlong/asma-prototype/ops/watchdog/.asma_last_restart_epoch` (runtime file)

## Master Runbook

For comprehensive operational procedures, see:
[THAR_ASMA_MASTER_RUNBOOK.md](../../docs/runbooks/THAR_ASMA_MASTER_RUNBOOK.md)

## Notes

- All paths are absolute paths for THAR server
- Templates are reference copies - deployed units may use different paths
- Runtime files (like cooldown file) remain in original locations for deployed systems
- No secrets or credentials stored in this directory
