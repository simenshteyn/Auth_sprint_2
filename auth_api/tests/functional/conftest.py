import asyncio

import aiohttp
import aioredis
import psycopg2
import pytest
from psycopg2.extras import DictCursor
from redis import Redis

from tests.functional.settings import config
from tests.functional.src.test_user import AuthTokenResponse, create_user
from tests.functional.utils.db_utils import (assign_role, create_role,
                                             remove_role, remove_user)
from tests.functional.utils.models import HTTPResponse

dsl = {'dbname': config.pg_dbname,
       'user': config.pg_user,
       'password': config.pg_pass,
       'host': config.pg_host,
       'port': config.pg_port}

redis_details = {
    'host': config.redis_host,
    'port': config.redis_port
}


@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def pg_conn():
    pg_conn = psycopg2.connect(**dsl, cursor_factory=DictCursor)
    pg_conn.autocommit = True
    yield pg_conn
    pg_conn.close()


@pytest.fixture
def pg_curs(pg_conn):
    pg_curs = pg_conn.cursor()
    yield pg_curs
    pg_curs.close()


@pytest.fixture(scope='session')
async def session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture(scope='session')
def make_get_request(session):
    async def inner(method: str,
                    params: dict = None,
                    headers: dict = None) -> HTTPResponse:
        params = params or {}
        headers = headers or {}
        url = '{protocol}://{host}:{port}/api/v{api_version}/{method}'.format(
            protocol=config.service_protocol,
            host=config.service_host,
            port=config.service_port,
            api_version=config.service_api_version,
            method=method
        )
        async with session.get(url,
                               params=params, headers=headers) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner


@pytest.fixture
def redis_conn():
    r = Redis(redis_details['host'],
              redis_details['port']
              )
    yield r
    r.close()


@pytest.fixture(scope='session')
def make_post_request(session):
    async def inner(method: str,
                    json: dict = None,
                    headers: dict = None) -> HTTPResponse:
        json = json or {}
        headers = headers or {}
        url = '{protocol}://{host}:{port}/api/v{api_version}/{method}'.format(
            protocol=config.service_protocol,
            host=config.service_host,
            port=config.service_port,
            api_version=config.service_api_version,
            method=method
        )
        async with session.post(url, json=json, headers=headers) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner


@pytest.fixture(scope='session')
def make_patch_request(session):
    async def inner(method: str,
                    json: dict = None,
                    headers: dict = None) -> HTTPResponse:
        json = json or {}
        headers = headers or {}
        url = '{protocol}://{host}:{port}/api/v{api_version}/{method}'.format(
            protocol=config.service_protocol,
            host=config.service_host,
            port=config.service_port,
            api_version=config.service_api_version,
            method=method
        )
        async with session.patch(url, json=json, headers=headers) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner


@pytest.fixture(scope='session')
def make_delete_request(session):
    async def inner(method: str,
                    params: dict = None,
                    headers: dict = None) -> HTTPResponse:
        params = params or {}
        headers = headers or {}
        url = '{protocol}://{host}:{port}/api/v{api_version}/{method}'.format(
            protocol=config.service_protocol,
            host=config.service_host,
            port=config.service_port,
            api_version=config.service_api_version,
            method=method
        )
        async with session.delete(url,
                                  params=params, headers=headers) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner


@pytest.fixture(scope='session')
async def redis_client():
    pool = aioredis.ConnectionPool.from_url(
        f'redis://{config.redis_host}:{config.redis_port}',
        encoding='utf-8',
        decode_responses=True
    )
    redis = aioredis.Redis(connection_pool=pool)
    await redis.flushall()
    yield redis
    await pool.disconnect()


@pytest.fixture(scope='function')
async def get_superuser_token(pg_curs, redis_conn):
    # Create superuser to work with roles and get tokens
    username = password = 'testsuperuser'
    email = username + '@yandex.com'
    valid_data = {
        'username': username,
        'password': password,
        'email': email
    }

    response, user = create_user(valid_data, pg_curs, redis_conn)
    tokens = AuthTokenResponse(**response.json())
    access_token = tokens.access_token
    su_user_uuid = user['user_id']
    assert response.status_code == 200
    assert user['user_login'] == username
    assert user['user_email'] == email
    assert len(access_token) > 5

    # Assign superuser role to superuser
    su_role_uuid = create_role(pg_curs, role_name=config.service_admin_role)
    assign_role(pg_curs, owner_id=su_user_uuid, role_id=su_role_uuid)
    yield access_token

    # Remove superuser and superadmin role
    remove_user(pg_curs, user_id=su_user_uuid)
    remove_role(pg_curs, role_id=su_role_uuid)
