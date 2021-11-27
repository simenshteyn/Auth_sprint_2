from functools import lru_cache
from typing import List, Optional, Tuple

from aioredis import Redis
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch
from elasticsearch import NotFoundError as ESNotFoundError
from elasticsearch import RequestError as ESRequestError
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Q
from fastapi import Depends, HTTPException
from fastapi.logger import logger as log
from models.film import Film

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5
FILM_ES_INDEX = 'movies'


class FilmService:
    """Class that retrieves film data."""

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def _get_film_from_cache(self, film_id: str) -> Optional[Film]:
        """Get film by ID from Redis."""
        data = await self.redis.get(film_id)
        if data:
            film = Film.parse_raw(data)
            return film

        return None

    async def _put_film_to_cache(self, film: Film):
        """Put film using ID as a key to Redis."""
        await self.redis.set(
            film.id, film.json(), expire=FILM_CACHE_EXPIRE_IN_SECONDS
        )

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        """Get film by ID from Elasticsearch."""
        try:
            doc = await self.elastic.get(FILM_ES_INDEX, film_id)
            return Film(**doc['_source'])
        except ESNotFoundError:
            return None

    async def _search_films_in_elastic(
            self,
            query_body: Optional[dict] = None,
            sort: Optional[List[str]] = None,
            offset: Optional[int] = 0,
            limit: Optional[int] = 10,
    ) -> Tuple[List[Film], int]:
        """
        Search film in Elasticsearch.
        It supports arbitrary query body, sorting and pagination.
        """
        params = {
            'from': offset,
            'size': limit,
        }

        if sort is not None:
            sort_params = []
            for item in sort:
                if item[0] == '-':
                    sort_params.append(f'{item[1:]}:desc')
                else:
                    sort_params.append(f'{item}:asc')
            params['sort'] = ','.join(sort_params)

        try:
            response = await self.elastic.search(
                body=query_body, index=FILM_ES_INDEX, params=params
            )
        except ESNotFoundError:
            return [], 0
        except ESRequestError as err:
            log.warn('Elasticsearch request failed!', err)
            raise HTTPException(
                status_code=err.status_code, detail='Search request failed'
            )

        hits = response['hits']['hits']
        docs = (Film(**hit['_source']) for hit in hits)
        docs_found = int(response['hits']['total']['value'])

        return docs, docs_found

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        """Get film by ID."""
        film = await self._get_film_from_cache(film_id)
        if film:
            return film

        film = await self._get_film_from_elastic(film_id)
        if film:
            await self._put_film_to_cache(film)
            return film

        return None

    async def get_list(
            self,
            query_str: Optional[str] = None,
            filter_by_genre: Optional[List[str]] = None,
            filter_by_max_rating: Optional[float] = None,
            sort: Optional[List[str]] = None,
            offset: Optional[int] = 0,
            limit: Optional[int] = 10,
    ) -> Tuple[List[Film], int]:
        """
        Get list of fims.
        It supports filtering, search by text, sorting and pagination.
        """
        query_body = {'query': {'bool': {}}}
        is_empty_body = True

        if query_str is not None and len(query_str) > 0:
            query_body['query']['bool']['should'] = [
                {'match': {'title': {'query': query_str, 'boost': 2}}},
                {'match': {'description': {'query': query_str}}},
            ]
            is_empty_body = False

        filters = []
        if filter_by_genre is not None and len(filter_by_genre) > 0:
            filters.append({'terms': {'genre': filter_by_genre}})
            is_empty_body = False

        if filter_by_max_rating is not None:
            filters.append(
                {"range": {"imdb_rating": {"lte": filter_by_max_rating}}}
            )

        if filters:
            query_body['query']['bool']['filter'] = filters
            is_empty_body = False

        if is_empty_body:
            query_body = None

        docs, docs_found = await self._search_films_in_elastic(
            query_body=query_body, sort=sort, offset=offset, limit=limit
        )

        return docs, docs_found

    async def get_by_person_id(self, person_id) -> List[Film]:
        q = Q("multi_match", query=person_id, fields=['actors.id', 'writers.id', 'directors.id'])

        s: Search = Search(using=self.elastic, index='movies').query(q)

        result = await self.elastic.search(index='movies', body=s.to_dict())
        films = [Film(**hit['_source']) for hit in result['hits']['hits']]

        return films


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
