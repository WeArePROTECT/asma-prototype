# ASMA Prototype Operations

This directory contains operational procedures, deployment templates, and diagnostics for the ASMA Prototype platform.

## Directory Structure

```
ops/
├── README.md (this file)
└── thar/
    ├── README.md (THAR server-specific ops)
    └── asma_hardening_20260116/
        ├── README.md (Hardening packet documentation)
        ├── systemd_user_units/ (systemd unit templates)
        ├── watchdog/ (health monitoring scripts)
        └── diagnostics/ (historical diagnostics and reports)
```

## Quick Links

- **THAR Server Ops:** [ops/thar/README.md](thar/README.md)
- **ASMA Hardening (2026-01-16):** [ops/thar/asma_hardening_20260116/README.md](thar/asma_hardening_20260116/README.md)
- **Master Runbook:** [docs/runbooks/THAR_ASMA_MASTER_RUNBOOK.md](../docs/runbooks/THAR_ASMA_MASTER_RUNBOOK.md)

## What's Here

### THAR Server Operations

The `thar/` directory contains server-specific operational artifacts for the THAR production server (protect.qb3.berkeley.edu).

### Hardening Packets

Each hardening packet (e.g., `asma_hardening_20260116/`) contains:
- Systemd unit templates for auto-start
- Watchdog scripts for health monitoring
- Installation and verification procedures
- Historical diagnostics from deployment

### Diagnostics

Diagnostics files are organized by hardening packet and contain:
- Deployment maps
- Phase-by-phase validation reports
- Merge and production deployment reports
- Historical troubleshooting notes

## Usage

1. **For THAR operations:** See [ops/thar/README.md](thar/README.md)
2. **For specific hardening packet:** Navigate to the packet directory and read its README.md
3. **For comprehensive procedures:** See the master runbook in `docs/runbooks/`

## Notes

- All paths in templates are absolute paths for THAR server
- Templates are reference copies - deployed units may use different paths
- Diagnostics are historical records and may reference old paths
- No secrets or credentials are stored in this directory
