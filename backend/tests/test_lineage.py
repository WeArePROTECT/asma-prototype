def test_lineage_by_patient(client):
    r = client.get("/lineage/patient/P001")
    assert r.status_code == 200
    payload = r.json()
    assert "patient" in payload
    assert payload["patient"]["patient_id"] == "P001"
    assert isinstance(payload.get("samples", []), list)
    assert isinstance(payload.get("bins", []), list)
    assert isinstance(payload.get("isolates", []), list)
