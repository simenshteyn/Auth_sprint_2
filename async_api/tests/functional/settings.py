from pydantic import BaseSettings, Field


class TestSettings(BaseSettings):
    es_host: str = Field('localhost', env='ELASTIC_HOST')
    es_port: int = Field(9200, env='ELASTIC_PORT')
    redis_host: str = Field('localhost', env='REDIS_HOST')
    redis_port: int = Field(6379, env='REDIS_PORT')
    api_host: str = Field('localhost', env='API_HOST')
    api_port: int = Field(8888, env='API_PORT')

    @property
    def es_url(self):
        return f'http://{self.es_host}:{self.es_port}'

    @property
    def redis_url(self):
        return f'http://{self.redis_host}:{self.redis_port}'

    @property
    def service_url(self):
        return f'http://{self.api_host}:{self.api_port}'
