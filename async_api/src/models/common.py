import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class ElasticModel(BaseModel):
    """Baseclass for internal data models for Elasticsearch index."""

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
