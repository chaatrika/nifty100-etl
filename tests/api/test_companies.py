def test_list_companies_returns_92(client):
    r = client.get("/api/v1/companies")
    assert r.status_code == 200
    assert r.json()["count"] == 92


def test_company_profile_returns_correct_data(client):
    r = client.get("/api/v1/companies/TCS")
    assert r.status_code == 200
    assert r.json()["id"] == "TCS"


def test_unknown_ticker_returns_404(client):
    r = client.get("/api/v1/companies/INVALID")
    assert r.status_code == 404
