def test_404s(client):
    for url in ["/bins/NOPE", "/isolates/NOPE", "/samples/NOPE", "/patients/NOPE"]:
        r = client.get(url)
        assert r.status_code == 404
