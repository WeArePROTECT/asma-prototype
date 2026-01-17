#!/bin/bash
# ASMA Prototype Health Watchdog
# Checks backend health and restarts asma-proto-v10 if unhealthy
# Logs all actions to journald
# Hardened: cooldown, container-aware, accepts 200 as healthy
#
# IMPORTANT: This is a TEMPLATE/REFERENCE copy.
# Live location on THAR: /usr2/people/spencerlong/asma-prototype/ops/watchdog/asma_watchdog.sh
#
# Installation:
# 1. Copy to desired location (e.g., /usr2/people/spencerlong/asma-prototype/ops/watchdog/asma_watchdog.sh)
# 2. Edit COOLDOWN_FILE path if needed (line 14)
# 3. Make executable: chmod +x asma_watchdog.sh
# 4. Update asma-watchdog.service ExecStart path to match
# 5. Test manually: systemctl --user start asma-watchdog.service
#
# Behavior:
# - Checks backend health every 2 minutes (via timer)
# - Accepts HTTP 200 as healthy
# - Cooldown: max one recovery attempt per 10 minutes
# - ASMA has no database - no DB guardrail needed
# - Systemd-aware: uses systemctl if container-asma-proto.service enabled, else podman
# - Exit codes: 0 for healthy/cooldown, 1 for actual failures
#
# Logs: journalctl --user -u asma-watchdog.service -n 50
# Disable: systemctl --user disable --now asma-watchdog.timer

set -euo pipefail

HEALTH_URL="http://127.0.0.1:8765/health"
CURL_TIMEOUT_CONNECT=3
CURL_TIMEOUT_TOTAL=5
RESTART_WAIT=20
COOLDOWN_SECONDS=600
COOLDOWN_FILE="/usr2/people/spencerlong/asma-prototype/ops/watchdog/.asma_last_restart_epoch"

# Log function that writes to journald
log() {
    echo "$1" | systemd-cat -t asma-watchdog -p info
    echo "$(/usr/bin/date '+%Y-%m-%d %H:%M:%S') [INFO] $1"
}

log_error() {
    echo "$1" | systemd-cat -t asma-watchdog -p err
    echo "$(/usr/bin/date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >&2
}

# Check backend health - returns HTTP status code
check_health_status() {
    local status
    # Redirect stderr to /dev/null to avoid capturing curl error messages
    status=$(/usr/bin/curl -sS -o /dev/null -w '%{http_code}' \
        --connect-timeout "${CURL_TIMEOUT_CONNECT}" \
        --max-time "${CURL_TIMEOUT_TOTAL}" \
        "${HEALTH_URL}" 2>/dev/null || echo "000")
    echo "${status}"
}

# Check if status code is considered healthy
# ASMA health endpoint returns 200 when healthy
is_healthy_status() {
    local status="$1"
    case "${status}" in
        200)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Check if container is running
is_container_running() {
    /usr/bin/podman ps --format '{{.Names}}' | /usr/bin/grep -qx 'asma-proto-v10'
}

# Check cooldown
is_cooldown_active() {
    if [ ! -f "${COOLDOWN_FILE}" ]; then
        return 1
    fi
    
    local last_restart
    local current_time
    local elapsed
    
    last_restart=$(cat "${COOLDOWN_FILE}" 2>/dev/null || echo "0")
    current_time=$(/usr/bin/date +%s)
    elapsed=$((current_time - last_restart))
    
    if [ "${elapsed}" -lt "${COOLDOWN_SECONDS}" ]; then
        return 0
    else
        return 1
    fi
}

# Write current epoch to cooldown file
update_cooldown() {
    /usr/bin/date +%s > "${COOLDOWN_FILE}"
    log "Cooldown file updated (next restart allowed after ${COOLDOWN_SECONDS} seconds)"
}

# Check if systemd owns the container lifecycle
systemd_is_owner_enabled() {
    /usr/bin/systemctl --user is-enabled container-asma-proto.service >/dev/null 2>&1
}

# Main execution
log "Starting health check for ${HEALTH_URL}"

# Get HTTP status
status=$(check_health_status)

# Check if healthy
if is_healthy_status "${status}"; then
    log "Backend is healthy (status=${status})"
    exit 0
fi

log_error "Backend is unhealthy (status=${status})"

# Check cooldown
if is_cooldown_active; then
    last_restart=$(cat "${COOLDOWN_FILE}")
    current_time=$(/usr/bin/date +%s)
    elapsed=$((current_time - last_restart))
    remaining=$((COOLDOWN_SECONDS - elapsed))
    
    log "Unhealthy but cooldown active (${remaining} seconds remaining); skipping recovery; manual intervention may be required"
    exit 0
fi

# ASMA has no database - no DB guardrail needed
# Proceed directly to recovery

# Determine recovery action based on systemd ownership and container state
update_cooldown

if systemd_is_owner_enabled; then
    # Systemd owns the container lifecycle - use systemctl
    log "systemd owns asma-proto-v10; restarting via systemctl"
    
    if /usr/bin/systemctl --user restart container-asma-proto.service; then
        log "Successfully restarted asma-proto-v10 via systemctl"
    else
        log_error "Failed to restart asma-proto-v10 via systemctl"
        exit 1
    fi
else
    # Systemd does not own it - use podman directly
    if is_container_running; then
        log "asma-proto-v10 is running but unhealthy; restarting via podman"
        
        if /usr/bin/podman restart asma-proto-v10; then
            log "Successfully restarted asma-proto-v10 container via podman"
        else
            log_error "Failed to restart asma-proto-v10 container via podman"
            exit 1
        fi
    else
        log "asma-proto-v10 is not running; starting via podman"
        
        if /usr/bin/podman start asma-proto-v10; then
            log "Successfully started asma-proto-v10 container via podman"
        else
            log_error "Failed to start asma-proto-v10 container via podman"
            exit 1
        fi
    fi
fi

# Wait for container to initialize
log "Waiting ${RESTART_WAIT} seconds for container to initialize"
/usr/bin/sleep "${RESTART_WAIT}"

# Re-check health
status2=$(check_health_status)

if is_healthy_status "${status2}"; then
    log "Backend recovered after recovery action (status=${status2})"
    exit 0
else
    log_error "Backend still unhealthy after recovery action (status=${status2}); manual intervention required"
    exit 1
fi
