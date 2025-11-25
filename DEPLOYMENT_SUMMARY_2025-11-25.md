# Taxonomy Endpoints Deployment Summary

**Date:** 2025-11-25  
**Branch:** main  
**Status:** ✅ Production-ready and deployed

## Quick Links

- **Taxonomic Table Viewer:** https://protect.qb3.berkeley.edu/asma/api/taxonomy/table
- **Isolate Treemap Viewer:** https://protect.qb3.berkeley.edu/asma/api/taxonomy/treemap
- **Taxonomy Data (TSV):** https://protect.qb3.berkeley.edu/asma/api/taxonomy/tsv

## What Was Deployed

Successfully integrated Alex Styer's taxonomic table and isolate treemap viewers into the ASMA platform:

1. **Taxonomic Table Viewer** - Interactive DataTables view of ASMA isolate taxonomy
2. **Isolate Treemap Viewer** - Plotly treemap visualization of taxonomic hierarchy  
3. **Taxonomy Data Endpoint** - Raw TSV data with Last-Modified header support
4. **Logo Endpoint** - PROTECT logo for table viewer

## Implementation Summary

### Commits Merged to Main

1. `0d06f83` - Add taxonomy endpoints for Alex's taxonomic table and isolate treemap viewers
2. `ab022d0` - Fix taxonomy table paths to include /asma prefix for correct routing
3. `20bd85a` - Add Last-Modified header support for taxonomy TSV endpoint
4. `dae4bbe` - Update documentation with deployment details and production status

### Files Changed

- `backend/app/main.py` - Added 4 new API endpoints with error handling
- `backend/tests/test_taxonomy.py` - Comprehensive test suite (11 test cases)
- `README.md` - Updated with new functionality section
- `TAXONOMY_ENDPOINTS_IMPLEMENTATION.md` - Full implementation documentation

### Container Configuration

- **Image:** `localhost/asma-prototype:main-latest`
- **Container Name:** `asma-proto-v10`
- **Status:** Running and healthy
- **Port:** 5000 (proxied via nginx to https://protect.qb3.berkeley.edu/asma/)

### Volume Mounts

```bash
-v /opt/shared/spencerlong/asma-prototype/demo_data:/app/demo_data
-v /usr2/people/alex.styer/public_html:/app/alex_public_html:ro
```

### Environment Variables

```bash
ASMA_DATA_DIR=/app/demo_data
ALEX_PUBLIC_HTML_DIR=/app/alex_public_html
```

## Verification Tests

All endpoints verified working:
- ✅ `/api/taxonomy/tsv` - Returns TSV data with Last-Modified header
- ✅ `/api/taxonomy/table` - Returns modified HTML with correct API paths
- ✅ `/api/taxonomy/treemap` - Returns treemap HTML viewer
- ✅ `/api/taxonomy/logo` - Returns PNG logo image

## Key Features

1. **Automatic Sync** - Reads directly from Alex's directory, stays in sync automatically
2. **Last-Modified Header** - Shows when taxonomy data was last updated
3. **Dynamic Path Modification** - HTML paths updated on-the-fly to work under /asma/ route
4. **Comprehensive Error Handling** - Handles missing files, permissions, encoding errors
5. **Production Ready** - Full test coverage, proper HTTP headers, caching

## Resource Usage

- **Container Build:** ~2 minutes (mostly cached layers)
- **Container Runtime:** Minimal - serves static files and API responses
- **Memory:** < 200MB typical
- **CPU:** Low - only on-demand requests

## Maintenance

### Updating Taxonomy Data

When Alex updates the taxonomy.tsv file using his R script (`update-asma-summary.R`):
- File modification time updates automatically
- Last-Modified header reflects new timestamp
- Page shows updated "Last updated" date on next load
- No container restart needed (reads file on each request)

### Container Updates

To update the container with new code:

```bash
cd /usr2/people/spencerlong/asma-prototype
git pull origin main
podman build -t localhost/asma-prototype:main-latest -f Dockerfile .
podman stop asma-proto-v10
podman rm asma-proto-v10
podman run -d --name asma-proto-v10 -p 8765:5000 \
  -v /opt/shared/spencerlong/asma-prototype/demo_data:/app/demo_data \
  -v /usr2/people/alex.styer/public_html:/app/alex_public_html:ro \
  -e ASMA_DATA_DIR=/app/demo_data \
  -e ALEX_PUBLIC_HTML_DIR=/app/alex_public_html \
  --restart unless-stopped \
  localhost/asma-prototype:main-latest
```

**⚠️ CRITICAL:** Always include both volume mounts and both environment variables. Missing either will cause the taxonomy endpoints to fail.

### Required Configuration

The container **MUST** have:
1. **Volume mount:** `-v /usr2/people/alex.styer/public_html:/app/alex_public_html:ro`
2. **Environment variable:** `-e ALEX_PUBLIC_HTML_DIR=/app/alex_public_html`

Without these, the taxonomy endpoints will return 404 errors. The application will log warnings at startup if these are missing.

## Documentation

- **Full Implementation Details:** See `TAXONOMY_ENDPOINTS_IMPLEMENTATION.md`
- **API Documentation:** See endpoint docstrings in `backend/app/main.py`
- **Test Suite:** `backend/tests/test_taxonomy.py`

## Success Criteria Met

✅ All endpoints accessible under /asma/ route  
✅ Taxonomic table displays data correctly  
✅ Treemap visualization works  
✅ Last-Modified date displays correctly  
✅ Logo loads properly  
✅ Code merged to main branch  
✅ Container running from main branch  
✅ Documentation complete  
✅ Tests written and passing  

---

**Deployed by:** AI Assistant (Cursor)  
**Reviewed and approved by:** Spencer Long  
**Deployment Date:** 2025-11-25

