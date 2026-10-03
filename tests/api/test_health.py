def test_health_returns_200_and_ok(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


def test_health_db_row_counts_has_all_10_tables(client):
    body = client.get("/api/v1/health").json()
    expected = {
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "analysis",
        "documents",
        "prosandcons",
        "sectors",
        "stock_prices",
        "market_cap",
    }
    assert expected.issubset(set(body["db_row_counts"].keys()))
