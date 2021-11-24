from http import HTTPStatus

import pytest


@pytest.mark.asyncio
async def test_flask_main_page(make_get_request):
    response = await make_get_request('')
    assert response.status == HTTPStatus.OK
