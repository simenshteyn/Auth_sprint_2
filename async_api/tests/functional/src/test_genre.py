import json

import pytest
from aioredis import Redis


# Testing endpoint /api/v1/genre/
@pytest.mark.asyncio
async def test_genre_invalid(make_get_request, redis_client: Redis):
    # Non-existing ID
    non_existing_genre_id = '00000000-0000-0000-0000-000000000000'
    url = f'/genre/{non_existing_genre_id}'
    response = await make_get_request(url)
    assert response.status == 404

    # No ID
    url = '/genre/'
    response = await make_get_request(url)
    assert response.status == 404

    # existing genre_id (no cache)
    existing_id = '5723ee25-b656-4bca-a821-1d915c2cf272'
    url = f'/genre/{existing_id}'
    await redis_client.flushall()  # make sure there is no cache
    response = await make_get_request(url)
    assert response.status == 200
    expected = {"id": "5723ee25-b656-4bca-a821-1d915c2cf272", "title": "Mystery",
                "movies": ["2d32c2a2-fde2-4764-b435-d598872d6bb7", "174ce5e8-183c-4480-b269-30a5715b97e9",
                           "51a4d0e8-df3d-488f-9788-b13b9a69320f", "71da253a-30e5-424d-8b1d-8729f6c39bbe",
                           "2ceb64e3-1628-40ca-a356-04f32679e0ab", "cbad22ee-5ac3-45f5-8177-363258c34bcb",
                           "3c5c3980-9015-43e1-adad-de3996d9abef", "88a85eb8-3c0d-4de5-80e0-5c1b376309fc",
                           "04441eeb-0a77-4566-a6e5-c50231f6c9fb", "173be65b-8e89-45ea-bbdd-b21e698d262e",
                           "db40d520-a93c-4fca-bbe4-e032dffde505", "16ebd3e2-2a32-4e63-8aca-f6652f83f0c9",
                           "16738d41-4409-49e9-9215-9eda216cf46a", "410efecd-f1c7-4260-a6ac-4f58a5204a1e"]}
    assert response.body == expected

    # check that the cache was created
    cached = await redis_client.get(existing_id)
    cached = json.loads(cached)
    assert cached['id'] == expected['id']
    assert cached['title'] == expected['title']

    # existing genre_id (with cache)
    response = await make_get_request(url)
    assert response.status == 200
    assert response.body == expected


# Testing  /genre/search/?query=smith&page[number]=1&page[size]=50&sort=-title
@pytest.mark.asyncio
async def test_genre_search_id(make_get_request):
    url = '/genre/search/'

    # No query string
    query = {'page[number]': '1', 'page[size]': '50', 'sort': '-title'}
    response = await make_get_request(url, query)
    assert response.status == 422

    # No results
    query = {'query': 'xxxxxxx', 'page[number]': '1', 'page[size]': '50'}
    response = await make_get_request(url, query)
    assert response.status == 200
    assert len(response.body) == 0

    # Empty query returns all results
    query = {'query': '', 'page[number]': '1', 'page[size]': '10000'}
    response = await make_get_request(url, query)
    assert response.status == 200
    assert len(response.body) == 236

    # Searching for specific genre
    query = {'query': 'Mystery', 'page[number]': '1', 'page[size]': '1'}
    response = await make_get_request(url, query)
    assert response.status == 200
    assert len(response.body) == 1
    assert {"id": "9c3ca691-ab36-4b69-8e19-9ec73022f40c",
            "title": "Mystery", "movies": []} in response.body
