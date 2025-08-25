def test_download_bins_csv(client):
    r = client.get("/download/bins.csv")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("text/csv")
    text = r.text
    # basic sanity: header and at least one known id present
    assert "bin_id" in text
    assert "B001" in text
