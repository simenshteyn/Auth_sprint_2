import pytest


@pytest.mark.asyncio
async def test_auth_is_online(make_auth_get_request):
    path = ''
    response = await make_auth_get_request(path)
    assert response.status == 200
    assert response.body['result'] == 'Hello, World!'