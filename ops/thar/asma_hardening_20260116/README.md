# ASMA Hardening Packet - 2026-01-16

**Date:** 2026-01-16  
**Status:** ✅ Production (deployed to dev and main branches)  
**Purpose:** Auto-start and watchdog hardening for ASMA Prototype on THAR

## What Happened

After the THAR server restart, ASMA prototype container (`asma-proto-v10`) was not surviving reboots. No health monitoring or automatic recovery was in place. This hardening packet implements:

1. **Auto-start:** Systemd user units automatically start container on boot
2. **Health monitoring:** Watchdog script checks health every 2 minutes
3. **Automatic recovery:** Watchdog restarts container if unhealthy (with cooldown)
4. **Single owner rule:** Systemd manages container lifecycle (no dueling orchestrators)

## What Was Fixed

### Problems
- Container not surviving server restarts
- No health monitoring
- No automatic recovery
- Existing systemd unit misconfigured (wrong container name, pod reference)

### Root Cause
- Container created standalone but old systemd unit referenced pod
- No auto-start mechanism enabled
- No health monitoring or recovery automation
- Single owner rule not enforced

### Fix
- Created new systemd user unit (`container-asma-proto.service`) with correct configuration
- Created watchdog script (`asma_watchdog.sh`) with 10-minute cooldown, systemd-aware restart
- Created watchdog timer (`asma-watchdog.timer`) runs every 2 minutes
- Documented deprecated units and single owner rule

## Current State

### Operational Status

- **Container:** `asma-proto-v10` - Running
- **Systemd Unit:** `container-asma-proto.service` - Enabled and active
- **Watchdog:** `asma-watchdog.timer` - Enabled and active
- **Health:** All checks passing (HTTP 200)
- **External URL:** Working (returns 401 - Basic auth)

### What's Running on THAR Right Now

- **Container Name:** `asma-proto-v10`
- **Local Port:** `8765` (host) → `5000` (container)
- **External URL:** `https://protect.qb3.berkeley.edu/asma/`
- **Health Endpoint:** `http://127.0.0.1:8765/health`
- **Expected Health Code:** `200`

### Systemd Units Enabled

- `container-asma-proto.service` - Auto-starts `asma-proto-v10` container
- `asma-watchdog.timer` - Health monitoring (runs every 2 minutes)

### Watchdog Schedule + What Counts as Healthy

- **Frequency:** Every 2 minutes
- **Healthy Code:** HTTP 200 (only)
- **Cooldown:** 10 minutes between recovery attempts
- **Recovery:** Restarts container via systemctl if unit enabled, else podman
- **Exit Codes:** 0 for healthy/cooldown, 1 for actual failures

## Install Steps

### Prerequisites

- Linger enabled: `loginctl enable-linger spencerlong`
- Container exists: `asma-proto-v10`
- Data directories exist:
  - `/opt/shared/spencerlong/asma-prototype/demo_data`
  - `/usr2/people/alex.styer/public_html`

### Step 1: Install Container Unit

```bash
# Copy template to systemd user directory
cp /usr2/people/spencerlong/asma-prototype/ops/thar/asma_hardening_20260116/systemd_user_units/container-asma-proto.service \
   ~/.config/systemd/user/container-asma-proto.service

# Reload systemd
systemctl --user daemon-reload

# Enable and start
systemctl --user enable container-asma-proto.service
systemctl --user start container-asma-proto.service

# Verify
systemctl --user status container-asma-proto.service
```

### Step 2: Install Watchdog

```bash
# Copy watchdog script (already executable)
# Script location: /usr2/people/spencerlong/asma-prototype/ops/thar/asma_hardening_20260116/watchdog/asma_watchdog.sh
# NOTE: If installing fresh, update ExecStart path in asma-watchdog.service to match script location

# Copy watchdog service
cp /usr2/people/spencerlong/asma-prototype/ops/thar/asma_hardening_20260116/systemd_user_units/asma-watchdog.service \
   ~/.config/systemd/user/asma-watchdog.service

# Copy watchdog timer
cp /usr2/people/spencerlong/asma-prototype/ops/thar/asma_hardening_20260116/systemd_user_units/asma-watchdog.timer \
   ~/.config/systemd/user/asma-watchdog.timer

# Reload systemd
systemctl --user daemon-reload

# Enable timer (this enables the service automatically)
systemctl --user enable --now asma-watchdog.timer

# Verify
systemctl --user status asma-watchdog.timer
```

### Step 3: Verify Linger

```bash
loginctl show-user spencerlong | grep Linger
# If not enabled: loginctl enable-linger spencerlong
```

## Verify Steps

### Quick Health Check

```bash
curl -s http://127.0.0.1:8765/health | python3 -m json.tool
# Expected: {"status": "ok", "data_dir": "/app/demo_data"}
```

### Container Status

```bash
podman ps | grep asma-proto-v10
# Expected: Container Up
```

### Systemd Units

```bash
systemctl --user status container-asma-proto.service
systemctl --user status asma-watchdog.timer
# Expected: Both active/enabled
```

### Watchdog Logs

```bash
journalctl --user -u asma-watchdog.service -n 50
# Expected: "Backend is healthy (status=200)"
```

### Stability Check (10 iterations)

```bash
for i in {1..10}; do
    date
    curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/health
    sleep 2
done
# Expected: All 10 checks return 200
```

### External URL

```bash
curl -k -I https://protect.qb3.berkeley.edu/asma/
# Expected: HTTP 401 (Basic auth working)
```

## Rollback Commands

### Disable Auto-Start

```bash
systemctl --user disable --now container-asma-proto.service
```

### Disable Watchdog

```bash
systemctl --user disable --now asma-watchdog.timer
```

### Manual Container Control

```bash
podman start asma-proto-v10
podman stop asma-proto-v10
```

### Complete Rollback

```bash
# Disable all ASMA systemd units
systemctl --user disable --now container-asma-proto.service
systemctl --user disable --now asma-watchdog.timer

# Containers can still be managed manually
podman start asma-proto-v10
podman stop asma-proto-v10
```

## Files in This Packet

### Systemd Unit Templates

- `systemd_user_units/container-asma-proto.service` - Container auto-start unit
- `systemd_user_units/asma-watchdog.service` - Watchdog service unit
- `systemd_user_units/asma-watchdog.timer` - Watchdog timer unit

### Watchdog Script

- `watchdog/asma_watchdog.sh` - Health monitoring script (executable)

### Diagnostics

- `diagnostics/` - Historical diagnostics and reports from deployment

## Important Notes

### Runtime Paths

**NOTE:** Deployed systemd units on THAR may reference old paths:
- ExecStart: `/usr2/people/spencerlong/asma-prototype/ops/watchdog/asma_watchdog.sh`
- COOLDOWN_FILE: `/usr2/people/spencerlong/asma-prototype/ops/watchdog/.asma_last_restart_epoch`

These deployed paths will NOT change automatically - we are only moving repo templates. Existing deployments continue to work. If reinstalling units, use the new paths from this packet.

### Deployed Systems and Path Migration

**Deployed systems may still reference old watchdog paths.** This is intentional to avoid breaking running systems during the repo reorganization (2026-01-17).

**What this means:**
- Currently deployed systemd units at `~/.config/systemd/user/asma-watchdog.service` may reference the old path: `/usr2/people/spencerlong/asma-prototype/ops/watchdog/asma_watchdog.sh`
- The watchdog script template has been moved to: `ops/thar/asma_hardening_20260116/watchdog/asma_watchdog.sh`
- **Reinstalling systemd units is required to adopt new template paths** - simply copying the new templates and updating ExecStart paths in the deployed units
- The runtime cooldown file (`.asma_last_restart_epoch`) remains in its original location to maintain compatibility

**This is intentional:** The reorganization was repo-only to avoid runtime behavior changes. Deployed systems continue to work with their existing paths until units are manually reinstalled with updated paths.

### ASMA Has No Database

ASMA is a single-container FastAPI application with no database. The watchdog has no DB guardrail (unlike GenomeDepot).

### Single Owner Rule

Each container lifecycle must have ONE orchestrator. Systemd manages the container lifecycle. Do not use `podman run --restart unless-stopped` for `asma-proto-v10`.

## Related Documentation

- **Master Runbook:** [docs/runbooks/THAR_ASMA_MASTER_RUNBOOK.md](../../../../docs/runbooks/THAR_ASMA_MASTER_RUNBOOK.md)
- **THAR Ops:** [ops/thar/README.md](../README.md)
- **Ops Index:** [ops/README.md](../../README.md)

## Deployment History

- **2026-01-16:** Initial hardening deployment
- **2026-01-16:** Soak period (12-24 hours)
- **2026-01-17:** Merged to dev branch
- **2026-01-17:** Merged to main branch

## Verification

All validation checks passed:
- ✅ Container unit enabled and starts container successfully
- ✅ Health checks: 10/10 iterations returned HTTP 200
- ✅ External URL: returns 401 (Basic auth working)
- ✅ Watchdog: runs every 2 minutes, logs healthy status
- ✅ Recovery test: watchdog detected failure, restarted via systemctl, container recovered
- ✅ Single owner rule: only container-asma-proto.service enabled
- ✅ No errors in logs, no restart loops

---

**Status:** ✅ Production Ready  
**Branches:** dev ✅, main ✅
