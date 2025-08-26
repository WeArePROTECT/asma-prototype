def test_bin_pathways_smoke(client):
    # Get any bin_id
    bins = client.get("/bins").json()
    assert isinstance(bins, list) and bins, "No bins found in demo_data"
    bid = bins[0]["bin_id"]

    r = client.get(f"/bins/{bid}/pathways")
    assert r.status_code == 200
    data = r.json()
    assert data["bin_id"] == bid
    assert "pathways" in data and isinstance(data["pathways"], list)