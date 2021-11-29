"""
Testing accessing Async API endpoints
while authenticated against the Auth API
"""
from http import HTTPStatus

import pytest
from tests.functional.utils.db_utils import get_auth_headers


@pytest.mark.asyncio
async def test_auth_user_film(get_subscriber_token, make_service_get_request):
    """Test that authenticated user having a 'subscriber' role
    will receive all movies from the film endpoint,
    and non-subscriber (or not authenticated) users: only movies
    with IMDB rating less or equal 5.
    """

    access_token = get_subscriber_token

    # Test that with auth headers we get movies with rating above 5.
    response = await make_service_get_request(
        'film?sort=-imdb_rating', headers=get_auth_headers(access_token))
    assert response.status == HTTPStatus.OK
    assert response.body['films'][0]['imdb_rating'] > 5
    high_rating_film_id = response.body['films'][0]['id']

    # Test that without auth headers we get movies with rating 5 at most.
    response = await make_service_get_request('film?sort=-imdb_rating')
    assert response.status == HTTPStatus.OK
    assert response.body['films'][0]['imdb_rating'] <= 5

    # Test that its not possible to get high rating film's details
    response = await make_service_get_request('film/' + high_rating_film_id)
    assert response.status == HTTPStatus.FORBIDDEN
