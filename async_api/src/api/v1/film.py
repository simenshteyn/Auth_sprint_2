from typing import List, Optional

import aiohttp
from aiohttp import ClientConnectionError
from core.config import AUTH_SERVICE_USER_ROLES_URL, LIMITATION_MAX_RATING
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.logger import logger as log

from core.utils import AuthUser, get_auth_user
from models.film import Film as FilmData
from pydantic import BaseModel
from services.film import FilmService, get_film_service

FILM_NOT_FOUND = 'Film not found'
FILM_NOT_ALLOWED = 'Please subscribe to see this film'

router = APIRouter()


class Film(BaseModel):
    """Responce data model of single film."""

    id: str
    title: str
    imdb_rating: Optional[float]
    description: Optional[str]
    genres: Optional[List[str]]
    directors: Optional[List[str]]
    writers: Optional[List[str]]
    actors: Optional[List[str]]


class FilmList(BaseModel):
    """Responce data model of film list."""

    total: int
    offset: int
    limit: int
    films: List[Film]


def _create_response_model(film: FilmData):
    """Convert film from internal model to response model."""
    return Film(
        id=film.id,
        title=film.title,
        imdb_rating=film.imdb_rating,
        description=film.description,
        genres=[film.genre, ] if type(film.genre) == str else film.genre,
        directors=[film.director, ] if type(film.director) == str else film.director,
        writers=[film.actors_names, ] if type(film.actors_names) == str else film.actors_names,
        actors=[film.writers_names, ] if type(film.writers_names) == str else film.writers_names,
    )


@router.get('/search', response_model=FilmList)
async def search_films(
        query: str = Query(
            ...,
            description='Query string (any text)',
        ),
        sort: Optional[List[str]] = Query(
            None,
            description="""Sort field name.
        Minus sign "-" before name means "descending".
        This parameter can be repeated.""",
        ),
        offset: Optional[int] = Query(
            0,
            description='Offset (page number)',
        ),
        limit: Optional[int] = Query(
            10,
            description="""Data rows per page.
        Page may contain less rows than requested (for last or single page)""",
        ),
        film_service: FilmService = Depends(get_film_service),
):
    """
    Paginated list of movies that satisfy query.\n
    Example: ".../film/search/?query=abracadabra"
    """
    docs, docs_found = await film_service.get_list(
        query_str=query,
        sort=sort,
        offset=offset,
        limit=limit,
    )
    films = [_create_response_model(doc) for doc in docs]

    return {
        'total': docs_found,
        'offset': offset,
        'limit': limit,
        'films': films,
    }


@router.get(
    path='/{film_id}',
    response_model=Film,
    name='Get film details by id',
    responses={
        status.HTTP_404_NOT_FOUND: {
            'description': FILM_NOT_FOUND,
            'content': {
                'application/json': {'example': {'detail': FILM_NOT_FOUND}}
            },
        },
    },
)
async def get_film_details(
        film_id: str = Query(
            ...,
            description='Film ID (UUID)',
        ),
        film_service: FilmService = Depends(get_film_service),
        auth_user: AuthUser = Depends(get_auth_user)
) -> Film:
    """
    Detailed info about movie by its ID.\n
    Example: ".../film/bf977449-5c35-4d46-b330-a8cd15d65ef9"
    """
    film: FilmData = await film_service.get_by_id(film_id)

    if not film:
        log.info(f'Film not found! ID: "{film_id}"')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=FILM_NOT_FOUND
        )

    if not auth_user or not auth_user.is_subscriber():
        if film.imdb_rating > LIMITATION_MAX_RATING:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=FILM_NOT_ALLOWED
            )

    return _create_response_model(film)


@router.get('/', response_model=FilmList)
async def get_film_list(
        filter_by_genre: Optional[List[str]] = Query(
            None,
            description='Genre name. This parameter can be repeated.',
            alias='filter[genre]',
        ),
        sort: Optional[List[str]] = Query(
            None,
            description="""Sort field name.
        Minus sign "-" before name means "descending".
        This parameter can be repeated.""",
        ),
        offset: Optional[int] = Query(
            0,
            description='Offset (page number)',
        ),
        limit: Optional[int] = Query(
            10,
            description="""Data rows per page.
        Page may contain less rows than requested (for last or single page)""",
        ),
        film_service: FilmService = Depends(get_film_service),
        auth_user: AuthUser = Depends(get_auth_user)
):
    """
    Paginated list of movies.\n
    Examples:\n
    Full list (paginated and sorted): ".../film?sort=-imdb_rating&offset=100&limit=10"\n
    Filtered list: ".../film?filter[genre]=Comedy&filter[genre]=Drama" (boolean OR)
    """

    filter_by_max_rating = LIMITATION_MAX_RATING

    # Remove the limitation for subscribers
    if auth_user and auth_user.is_subscriber():
        filter_by_max_rating = None

    docs, docs_found = await film_service.get_list(
        filter_by_genre=filter_by_genre,
        filter_by_max_rating=filter_by_max_rating,
        sort=sort,
        offset=offset,
        limit=limit,
    )

    if docs_found > 0:
        films = [_create_response_model(doc) for doc in docs]
    else:
        films = []

    return {
        'total': docs_found,
        'offset': offset,
        'limit': limit,
        'films': films,
    }
