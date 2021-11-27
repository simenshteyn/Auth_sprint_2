from typing import List, Optional

from api.v1.film import Film
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Query
from pydantic import BaseModel
from services.genre import GenreService, get_genre_service

GENRE_NOT_FOUND = 'Genre not found'

router = APIRouter()


class Genre(BaseModel):
    id: str
    title: str
    movies: List[Optional[str]]


@router.get('/{genre_id}', response_model=Genre)
async def genre_detail(genre_id: str = Query(..., description="ID of the genre (UUID)"),
                       genre_service: GenreService = Depends(get_genre_service)) -> List[Film]:
    genre = await genre_service.get_genre_by_id(genre_id)
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=GENRE_NOT_FOUND
        )

    return genre


@router.get('/search/', response_model=List[Genre])
async def genre_search(query: str = Query(...,
                                          description="Search term to use when searching genres"),
                       page_number: Optional[int] = Query(1,
                                                          alias="page[number]",
                                                          description="Page number"),
                       page_size: Optional[int] = Query(50,
                                                        alias="page[size]",
                                                        description="Number of results per page to return"),
                       sort: Optional[str] = Query(None,
                                                   description="""field name to use for ordering. 
                                                                    Use '-' in front for descending order"""),
                       genre_service: GenreService = Depends(get_genre_service),
                       ):
    start = (page_number - 1) * page_size
    genres = await genre_service.search(query, size=page_size, start=start, sort=sort)

    return genres
