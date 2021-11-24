import json
import pytest
from aioredis import Redis
from functional.conftest import make_get_request, redis_client

# Testing endpoint /api/v1/person/

test_data = [
    # Non-existing ID
    ('00000000-0000-0000-0000-000000000000', 404, "Request with non-existing id has to result in status 404"),
    # Empty id
    ('', 404, "Request with empty/missing id has to result in status 404"),
]


@pytest.mark.parametrize("person_id,expected,message", test_data)
@pytest.mark.asyncio
async def test_person_invalid(make_get_request, person_id, expected, message):
    url = f'/person/{person_id}'
    response = await make_get_request(url)
    assert response.status == expected, message


cache_test_data = [
    ('3cfd976a-558c-4389-8f78-6becd3709c69', 200,
     {'id': '3cfd976a-558c-4389-8f78-6becd3709c69', 'full_name': 'Édith Piaf'})
]


# In the following test the assertions depend on each other, and therefore executed as a single test
@pytest.mark.parametrize("existing_id,expected_status,expected_record", cache_test_data)
@pytest.mark.asyncio
async def test_person_existing(make_get_request, redis_client: Redis, existing_id, expected_status, expected_record):
    # existing person_id (no cache)
    url = f'/person/{existing_id}'
    await redis_client.flushall()  # make sure there is no cache
    response = await make_get_request(url)
    assert response.status == expected_status
    assert response.body == expected_record, f"Searching {existing_id} w/o cache brings unexpected result"

    # check that the cache was created
    cached = await redis_client.get(existing_id)
    cached = json.loads(cached)
    assert cached['id'] == expected_record['id']
    assert cached['full_name'] == expected_record['full_name']

    # existing person_id (with cache)
    response = await make_get_request(url)
    assert response.status == expected_status
    assert response.body == expected_record, f"Searching {existing_id} with cache brings unexpected result"


# None means we aren't interested in checking the value
search_test_data = [
    # No query string
    ({'page[number]': '1', 'page[size]': '50', 'sort': '-full_name'}, 422, None),
    # No results
    ({'query': 'xxxxxxx', 'page[number]': '1', 'page[size]': '50', 'sort': '-full_name'}, 200, 0),
    # Empty query returns all results
    ({'query': '', 'page[number]': '1', 'page[size]': '10000', 'sort': '-full_name'}, 200, 4166),
    # Searching for specific person
    ({'query': 'Édith Piaf', 'page[number]': '1', 'page[size]': '10000', 'sort': '-full_name'}, 200, 1)

]


# Testing endpoint /person/search/?query=smith&page[number]=1&page[size]=50&sort=-full_name
@pytest.mark.parametrize("query,expected_status_code,expected_body_length", search_test_data)
@pytest.mark.asyncio
async def test_person_search(make_get_request, query, expected_status_code, expected_body_length):
    url = '/person/search/'
    response = await make_get_request(url, query)

    assert response.status == expected_status_code

    if expected_body_length:
        assert len(response.body) == expected_body_length


person_films_test_data = [
    ('1dfa1b08-5a44-4096-bcf0-a318d3645f16', 200, 2,
     ['8f20c184-7018-4c7c-82c9-e2228f75dff3', 'b10a3e12-58ce-4dea-a49d-b7d7c1784757'])
]


@pytest.mark.parametrize("person_id,expected_status_code,expected_body_length,expected_film_ids",
                         person_films_test_data)
@pytest.mark.asyncio
async def test_person_films(make_get_request, person_id, expected_status_code, expected_body_length, expected_film_ids):
    url = f'/person/{person_id}/film/'
    response = await make_get_request(url)
    assert response.status == expected_status_code
    assert len(response.body) == expected_body_length, "Response has to return %d records, %d returned" % \
                                                       (expected_body_length, len(response.body))
    assert [film['id'] for film in response.body] == expected_film_ids
