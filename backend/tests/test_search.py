def test_search_patients(client):
    r = client.get("/search", params={"q": "P001"})
    assert r.status_code == 200
    payload = r.json()
    assert "patients" in payload
    assert any(p["patient_id"] == "P001" for p in payload["patients"])
