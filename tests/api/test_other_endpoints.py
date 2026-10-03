def test_ratios_endpoint_returns_multiple_years(client):
    r = client.get("/api/v1/companies/TCS/ratios")
    assert r.status_code == 200
    assert len(r.json()["ratios"]) >= 10


def test_ratios_single_year_filter(client):
    r = client.get("/api/v1/companies/TCS/ratios", params={"year": "2024-03"})
    assert r.status_code == 200
    assert len(r.json()["ratios"]) == 1


def test_tearsheet_returns_pdf(client):
    r = client.get("/api/v1/companies/TCS/tearsheet")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"


def test_market_cap_history(client):
    r = client.get("/api/v1/market-cap/TCS")
    assert r.status_code == 200


def test_portfolio_stats(client):
    r = client.get("/api/v1/portfolio/stats")
    assert r.status_code == 200


def test_peer_compare_radar_data(client):
    r = client.get("/api/v1/companies/TCS/peers/compare")
    assert r.status_code == 200
