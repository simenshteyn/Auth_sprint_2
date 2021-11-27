import json
from functools import lru_cache
from typing import Optional

from aioredis import Redis
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch
from elasticsearch import NotFoundError as ESNotFoundError
from elasticsearch_dsl import Search
from fastapi import Depends
from models.genre import Genre

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class GenreService:
    def __init__(self, elastic: AsyncElasticsearch, redis: Redis):
        self.es_client = elastic
        self.redis_client = redis

    async def get_genre_by_id(self, genre_id: str) -> Optional[dict]:
        genre = await self._genre_from_cache(genre_id=genre_id)
        if not genre:
            genre = await self._genre_from_elastic(genre_id=genre_id)
            if not genre:
                return None
            await self._put_genre_to_cache(genre)
        return genre

    async def search(self, query, size, start, sort=Optional[str]):
        s: Search = Search(using=self.es_client, index='genres')
        if query:
            s = s.query("match", title=query)
        if sort:
            s = s.sort(sort)
        s = s[start:start + size]
        result = await self.es_client.search(index='genres', body=s.to_dict())
        items = [Genre(**hit['_source']) for hit in result['hits']['hits']]
        return items

    async def _genre_from_cache(self, genre_id: str) -> Optional[dict]:
        data = await self.redis_client.get(genre_id)
        if not data:
            return None
        genre = Genre.parse_raw(data)
        return genre

    async def _put_genre_to_cache(self, genre: dict):
        await self.redis_client.set(genre.get("id"), json.dumps(genre), expire=FILM_CACHE_EXPIRE_IN_SECONDS)

    async def _genre_from_elastic(self, genre_id: str) -> dict:
        try:
            genre = await self.es_client.get(index="genres", id=genre_id)
            return genre.get("_source")
        except ESNotFoundError:
            return None


@lru_cache()
def get_genre_service(elastic: AsyncElasticsearch = Depends(get_elastic),
                      redis: Redis = Depends(get_redis)) -> GenreService:
    return GenreService(elastic=elastic, redis=redis)
