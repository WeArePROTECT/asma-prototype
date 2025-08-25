def test_get_patients(client):
    r = client.get("/patients")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    # Expect our mock patients to be present
    ids = {p["patient_id"] for p in data}
    assert "P001" in ids and "P003" in ids
