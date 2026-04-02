from fastapi.testclient import TestClient


def test_scjn_sync_endpoint_is_not_exposed(client: TestClient):
    response = client.post("/api/v1/legal/scjn/sync", json={"page": 1, "size": 20})
    assert response.status_code == 404
