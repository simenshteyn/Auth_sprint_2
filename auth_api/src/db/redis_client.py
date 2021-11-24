from redis import Redis

from core.settings import config

redis = Redis(host=config.redis_host, port=config.redis_port)
