import asyncio
from dataclasses import dataclass
from pprint import pprint
from typing import Union

import aiohttp
import aioredis
import pytest
from elasticsearch import AsyncElasticsearch
from functional.settings import TestSettings
from multidict import CIMultiDict, CIMultiDictProxy


@dataclass
class HTTPResponse:
    body: dict
    headers: CIMultiDictProxy[str]
    status: int


# Redefine event_loop to be session-based, otherwise getting
# "RuntimeError: Event loop is closed" when there is more then one test
@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture(scope='session')
def settings() -> TestSettings:
    return TestSettings()


@pytest.fixture(scope='session')
async def es_client(settings):
    client = AsyncElasticsearch(
        {'host': settings.es_host, 'port': settings.es_port}
    )
    yield client
    await client.close()


@pytest.fixture(scope='session')
async def redis_client(settings):
    client = await aioredis.create_redis_pool(
        (settings.redis_host, settings.redis_port)
    )
    yield client
    client.close()
    await client.wait_closed()


@pytest.fixture
def make_get_request(session, settings):
    async def inner(
            path: str, params: Union[dict, CIMultiDict] = {},
            api_ver: str = '1'
    ) -> HTTPResponse:
        url = f'{settings.service_url}/api/v{api_ver}{path}'
        # The following prints will be outputed only for failed tests
        print(url)
        pprint(params)
        async with session.get(url, params=params) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner


@pytest.fixture(scope='session')
def make_post_request(session):
    async def inner(url: str,
                    json: dict = None,
                    headers: dict = None) -> HTTPResponse:
        json = json or {}
        headers = headers or {}
        # url = '{protocol}://{host}:{port}/api/v{api_version}/{method}'.format(
        #     protocol=config.service_protocol,
        #     host=config.service_host,
        #     port=config.service_port,
        #     api_version=config.service_api_version,
        #     method=method
        # )
        async with session.post(url, json=json, headers=headers) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner


@pytest.fixture
def make_auth_get_request(session, settings):
    async def inner(
            path: str, params: Union[dict, CIMultiDict] = {},
    ) -> HTTPResponse:
        url = f'http://host.docker.internal:8000/api/v1/{path}'
        # The following prints will be outputed only for failed tests
        print(url)
        pprint(params)
        async with session.get(url, params=params) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )

    return inner
