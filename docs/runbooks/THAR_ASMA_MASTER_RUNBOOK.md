# THAR ASMA Prototype Master Runbook

**Last Updated:** January 16, 2026  
**Server:** THAR (protect.qb3.berkeley.edu)  
**Purpose:** Canonical operational procedures for ASMA Prototype on THAR

---

## 1. PURPOSE & SCOPE

### What This Runbook Covers

- Bringing ASMA Prototype online after THAR server restart
- Diagnosing and fixing service failures
- Understanding known failure modes and their fixes
- Safe maintenance procedures
- Health verification procedures
- Auto-start and watchdog configuration

### What This Runbook Does NOT Cover

- GenomeDepot containers (separate system)
- Development environments
- Rebuilding images or containers
- Initial deployment from scratch
- Nginx configuration changes (requires sysadmin)
- Data directory updates (requires explicit approval)

### When to Use This Runbook

- After THAR server restart
- When `https://protect.qb3.berkeley.edu/asma/` returns 502 or 503
- When container shows "Up" but service is unresponsive
- For routine health checks
- When watchdog reports failures

---

## 2. SYSTEM OVERVIEW (MENTAL MODEL)

### Architecture

```
Internet → nginx (port 443) → localhost:8765 → asma-proto-v10 (FastAPI/Uvicorn, port 5000)
```

**ASMA is a single-container FastAPI application with no database or cache.**

### Port Mappings

- **Host port 8765** → Container port 5000 (FastAPI service)
- **External HTTPS** → nginx → localhost:8765

### Container Names (Authoritative)

- **Container:** `asma-proto-v10`

This name is fixed. Do not create containers with different names.

### Data Locations

- **Demo data:** `/opt/shared/spencerlong/asma-prototype/demo_data` (mounted to `/app/demo_data`)
- **Alex's taxonomy files:** `/usr2/people/alex.styer/public_html` (mounted to `/app/alex_public_html`, read-only)
- **Ops scripts:** `/usr2/people/spencerlong/asma-prototype/ops/`
- **Watchdog cooldown file:** `/usr2/people/spencerlong/asma-prototype/ops/watchdog/.asma_last_restart_epoch` (runtime file, remains in old location for deployed systems)

### Environment Variables

- `ASMA_DATA_DIR=/app/demo_data`
- `ALEX_PUBLIC_HTML_DIR=/app/alex_public_html`

### Key Difference from GenomeDepot

**ASMA has no database.** There is no DB container, no DB guardrail in the watchdog, and no DB dependency checks. ASMA loads data from CSV/JSONL files at startup.

---

## 3. CANONICAL DEPLOYMENT METHOD

### Current Authoritative Method

**Systemd user services** (auto-start enabled). This is the supported method.

### Systemd Services Status

Systemd user services exist at `~/.config/systemd/user/container-asma-proto.service`:
- **Active unit:** `container-asma-proto.service` (manages `asma-proto-v10`)
- **Watchdog:** `asma-watchdog.service` + `asma-watchdog.timer` (health monitoring)

### Required Container

This container MUST exist:
- `asma-proto-v10` (FastAPI/Uvicorn)

### Required Files

- `/opt/shared/spencerlong/asma-prototype/demo_data/` (demo data directory)
- `/usr2/people/alex.styer/public_html/` (Alex's taxonomy files)
- Systemd unit templates in repo: `ops/thar/asma_hardening_20260116/systemd_user_units/`

### Auto-Start Status

**Status:** Auto-restart after reboot is implemented (see Section 13: Auto-Restart Hardening). Systemd user services automatically start containers on boot.

---

## 4. FAST RECOVERY CHECKLIST (TL;DR)

**Use this when you need to restore service quickly.**

```bash
# 1. Check container status
podman ps | grep asma-proto-v10

# 2. Start container if stopped
podman start asma-proto-v10
sleep 5

# 3. Test backend
curl -I http://127.0.0.1:8765/health

# 4. If unhealthy, restart container
podman restart asma-proto-v10
sleep 10
curl -I http://127.0.0.1:8765/health
```

**What "Good" Looks Like:**
- `podman ps` shows `asma-proto-v10` as "Up"
- `curl -I http://127.0.0.1:8765/health` returns HTTP 200 OK
- Port 8765 is listening: `ss -ltnp | grep 8765`

**What NOT to Touch:**
- Do not delete containers
- Do not recreate volumes
- Do not edit nginx configs
- Do not modify data directories without approval

---

## 5. FULL BRING-UP PROCEDURE (STEP-BY-STEP)

### Step 1: Host Verification

```bash
hostname
# Expected: thar

whoami
# Expected: spencerlong

podman --version
# Expected: 3.4.4 or higher
```

### Step 2: Check Container Status

```bash
podman ps -a --format "{{.Names}}\t{{.Status}}\t{{.Ports}}" | grep asma-proto-v10
```

**Expected output:**
```
asma-proto-v10  Up X minutes ago  0.0.0.0:8765->5000/tcp
```

**If container shows "Created" or "Exited":**
- It needs to be started. Proceed to Step 3.

### Step 3: Start Container

```bash
podman start asma-proto-v10
```

**Wait 5-10 seconds for Uvicorn to start.**

**Check logs for successful startup:**
```bash
podman logs --tail 30 asma-proto-v10 | tail -10
```

**Expected log output:**
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

**If you see errors:**
- See Section 7: Common Failure Modes

### Step 4: Verify Port Is Listening

```bash
ss -ltnp | grep 8765
```

**Expected output:**
```
LISTEN 0  4096  *:8765  *:*  users:(("exe",pid=XXXXX,fd=XX))
```

**If port is not listening:**
- Container may not be fully started. Wait 10 more seconds and check again.

### Step 5: Health Verification

See Section 6 for detailed health checks.

**Quick verification:**
```bash
curl -I http://127.0.0.1:8765/health
# Expected: HTTP 200 OK
```

---

## 6. HEALTH & READINESS CHECKS

### Container Status Check

```bash
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "NAME|asma-proto"
```

**Expected output:**
```
NAMES               STATUS                 PORTS
asma-proto-v10      Up X minutes ago       0.0.0.0:8765->5000/tcp
```

### Port Listening Check

```bash
ss -ltnp | grep 8765
```

**Expected:**
- Port 8765 listening

### Backend Health Check

```bash
curl -I http://127.0.0.1:8765/health
```

**Expected response:**
```
HTTP/1.1 200 OK
date: ...
content-type: application/json
content-length: XX
```

**Full health check with JSON response:**
```bash
curl -s http://127.0.0.1:8765/health | python3 -m json.tool
```

**Expected JSON:**
```json
{
    "status": "ok",
    "data_dir": "/app/demo_data"
}
```

### API Endpoint Check

```bash
curl -s http://127.0.0.1:8765/patients | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Patients: {len(data)}')"
```

**Expected:** Returns number of patients (e.g., "Patients: 3")

### External URL Check

```bash
curl -k -I https://protect.qb3.berkeley.edu/asma/
```

**Expected:** HTTP 401 (Basic auth required) or HTTP 200 (if authenticated)

**Note:** 401 is expected and indicates nginx proxy is working.

### Stability Check (10 iterations)

```bash
for i in {1..10}; do
    date
    curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/health
    sleep 2
done
```

**Expected:** All 10 checks return `200`

---

## 7. COMMON FAILURE MODES

### Failure Mode 1: Container Not Running

**Symptoms:**
- `podman ps` shows container as "Created" or "Exited"
- `curl http://127.0.0.1:8765/health` returns connection refused

**Root Cause:**
- Container was stopped or never started
- Server restart without auto-start enabled

**Fix:**
```bash
podman start asma-proto-v10
sleep 5
curl -I http://127.0.0.1:8765/health
```

**Prevention:**
- Enable systemd auto-start (Section 13)

### Failure Mode 2: Container Running but Unhealthy

**Symptoms:**
- `podman ps` shows container as "Up"
- `curl http://127.0.0.1:8765/health` returns non-200 or connection refused
- Port 8765 not listening

**Root Cause:**
- Uvicorn process crashed inside container
- Application startup error
- Port binding issue

**Fix:**
```bash
podman restart asma-proto-v10
sleep 10
curl -I http://127.0.0.1:8765/health
```

**If still failing, check logs:**
```bash
podman logs --tail 50 asma-proto-v10
```

**Prevention:**
- Watchdog will auto-restart (Section 12)

### Failure Mode 3: Data Directory Missing

**Symptoms:**
- Container starts but health endpoint returns error
- Logs show "FileNotFoundError" or "No such file or directory"

**Root Cause:**
- Volume mount path incorrect or missing
- Data directory not accessible

**Fix:**
```bash
# Verify data directory exists
test -d /opt/shared/spencerlong/asma-prototype/demo_data && echo "EXISTS" || echo "MISSING"
test -d /usr2/people/alex.styer/public_html && echo "EXISTS" || echo "MISSING"

# Check container mounts
podman inspect asma-proto-v10 --format '{{json .Mounts}}' | python3 -m json.tool
```

**If missing, contact sysadmin or restore from backup.**

### Failure Mode 4: Port Already in Use

**Symptoms:**
- Container fails to start
- Error: "port is already allocated"

**Root Cause:**
- Another process using port 8765
- Old container instance still running

**Fix:**
```bash
# Find process using port
ss -ltnp | grep 8765

# Stop conflicting container
podman ps -a | grep -E "asma|8765"
podman stop <conflicting_container_name>

# Start correct container
podman start asma-proto-v10
```

### Failure Mode 5: Systemd Unit Not Starting

**Symptoms:**
- Container not starting after reboot
- `systemctl --user status container-asma-proto.service` shows failed

**Root Cause:**
- Unit not enabled
- Linger not enabled
- Unit file path incorrect

**Fix:**
- See Section 13: Auto-Restart Hardening

---

## 8. DEPRECATED UNITS

### Deprecated Unit: `container-asma-proto.service` (Old Version)

**Location:** `/usr2/people/spencerlong/.config/systemd/user/container-asma-proto.service`

**Status:** DISABLED (should remain disabled)

**Issues:**
- References wrong container name: `asma-proto` (should be `asma-proto-v10`)
- References pod: `pod_asma-prototype` (container is standalone, not in pod)
- Uses `--network=host` (container uses port mapping)
- Uses `Type=notify` with `Restart=always` (should use `Type=oneshot` with `RemainAfterExit=yes`)

**Action:**
- **DO NOT ENABLE** this unit
- New unit template is in repo: `ops/thar/asma_hardening_20260116/systemd_user_units/container-asma-proto.service`
- Install new unit following Section 13

**Verification:**
```bash
systemctl --user status container-asma-proto.service
# Should show: disabled (not enabled)
```

---

## 9. SINGLE OWNER RULE

### Principle

**Each container lifecycle must have ONE orchestrator.** Avoid "dueling orchestrators" where multiple systems try to manage the same container.

### Current Owner

**Systemd user service:** `container-asma-proto.service`

### What This Means

- **DO NOT** use `podman run --restart unless-stopped` for `asma-proto-v10`
- **DO NOT** enable multiple systemd units for the same container
- **DO NOT** manually start/stop container if systemd unit is enabled (use `systemctl --user`)

### Verification

```bash
# Check if systemd owns the container
systemctl --user is-enabled container-asma-proto.service
# Should return: enabled

# Check container restart policy
podman inspect asma-proto-v10 --format '{{.HostConfig.RestartPolicy.Name}}'
# Should return: "" (no restart policy, systemd manages it)
```

---

## 10. WATCHDOG BEHAVIOR

### Overview

The watchdog (`asma-watchdog.timer`) runs every 2 minutes and checks container health.

### Health Check

- **Endpoint:** `http://127.0.0.1:8765/health`
- **Healthy codes:** `200`
- **Unhealthy:** Any other code or connection failure

### Cooldown

- **Duration:** 10 minutes (600 seconds)
- **Purpose:** Prevents rapid restart loops
- **Behavior:** If unhealthy but cooldown active, watchdog exits 0 (not an error)

### Recovery Actions

1. **If systemd unit enabled:** Restart via `systemctl --user restart container-asma-proto.service`
2. **If systemd unit not enabled:** Restart via `podman restart asma-proto-v10` or `podman start asma-proto-v10`

### Exit Codes

- **0:** Healthy or cooldown active (expected)
- **1:** Unhealthy after recovery attempt (requires manual intervention)

### Logs

```bash
journalctl --user -u asma-watchdog.service -n 50
```

**Example healthy log:**
```
Jan 16 17:00:00 thar asma-watchdog[12345]: 2026-01-16 17:00:00 [INFO] Starting health check for http://127.0.0.1:8765/health
Jan 16 17:00:00 thar asma-watchdog[12345]: 2026-01-16 17:00:00 [INFO] Backend is healthy (status=200)
```

**Example recovery log:**
```
Jan 16 17:00:00 thar asma-watchdog[12345]: 2026-01-16 17:00:00 [ERROR] Backend is unhealthy (status=000)
Jan 16 17:00:00 thar asma-watchdog[12345]: 2026-01-16 17:00:00 [INFO] Cooldown file updated (next restart allowed after 600 seconds)
Jan 16 17:00:00 thar asma-watchdog[12345]: 2026-01-16 17:00:00 [INFO] systemd owns asma-proto-v10; restarting via systemctl
Jan 16 17:00:20 thar asma-watchdog[12345]: 2026-01-16 17:00:20 [INFO] Backend recovered after recovery action (status=200)
```

### Disabling Watchdog

```bash
systemctl --user disable --now asma-watchdog.timer
```

### Re-enabling Watchdog

```bash
systemctl --user enable --now asma-watchdog.timer
systemctl --user status asma-watchdog.timer
```

---

## 11. LINGER (USER SESSION PERSISTENCE)

### What Is Linger?

Linger allows user systemd services to run after logout. Required for auto-start on boot.

### Check Status

```bash
loginctl show-user spencerlong | grep Linger
# Expected: Linger=yes
```

### Enable Linger

```bash
loginctl enable-linger spencerlong
```

### Verify

```bash
loginctl show-user spencerlong | grep Linger
# Should show: Linger=yes
```

**Note:** Linger is typically enabled once and persists. Check if already enabled before enabling.

---

## 12. AUTO-RESTART HARDENING

### Overview

Auto-restart is implemented via systemd user services. Containers start automatically after server reboot.

### Components

1. **Container unit:** `container-asma-proto.service` (starts container)
2. **Watchdog timer:** `asma-watchdog.timer` (monitors health)
3. **Linger:** Enabled (allows user services to run after logout)

### Installation Steps

#### Step 1: Install Container Unit

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

#### Step 2: Install Watchdog

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

#### Step 3: Verify Linger

```bash
loginctl show-user spencerlong | grep Linger
# If not enabled: loginctl enable-linger spencerlong
```

### Verification After Reboot

```bash
# After server reboot, verify containers started
podman ps | grep asma-proto-v10

# Verify systemd units are active
systemctl --user status container-asma-proto.service
systemctl --user status asma-watchdog.timer

# Verify health
curl -I http://127.0.0.1:8765/health
```

### Rollback

```bash
# Disable auto-start
systemctl --user disable --now container-asma-proto.service
systemctl --user disable --now asma-watchdog.timer

# Containers will not auto-start on next reboot
```

---

## 13. MAINTENANCE PROCEDURES

### Updating Container Image

```bash
# 1. Pull latest code
cd /usr2/people/spencerlong/asma-prototype
git pull origin main

# 2. Build new image
podman build -t localhost/asma-prototype:main-latest -f Dockerfile .

# 3. Stop container
systemctl --user stop container-asma-proto.service
# OR: podman stop asma-proto-v10

# 4. Remove old container (preserves volumes)
podman rm asma-proto-v10

# 5. Create new container with same name and config
podman run -d --name asma-proto-v10 -p 8765:5000 \
  -v /opt/shared/spencerlong/asma-prototype/demo_data:/app/demo_data \
  -v /usr2/people/alex.styer/public_html:/app/alex_public_html:ro \
  -e ASMA_DATA_DIR=/app/demo_data \
  -e ALEX_PUBLIC_HTML_DIR=/app/alex_public_html \
  localhost/asma-prototype:main-latest

# 6. Start via systemd (if enabled)
systemctl --user start container-asma-proto.service
# OR: podman start asma-proto-v10

# 7. Verify
curl -I http://127.0.0.1:8765/health
```

### Viewing Logs

```bash
# Container logs
podman logs --tail 100 asma-proto-v10

# Systemd unit logs
journalctl --user -u container-asma-proto.service -n 50

# Watchdog logs
journalctl --user -u asma-watchdog.service -n 50
```

### Stopping Service

```bash
# Stop container via systemd
systemctl --user stop container-asma-proto.service

# OR stop directly
podman stop asma-proto-v10
```

### Starting Service

```bash
# Start container via systemd
systemctl --user start container-asma-proto.service

# OR start directly
podman start asma-proto-v10
```

---

## 14. TROUBLESHOOTING

### Container Won't Start

1. Check container status: `podman ps -a | grep asma-proto-v10`
2. Check logs: `podman logs --tail 50 asma-proto-v10`
3. Check systemd: `systemctl --user status container-asma-proto.service`
4. Check port: `ss -ltnp | grep 8765`
5. Check volumes: `podman inspect asma-proto-v10 --format '{{json .Mounts}}'`

### Health Check Failing

1. Check container is running: `podman ps | grep asma-proto-v10`
2. Test health endpoint: `curl -v http://127.0.0.1:8765/health`
3. Check logs: `podman logs --tail 50 asma-proto-v10`
4. Check watchdog logs: `journalctl --user -u asma-watchdog.service -n 50`

### External URL Not Working

1. Check local health: `curl -I http://127.0.0.1:8765/health`
2. Check nginx: `curl -k -I https://protect.qb3.berkeley.edu/asma/`
3. If 401: Expected (Basic auth)
4. If 502/503: Check container is running
5. Contact sysadmin if nginx issue suspected

---

## 15. ROLLBACK PROCEDURES

### Rollback Container Unit

```bash
systemctl --user disable --now container-asma-proto.service
systemctl --user stop container-asma-proto.service
```

### Rollback Watchdog

```bash
systemctl --user disable --now asma-watchdog.timer
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

---

## 16. CONTACTS & ESCALATION

### For ASMA Issues

- **Primary:** Spencer Long
- **Repository:** `/usr2/people/spencerlong/asma-prototype`
- **Ops Directory:** `ops/`

### For Infrastructure Issues

- **Nginx:** Contact sysadmin
- **THAR server:** Contact sysadmin
- **Podman/containers:** Contact sysadmin

---

**End of Runbook**
