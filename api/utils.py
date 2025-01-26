import json
import redis
import logging
from config.settings import REDIS_URL, REDIS_PORT, REDIS_PASSWORD

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.Redis(
    host=REDIS_URL,
    port=REDIS_PORT,
    db=0,
    password=REDIS_PASSWORD,  # Add password if required
    socket_timeout=5,
    socket_connect_timeout=5
)

# Initialize Redis client
# redis_client = redis.Redis(host='localhost', port=6379, db=0)

def publish_to_redis(task):
    """
    Publish task data to Redis.
    """
    print(">>>>>> PUBLISH TO REDIS METHOD CALLED <<<<<<", flush=True)
    logger.debug("Publish to Redis method initiated")
    
    try:
        # Print task details for debugging
        print(f"Task Details:", flush=True)
        print(f"UID: {task.uid}", flush=True)
        print(f"Title: {task.title}", flush=True)
        print(f"User ID: {task.user.uid}", flush=True)

        message = {
            'action': 'task_scheduled',
            'task_id': str(task.uid),  
            'task_name': task.title,
            'user_id': str(task.user.uid),
            'start_date': task.start_date.isoformat(),
            'end_date': task.end_date.isoformat(),
            'time': task.time.isoformat(),
            'daily_reminder': task.daily_reminder,
        }
        
        print(f"Message to publish: {message}", flush=True)
        logger.debug(f"Prepared message: {message}")
        
        # Serialize message
        serialized_message = json.dumps(message, separators=(',', ':'))
        print(f"Serialized message: {serialized_message}", flush=True)
        
        # Publish to Redis
        try:
            receivers = redis_client.publish('tasks', serialized_message)
            print(f"Message published. Receivers: {receivers}", flush=True)
            logger.info(f"Published to Redis. Receivers: {receivers}")
        except Exception as publish_error:
            print(f"Redis publish error: {publish_error}", flush=True)
            logger.error(f"Redis publish error: {publish_error}", exc_info=True)
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}", flush=True)
        logger.critical(f"Critical error in Redis publishing: {e}", exc_info=True)