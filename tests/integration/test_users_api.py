import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_user_profile_integration(async_client: AsyncClient):
    response = await async_client.get("/api/v1/users/me")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "name" in data
    assert "plan" in data
    assert data["name"] == "Abogado Hexagonal"
