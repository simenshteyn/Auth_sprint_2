"""
Testing accessing Async API endpoints
while authenticated against the Auth API
"""

import requests
from psycopg2._psycopg import cursor
from redis import Redis

from tests.functional.settings import config
from tests.functional.utils.db_utils import get_auth_headers


class TestAsyncAuthIntegration:
    def test_auth_user_film(self, get_subscriber_token,
                            pg_curs: cursor,
                            redis_conn: Redis):
        """Test that authenticated user having a 'subscriber' role
        will receive all movies from the film endpoint,
        and non-subscriber (or not authenticated) users: only movies
        with IMDB rating less or equal 5.
        """

        url = config.async_api_url + "/film?sort=-imdb_rating"

        # Test that with auth headers we get movies with rating above 5.
        response = requests.request(
            'GET',
            url,
            headers=get_auth_headers(get_subscriber_token)
        )
        movies = response.json()
        assert movies['films'][0]['imdb_rating'] > 5

        # Test that without auth headers we get movies with rating 5 at most.
        response = requests.request('GET', url)
        movies = response.json()
        assert movies['films'][0]['imdb_rating'] <= 5
