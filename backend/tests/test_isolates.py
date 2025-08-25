def test_isolate_omics_endpoint(client):
    r = client.get("/isolates/I003/omics")
    assert r.status_code == 200
    payload = r.json()
    assert payload["isolate_id"] == "I003"
    assert "growth_media" in payload
    assert "metabolite_markers" in payload and isinstance(payload["metabolite_markers"], list)
