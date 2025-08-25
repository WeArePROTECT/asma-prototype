def test_bin_pathways_endpoint(client):
    r = client.get("/bins/B001/pathways")
    assert r.status_code == 200
    payload = r.json()
    assert payload["bin_id"] == "B001"
    assert "pathways" in payload and isinstance(payload["pathways"], list)
    assert len(payload["pathways"]) >= 1
    # Each pathway dict should have pathway key, score may be None for fallback
    assert "pathway" in payload["pathways"][0]
