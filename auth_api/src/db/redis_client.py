from core.settings import config
from redis import Redis

redis = Redis(host=config.redis_host, port=config.redis_port)
