from typing import List, Optional, Union

from models.common import ElasticModel


class Film(ElasticModel):
    """Internal data model for Elasticsearch index."""

    id: str
    title: str
    imdb_rating: Optional[float]
    description: Optional[str]
    genre: Union[List[str], str, None]  # case-sensitive
    director: Union[List[str], str, None]
    actors_names: Union[List[str], str, None]
    writers_names: Union[List[str], str, None]
