import os

from pydantic import BaseSettings


class AppSettings(BaseSettings):
    pg_host: str
    pg_port: int
    pg_dbname: str
    pg_user: str
    pg_pass: str
    pg_schema: str
    redis_host: str
    redis_port: int
    service_protocol: str
    service_host: str
    service_port: str
    service_api_version: int
    service_admin_role: str
    access_token_expiration: int
    jwt_secret_key: str
    cache_time: int
    user_max_request_rate: int


app_settings = {
    'pg_host': os.getenv('POSTGRES_HOST'),
    'pg_port': os.getenv('POSTGRES_PORT'),
    'pg_dbname': os.getenv('POSTGRES_DB'),
    'pg_user': os.getenv('POSTGRES_USER'),
    'pg_pass': os.getenv('POSTGRES_PASSWORD'),
    'pg_schema': os.getenv('POSTGRES_SCHEMA'),
    'redis_host': os.getenv('REDIS_HOST'),
    'redis_port': os.getenv('REDIS_PORT'),
    'service_protocol': os.getenv('SERVICE_PROTOCOL'),
    'service_host': os.getenv('SERVICE_HOST'),
    'service_port': os.getenv('SERVICE_PORT'),
    'service_api_version': os.getenv('SERVICE_API_VERSION'),
    'service_admin_role': os.getenv('SERVICE_ADMIN_ROLE'),
    'access_token_expiration': os.getenv('ACCESS_TOKEN_EXPIRATION'),
    'jwt_secret_key': os.getenv('JWT_SECRET_KEY'),
    'cache_time': os.getenv('CACHE_TIME'),
    'user_max_request_rate': os.getenv('USER_MAX_REQUEST_RATE')
}
config = AppSettings.parse_obj(app_settings)
