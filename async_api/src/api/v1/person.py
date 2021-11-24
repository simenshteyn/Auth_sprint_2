from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Query
from pydantic import BaseModel
from typing import Optional, List

from api.v1.film import Film
from services.film import FilmService, get_film_service
from services.person import PersonService, get_person_service

from uuid import UUID

NO_FILMS_FOUND = 'No films found'
PERSON_NOT_FOUND = 'Person not found'

router = APIRouter()


class Person(BaseModel):
    id: str
    full_name: str


@router.get('/{person_id:uuid}/film/', response_model=List[Film], deprecated=True)
async def person_films(
        person_id: UUID = Query(..., description="ID of the person (UUID)"),
        film_service: FilmService = Depends(get_film_service)
) -> List[Film]:
    """ Returns films the given person had participated in (as an actor, writer or director).
        This endpoint is exceptional: it belongs to /person/ base route but queries 'movies' ES index.
        (placing it in api/v1/person.py to make it work under /person/ as requested by the assignment)"""
    films = await film_service.get_by_person_id(str(person_id))

    if not films:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=NO_FILMS_FOUND
        )

    return films


@router.get('/{person_id:uuid}', response_model=Person)
async def person_details(
        person_id: UUID = Query(..., description="ID of the person (UUID)"),
        person_service: PersonService = Depends(get_person_service)
) -> Person:
    person = await person_service.get_by_id(str(person_id))

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=PERSON_NOT_FOUND
        )

    return person


@router.get('/search/', response_model=List[Person])
async def person_search(query: str = Query(...,
                                           description="Search term to use when searching persons"),
                        page_number: Optional[int] = Query(1,
                                                           alias="page[number]",
                                                           description="Page number"),
                        page_size: Optional[int] = Query(50,
                                                         alias="page[size]",
                                                         description="Number of results per page to return"),
                        sort: Optional[str] = Query(None,
                                                    description="""field name to use for ordering. 
                                                                    Use '-' in front for descending order"""),
                        person_service: PersonService = Depends(get_person_service),
                        ):
    start = (page_number - 1) * page_size
    persons = await person_service.search(query, size=page_size, start=start, sort=sort)

    return persons
