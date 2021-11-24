import asyncio
import pytest
import random
import string
from collections import Counter
from http import HTTPStatus
from psycopg2._psycopg import connection, cursor
from redis import Redis

from tests.functional.src.test_user import create_user


@pytest.mark.asyncio
async def test_rate_limit(
        pg_conn: connection,
        pg_curs: cursor,
        redis_conn: Redis,
        make_get_request):
    username = password = "".join(
        random.choices(string.ascii_lowercase, k=10))
    email = username + "@yandex.com"

    valid_data = {
        "username": username, "password": password, "email": email
    }

    response, user = create_user(valid_data, pg_curs, redis_conn)
    response_json = response.json()
    access_token = response_json['access_token']
    headers = {
        'Authorization': 'Bearer ' + access_token
    }

    # Testing server has to be configured with USER_MAX_REQUEST_RATE=10
    max_rate = 10
    overflow = 5

    # Sending simultaneous requests
    # causing an overflow by 5 requests
    tasks = []
    for _ in range(max_rate + overflow):
        task = asyncio.create_task(
            make_get_request('user/slow', headers=headers))
        tasks.append(task)

    # collecting responses and counting status codes
    stats = Counter()
    for task in tasks:
        response = await task
        stats[response.status] += 1

    if stats[HTTPStatus.OK] < max_rate:
        pytest.fail(f"Failed make {max_rate} parallel requests")

    if stats[HTTPStatus.OK] > max_rate:
        pytest.fail(
            f'Exceeded the rate of {max_rate} parallel'
            f'requests with {stats[HTTPStatus.OK]} requests')

    assert stats[HTTPStatus.TOO_MANY_REQUESTS] == overflow, \
        "Wrong number of 429 responses"
