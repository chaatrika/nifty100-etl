def test_peer_group_returns_percentiles(client):
    r = client.get("/api/v1/peers/IT Services")
    assert r.status_code == 200
    assert r.json()["count"] > 0


def test_unknown_peer_group_returns_404(client):
    r = client.get("/api/v1/peers/Not A Group")
    assert r.status_code == 404
