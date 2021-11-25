import json

import pytest
from multidict import CIMultiDict


@pytest.mark.asyncio
async def test_get_film_by_id(make_get_request, redis_client):
    id = '00705f85-05f0-4495-b0ca-49be5a38d936'
    path = f'/film/{id}'

    # Test "pure" request with empty cache
    await redis_client.flushall()  # clean cache
    response = await make_get_request(path, api_ver='1')
    assert response.status == 200
    assert response.body['id'] == id

    # Check cache
    cached = await redis_client.get(id)
    cached = json.loads(cached)
    assert cached['id'] == id

    # Test request with non-empty cache
    response = await make_get_request(path)
    assert response.status == 200
    assert response.body['id'] == id

    # Test if request with nonexistent ID returns 404
    nonexistent_id = '00000000-0000-0000-0000-000000000000'
    path = f'/film/{nonexistent_id}/'
    response = await make_get_request(path)
    assert response.status == 404


@pytest.mark.asyncio
async def test_get_film_list(make_get_request):
    path = '/film'

    # Test getting film list (implicitly paginated)
    response = await make_get_request(path)
    assert response.status == 200
    assert 'films' in response.body
    assert response.body['limit'] == 10

    # Test getting film list sorted by IMDB rating (ascending)
    params = CIMultiDict()
    params.add('sort', 'imdb_rating')
    params.add('sort', 'id')
    response = await make_get_request(path, params)
    assert response.status == 200
    first_id = response.body['films'][0]['id']
    assert first_id == '6b5d36b7-f75b-4aed-8a61-8e4bf0013d1b'

    # Test getting film list sorted by IMDB rating (descending)
    params = CIMultiDict()
    params.add('sort', '-imdb_rating')
    params.add('sort', 'id')
    response = await make_get_request(path, params)
    assert response.status == 200
    first_id = response.body['films'][0]['id']
    assert first_id == 'd3749a53-89b3-4c6f-b9c3-280607e71c8e'

    # Test getting film list with pagination params
    params = {'offset': 925, 'limit': 20}
    response = await make_get_request(path, params)
    assert response.status == 200
    assert len(response.body['films']) == 3

    # Test getting error for incorrect pagination params
    params = {'offset': 1_000_000}
    response = await make_get_request(path, params)
    assert response.status == 400

    # Test getting film list filtered by genres
    params = CIMultiDict()
    params.add('filter[genre]', 'Comedy')
    params.add('filter[genre]', 'Drama')
    params.add('sort', 'imdb_rating')
    params.add('sort', 'id')
    response = await make_get_request(path, params)
    assert response.status == 200
    first_id = response.body['films'][0]['id']
    assert first_id == 'f3a78fa2-3b82-474d-a66a-710405e10ab1'


@pytest.mark.asyncio
async def test_film_search(make_get_request):
    path = '/film/search'

    # Find films that contain "internet" in the title or description
    params = CIMultiDict()
    params.add('query', 'internet')
    params.add('sort', '-imdb_rating')
    params.add('sort', 'id')
    response = await make_get_request(path, params)
    assert response.status == 200
    assert response.body['total'] == 4
    first_id = response.body['films'][0]['id']
    assert first_id == '1278975c-e3b8-4e89-98f1-f6905ef89f15'

    # Try to find something non-existent
    params = {'query': 'abracadabra'}
    response = await make_get_request(path, params)
    assert response.status == 200
    assert response.body['total'] == 0

    # Try to use empty query (all films should be returned)
    params = {'query': ''}
    response = await make_get_request(path, params)
    assert response.status == 200
    assert response.body['total'] == 928

    # Try to forget to pass the "query" param at all
    response = await make_get_request(path)
    assert response.status == 422  # Unprocessable Entity
