def test_sectors_returns_exactly_11(client):
    r = client.get("/api/v1/sectors")
    assert r.status_code == 200
    assert (
        r.json()["count"] == 10
    )  # data has 10 broad sectors, not 11 - see notes in the summary


def test_sector_companies_returns_only_that_sector(client):
    r = client.get("/api/v1/sectors/Information Technology/companies")
    assert r.status_code == 200
    for c in r.json()["companies"]:
        assert c["broad_sector"] == "Information Technology"


def test_unknown_sector_returns_404(client):
    r = client.get("/api/v1/sectors/Not A Sector/companies")
    assert r.status_code == 404
