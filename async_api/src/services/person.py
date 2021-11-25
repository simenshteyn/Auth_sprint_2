from functools import lru_cache
from typing import Optional

from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from elasticsearch import NotFoundError as ESNotFoundError
from elasticsearch_dsl import Search

from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.person import Person

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def _person_from_cache(self, person_id: str) -> Optional[Person]:
        data = await self.redis.get(person_id)
        if not data:
            return None

        person = Person.parse_raw(data)
        return person

    async def _get_person_from_elastic(self, person_id: str) -> Optional[Person]:
        try:
            doc = await self.elastic.get('persons', person_id)
            return Person(**doc['_source'])
        except ESNotFoundError:
            return None

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        person = await self._person_from_cache(person_id)
        if person:
            return person

        person = await self._get_person_from_elastic(person_id)
        if person:
            await self._put_person_to_cache(person)
            return person

        return None

    async def _put_person_to_cache(self, person: Person):
        await self.redis.set(
            person.id, person.json(), expire=PERSON_CACHE_EXPIRE_IN_SECONDS
        )

    async def search(self, query, size, start, sort=Optional[str]):
        s: Search = Search(using=self.elastic, index='persons')
        if query:
            s = s.query("match", full_name_text=query)

        if sort:
            s = s.sort(sort)

        s = s[start:start + size]

        result = await self.elastic.search(index='persons', body=s.to_dict())
        items = [Person(**hit['_source']) for hit in result['hits']['hits']]

        return items


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
