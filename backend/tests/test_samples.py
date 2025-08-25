def test_get_samples_filter_by_patient(client):
    r = client.get("/samples", params={"patient_id": "P001"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(s["patient_id"] == "P001" for s in data)
