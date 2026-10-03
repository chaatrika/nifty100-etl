def test_min_roe_filters_correctly(client):
    r = client.get("/api/v1/screener", params={"min_roe": 15})
    assert r.status_code == 200
    for row in r.json()["results"]:
        assert row["return_on_equity_pct"] is None or row["return_on_equity_pct"] >= 15


def test_invalid_parameter_returns_400(client):
    r = client.get("/api/v1/screener", params={"min_roe": "not-a-number"})
    assert r.status_code == 400
