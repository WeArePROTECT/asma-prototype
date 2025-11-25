# Taxonomy Endpoints Implementation Documentation

**Date:** 2025-11-25  
**Branch:** dev  
**Status:** Completed

## Overview

This document describes the implementation of API endpoints to serve Alex Styer's taxonomic table viewer and isolate treemap viewer within the ASMA FastAPI backend. These endpoints integrate Alex's existing visualization tools into the ASMA platform, making them accessible under the `https://protect.qb3.berkeley.edu/asma/` root domain.

## What Was Changed

### Files Modified

1. **`backend/app/main.py`**
   - Added 4 new API endpoints for taxonomy data and viewers
   - Added constants for Alex's public_html directory paths
   - Added error handling and edge case management

### Files Created

1. **`backend/tests/test_taxonomy.py`**
   - Comprehensive test suite for all taxonomy endpoints
   - Tests cover success cases, missing files, permission errors, and path modifications

### Git Branch

- Work completed on `dev` branch (created from `main`)

## Implementation Details

### New API Endpoints

#### 1. `GET /api/taxonomy/tsv`
- **Purpose:** Serve the taxonomy.tsv file from Alex's directory
- **Returns:** TSV content with proper content-type headers
- **Data Source:** `/usr2/people/alex.styer/public_html/taxonomy.tsv`
- **Content-Type:** `text/tab-separated-values`
- **Cache-Control:** `public, max-age=3600` (1 hour)

#### 2. `GET /api/taxonomy/logo`
- **Purpose:** Serve the logo-banner.png image for the taxonomic table viewer
- **Returns:** PNG image file
- **Data Source:** `/usr2/people/alex.styer/public_html/logo-banner.png`
- **Content-Type:** `image/png`
- **Cache-Control:** `public, max-age=86400` (24 hours)

#### 3. `GET /api/taxonomy/table`
- **Purpose:** Serve the tax-table.html viewer with modified paths to use API endpoints
- **Returns:** HTML content with relative paths replaced with API endpoint paths
- **Data Source:** `/usr2/people/alex.styer/public_html/tax-table.html`
- **Modifications Made:**
  - `fetch("taxonomy.tsv"` → `fetch("/api/taxonomy/tsv"`
  - `Papa.parse("taxonomy.tsv"` → `Papa.parse("/api/taxonomy/tsv"`
  - `src="logo-banner.png"` → `src="/api/taxonomy/logo"`
- **Content-Type:** `text/html`
- **Cache-Control:** `public, max-age=3600` (1 hour)

#### 4. `GET /api/taxonomy/treemap`
- **Purpose:** Serve the protect-isolate-treemap.html viewer for isolate treemap visualization
- **Returns:** HTML file (no modifications needed - data is embedded)
- **Data Source:** `/usr2/people/alex.styer/public_html/protect-isolate-treemap.html`
- **Content-Type:** `text/html`
- **Cache-Control:** `public, max-age=3600` (1 hour)

### Configuration

The path to Alex's public_html directory is configurable via environment variable:
- **Environment Variable:** `ALEX_PUBLIC_HTML_DIR`
- **Default:** `/usr2/people/alex.styer/public_html`

This allows for flexibility in different deployment environments while maintaining a sensible default.

### Error Handling

All endpoints implement comprehensive error handling for:

1. **Missing Files (404)**
   - Checks if file exists before attempting to read
   - Checks if path is actually a file (not a directory)
   - Returns clear error messages with full path

2. **Permission Errors (403)**
   - Catches `PermissionError` exceptions
   - Returns appropriate 403 status with descriptive message

3. **Encoding Errors (500)**
   - Catches `UnicodeDecodeError` for non-UTF-8 files
   - Returns error indicating encoding issue

4. **General Errors (500)**
   - Catches all other exceptions
   - Returns generic error with exception message

### Edge Cases Covered

- Empty files (returns empty content, which is acceptable)
- Non-existent directory
- Directory exists but file doesn't
- Path exists but is a directory, not a file
- Permission denied errors
- Unicode decoding errors for non-UTF-8 files
- Malformed HTML/TSV (served as-is, validation not required)

## Why The Changes Were Needed

### Problem Statement

Alex Styer maintains taxonomic table and isolate treemap viewers at:
- `https://genomics.lbl.gov/~alex.styer/tax-table.html`
- `https://genomics.lbl.gov/~alex.styer/protect-isolate-treemap.html`

These viewers needed to be:
1. Consolidated under the ASMA platform at `https://protect.qb3.berkeley.edu/asma/`
2. Integrated into the existing FastAPI backend architecture
3. Updated to use API endpoints instead of relative file paths
4. Kept in sync with Alex's data directory automatically

### Solution Approach

Instead of copying files and maintaining duplicates, we:
1. Read directly from Alex's directory (stays in sync automatically)
2. Serve via FastAPI endpoints (consistent with ASMA architecture)
3. Modify HTML on-the-fly for tax-table.html (only file that needs path updates)
4. Serve treemap.html as-is (data is embedded, no external dependencies)

## How It Was Solved

1. **Added API Endpoints:** Created FastAPI route handlers for all required resources
2. **Dynamic Path Modification:** tax-table.html is modified on-the-fly to replace relative paths with API endpoints
3. **Error Handling:** Comprehensive error handling ensures graceful degradation
4. **Testing:** Full test coverage for all endpoints and edge cases
5. **Configuration:** Environment variable support for flexible deployment

## Usage Examples

### Accessing the Taxonomic Table Viewer
```
https://protect.qb3.berkeley.edu/asma/api/taxonomy/table
```

### Accessing the Isolate Treemap Viewer
```
https://protect.qb3.berkeley.edu/asma/api/taxonomy/treemap
```

### Programmatic Access to Taxonomy Data
```python
import requests

response = requests.get("https://protect.qb3.berkeley.edu/asma/api/taxonomy/tsv")
tsv_content = response.text
```

## Dependencies

- No new Python dependencies required
- Uses existing FastAPI components:
  - `FileResponse` for serving static files
  - `Response` for serving modified content
  - `HTTPException` for error handling

## Testing

Comprehensive tests are located in `backend/tests/test_taxonomy.py`:
- Success cases for all endpoints
- Missing file scenarios
- Permission error handling
- Path modification verification
- Unicode error handling

Run tests with:
```bash
pytest backend/tests/test_taxonomy.py -v
```

## Future Considerations

1. **Caching Strategy:** Currently using HTTP cache headers, could add Redis/memory caching for frequently accessed files
2. **Authentication:** No authentication currently - add if needed for production
3. **Rate Limiting:** Consider adding rate limiting if these endpoints see heavy traffic
4. **Monitoring:** Add logging/metrics for endpoint usage
5. **Data Validation:** Currently no validation of TSV content - could add if data quality becomes a concern

## Related Files

- Alex's original files: `/usr2/people/alex.styer/public_html/`
- Alex's R script for regeneration: `/usr2/people/alex.styer/protect/scripts/update-asma-summary.R`
- Tests: `backend/tests/test_taxonomy.py`
- Main application: `backend/app/main.py`

## Notes for Future Developers

1. **Path Configuration:** Remember that `ALEX_PUBLIC_HTML_DIR` can be set as an environment variable
2. **File Updates:** Alex regenerates taxonomy.tsv and HTML files - our endpoints automatically pick up changes (subject to cache headers)
3. **HTML Modifications:** If tax-table.html structure changes, update the path replacement logic in `get_taxonomy_table()`
4. **CORS:** Existing CORS middleware handles cross-origin requests - no changes needed

## Deployment Notes

- Ensure the ASMA container has read access to `/usr2/people/alex.styer/public_html/`
- No additional volume mounts needed if using default path
- Cache headers are conservative (1 hour) - adjust if needed for more frequent updates

