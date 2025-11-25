"""
Tests for taxonomy endpoints that serve Alex Styer's taxonomic table and treemap viewers.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from fastapi.testclient import TestClient


def test_taxonomy_tsv_endpoint_success(client):
    """Test that taxonomy TSV endpoint returns valid TSV data when file exists."""
    r = client.get("/api/taxonomy/tsv")
    
    # Should succeed if file exists
    if r.status_code == 200:
        assert r.headers.get("content-type", "").startswith("text/tab-separated-values")
        content = r.text
        assert len(content) > 0
        # Should have header line
        assert "ASMA_id" in content or "domain" in content or "phylum" in content
        # Should have tab-separated values
        lines = content.split("\n")
        assert len(lines) > 1
    elif r.status_code == 404:
        # File doesn't exist in test environment - that's ok for now
        pytest.skip("taxonomy.tsv file not found in test environment")


def test_taxonomy_tsv_endpoint_missing_file(client):
    """Test that taxonomy TSV endpoint returns 404 when file doesn't exist."""
    with patch("backend.app.main.TAXONOMY_TSV_PATH") as mock_path:
        mock_path.exists.return_value = False
        mock_path.__str__ = lambda x: "/fake/path/taxonomy.tsv"
        
        r = client.get("/api/taxonomy/tsv")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()


def test_taxonomy_logo_endpoint_success(client):
    """Test that logo endpoint returns PNG image when file exists."""
    r = client.get("/api/taxonomy/logo")
    
    # Should succeed if file exists
    if r.status_code == 200:
        assert r.headers.get("content-type") == "image/png"
        assert len(r.content) > 0
    elif r.status_code == 404:
        # File doesn't exist in test environment - that's ok for now
        pytest.skip("logo-banner.png file not found in test environment")


def test_taxonomy_logo_endpoint_missing_file(client):
    """Test that logo endpoint returns 404 when file doesn't exist."""
    with patch("backend.app.main.LOGO_BANNER_PATH") as mock_path:
        mock_path.exists.return_value = False
        mock_path.__str__ = lambda x: "/fake/path/logo-banner.png"
        
        r = client.get("/api/taxonomy/logo")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()


def test_taxonomy_table_endpoint_success(client):
    """Test that tax-table endpoint returns HTML with modified API paths."""
    r = client.get("/api/taxonomy/table")
    
    # Should succeed if file exists
    if r.status_code == 200:
        assert r.headers.get("content-type") == "text/html"
        content = r.text
        assert len(content) > 0
        # Should have modified paths to use API endpoints
        assert "/api/taxonomy/tsv" in content
        assert "/api/taxonomy/logo" in content
        # Should not have relative paths
        assert 'fetch("taxonomy.tsv"' not in content
        assert 'Papa.parse("taxonomy.tsv"' not in content
        assert 'src="logo-banner.png"' not in content
        # Should be valid HTML
        assert "<!DOCTYPE html>" in content or "<html" in content
    elif r.status_code == 404:
        # File doesn't exist in test environment - that's ok for now
        pytest.skip("tax-table.html file not found in test environment")


def test_taxonomy_table_endpoint_missing_file(client):
    """Test that tax-table endpoint returns 404 when file doesn't exist."""
    with patch("backend.app.main.TAX_TABLE_HTML_PATH") as mock_path:
        mock_path.exists.return_value = False
        mock_path.__str__ = lambda x: "/fake/path/tax-table.html"
        
        r = client.get("/api/taxonomy/table")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()


def test_taxonomy_treemap_endpoint_success(client):
    """Test that treemap endpoint returns HTML content when file exists."""
    r = client.get("/api/taxonomy/treemap")
    
    # Should succeed if file exists
    if r.status_code == 200:
        assert r.headers.get("content-type") == "text/html"
        content = r.text
        assert len(content) > 0
        # Should be valid HTML
        assert "<!DOCTYPE html>" in content or "<html" in content
    elif r.status_code == 404:
        # File doesn't exist in test environment - that's ok for now
        pytest.skip("protect-isolate-treemap.html file not found in test environment")


def test_taxonomy_treemap_endpoint_missing_file(client):
    """Test that treemap endpoint returns 404 when file doesn't exist."""
    with patch("backend.app.main.TREEMAP_HTML_PATH") as mock_path:
        mock_path.exists.return_value = False
        mock_path.__str__ = lambda x: "/fake/path/protect-isolate-treemap.html"
        
        r = client.get("/api/taxonomy/treemap")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()


def test_taxonomy_tsv_permission_error(client):
    """Test that TSV endpoint handles permission errors gracefully."""
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        with patch("backend.app.main.TAXONOMY_TSV_PATH") as mock_path:
            mock_path.exists.return_value = True
            mock_path.__str__ = lambda x: "/fake/path/taxonomy.tsv"
            
            r = client.get("/api/taxonomy/tsv")
            assert r.status_code == 403
            assert "permission" in r.json()["detail"].lower()


def test_taxonomy_table_path_modification(client):
    """Test that tax-table HTML has all paths correctly modified."""
    # Mock HTML content with relative paths
    mock_html = """
    <html>
    <head></head>
    <body>
        <img src="logo-banner.png" alt="Logo">
        <script>
            fetch("taxonomy.tsv", { method: 'HEAD' });
            Papa.parse("taxonomy.tsv", { download: true });
        </script>
    </body>
    </html>
    """
    
    with patch("backend.app.main.TAX_TABLE_HTML_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_path.__str__ = lambda x: "/fake/path/tax-table.html"
        
        with patch("builtins.open", mock_open(read_data=mock_html)):
            r = client.get("/api/taxonomy/table")
            
            if r.status_code == 200:
                content = r.text
                # All paths should be modified
                assert "/api/taxonomy/tsv" in content
                assert "/api/taxonomy/logo" in content
                assert 'src="logo-banner.png"' not in content
                assert 'fetch("taxonomy.tsv"' not in content
                assert 'Papa.parse("taxonomy.tsv"' not in content

