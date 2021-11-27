from models.common import ElasticModel


class Person(ElasticModel):
    id: str
    full_name: str
