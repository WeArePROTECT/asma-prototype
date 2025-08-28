def test_preview_formulation(client):
    body = {"organisms": ["ASMA-001", "ASMA-002"], "prebiotics": ["PB001"]}
    r = client.post("/formulations/preview", json=body)
    assert r.status_code == 200
    data = r.json()
    assert "score_predicted" in data and 0.0 <= data["score_predicted"] <= 1.0
    assert "notes" in data
