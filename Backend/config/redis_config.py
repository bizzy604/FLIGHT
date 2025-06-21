import os
from dotenv import load_dotenv
import redis

load_dotenv()

class RedisConfig:
    HOST = os.getenv('REDIS_HOST', 'localhost')
    PORT = int(os.getenv('REDIS_PORT', 6379))
    DB = int(os.getenv('REDIS_DB', 0))
    PASSWORD = os.getenv('REDIS_PASSWORD', None)
    SOCKET_TIMEOUT = 5
    SOCKET_CONNECT_TIMEOUT = 5
    RETRY_ON_TIMEOUT = True

def get_redis_connection():
    """Create and return a Redis connection"""
    return redis.Redis(
        host=RedisConfig.HOST,
        port=RedisConfig.PORT,
        db=RedisConfig.DB,
        password=RedisConfig.PASSWORD,
        socket_timeout=RedisConfig.SOCKET_TIMEOUT,
        socket_connect_timeout=RedisConfig.SOCKET_CONNECT_TIMEOUT,
        retry_on_timeout=RedisConfig.RETRY_ON_TIMEOUT,
        decode_responses=True  # Automatically decode responses to UTF-8
    )