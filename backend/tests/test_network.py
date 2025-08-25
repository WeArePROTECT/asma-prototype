def test_network_shape(client):
    r = client.get("/network")
    assert r.status_code == 200
    payload = r.json()
    assert "nodes" in payload and "edges" in payload
    assert isinstance(payload["nodes"], list)
    assert isinstance(payload["edges"], list)
