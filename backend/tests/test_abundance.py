def test_sample_abundance_smoke(client):
    # Get any sample_id
    samples = client.get("/samples").json()
    assert isinstance(samples, list) and samples, "No samples found in demo_data"
    sid = samples[0]["sample_id"]

    r = client.get(f"/samples/{sid}/abundance")
    assert r.status_code == 200
    data = r.json()
    assert data["sample_id"] == sid
    assert "bins" in data and isinstance(data["bins"], list)
    assert "total_abundance" in data