from typing import List, Optional

from models.common import ElasticModel


class Genre(ElasticModel):
    id: str
    title: str
    movies: List[Optional[str]]
