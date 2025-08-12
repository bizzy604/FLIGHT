import os
from dotenv import load_dotenv
import redis
from urllib.parse import urlparse
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class RedisConfig:
    """Enhanced Redis configuration supporting both URL and individual parameters"""
    
    # Redis Cloud URL - preferred method
    REDIS_URL = os.getenv('REDIS_URL', 'redis://default:9CTbyLNREutwAduVCxkCA9kgI3sj9tEG@redis-14657.c89.us-east-1-3.ec2.redns.redis-cloud.com:14657/0')
    
    # Fallback individual parameters (for legacy compatibility)
    HOST = os.getenv('REDIS_HOST', 'localhost')
    PORT = int(os.getenv('REDIS_PORT', 6379))
    DB = int(os.getenv('REDIS_DB', 0))
    PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # Connection settings
    SOCKET_TIMEOUT = 10
    SOCKET_CONNECT_TIMEOUT = 10
    RETRY_ON_TIMEOUT = True
    HEALTH_CHECK_INTERVAL = 30
    MAX_CONNECTIONS = 50

def get_redis_connection():
    """Create and return a Redis connection with enhanced error handling"""
    try:
        redis_url = RedisConfig.REDIS_URL
        
        if redis_url and redis_url != 'redis://localhost:6379/0':
            # Use Redis URL (preferred for cloud deployments)
            logger.info(f"Connecting to Redis using URL: {_mask_password(redis_url)}")
            
            connection = redis.from_url(
                redis_url,
                socket_timeout=RedisConfig.SOCKET_TIMEOUT,
                socket_connect_timeout=RedisConfig.SOCKET_CONNECT_TIMEOUT,
                retry_on_timeout=RedisConfig.RETRY_ON_TIMEOUT,
                health_check_interval=RedisConfig.HEALTH_CHECK_INTERVAL,
                max_connections=RedisConfig.MAX_CONNECTIONS,
                decode_responses=True
            )
        else:
            # Use individual connection parameters (fallback)
            logger.info(f"Connecting to Redis using individual parameters: {RedisConfig.HOST}:{RedisConfig.PORT}")
            
            connection = redis.Redis(
                host=RedisConfig.HOST,
                port=RedisConfig.PORT,
                db=RedisConfig.DB,
                password=RedisConfig.PASSWORD,
                socket_timeout=RedisConfig.SOCKET_TIMEOUT,
                socket_connect_timeout=RedisConfig.SOCKET_CONNECT_TIMEOUT,
                retry_on_timeout=RedisConfig.RETRY_ON_TIMEOUT,
                health_check_interval=RedisConfig.HEALTH_CHECK_INTERVAL,
                max_connections=RedisConfig.MAX_CONNECTIONS,
                decode_responses=True
            )
        
        # Test the connection
        connection.ping()
        logger.info("Redis connection established successfully")
        return connection
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise

def _mask_password(redis_url: str) -> str:
    """Mask the password in Redis URL for logging"""
    try:
        parsed = urlparse(redis_url)
        if parsed.password:
            masked_url = redis_url.replace(parsed.password, '*' * len(parsed.password))
            return masked_url
        return redis_url
    except:
        return "redis://***masked***"

def test_redis_connection():
    """Test Redis connection and return connection status"""
    try:
        connection = get_redis_connection()
        
        # Test basic operations
        test_key = "test:connection:check"
        test_value = "connection_test_value"
        
        # Set a test value
        connection.set(test_key, test_value, ex=10)  # Expire in 10 seconds
        
        # Get the test value
        retrieved_value = connection.get(test_key)
        
        # Clean up
        connection.delete(test_key)
        
        if retrieved_value == test_value:
            logger.info("Redis connection test successful")
            return {
                "success": True,
                "message": "Redis connection working properly",
                "url": _mask_password(RedisConfig.REDIS_URL)
            }
        else:
            logger.error("Redis connection test failed: value mismatch")
            return {
                "success": False,
                "message": "Redis connection test failed: value mismatch"
            }
            
    except Exception as e:
        logger.error(f"Redis connection test failed: {str(e)}")
        return {
            "success": False,
            "message": f"Redis connection test failed: {str(e)}"
        }