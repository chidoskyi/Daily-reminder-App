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

def publish_to_redis(reminder):
    """
    Publish reminder data to Redis Stream.
    """
    print(">>>>>> PUBLISH TO REDIS METHOD CALLED <<<<<<", flush=True)
    logger.debug("Publish to Redis method initiated")
    
    try:
        # Print reminder details for debugging
        print(f"Reminder Details:", flush=True)
        print(f"UID: {reminder.uid}", flush=True)
        print(f"Title: {reminder.title}", flush=True)
        print(f"User ID: {reminder.user.uid}", flush=True)
        print(f"Reminder Datetime: {reminder.reminder_datetime}", flush=True)

        message = {
            'reminder_id': str(reminder.uid),  
            'title': reminder.title,
            'user_id': str(reminder.user.uid),
            'reminder_datetime': reminder.reminder_datetime.isoformat(),
            'email': reminder.user.email,  # Add user's email for notifications
        }
        
        print(f"Message to publish: {message}", flush=True)
        logger.debug(f"Prepared message: {message}")
        
        # Publish to Redis Stream
        try:
            redis_client.xadd('reminders', message)
            print(f"Message published to Redis Stream.", flush=True)
            logger.info("Published to Redis Stream.")
        except Exception as publish_error:
            print(f"Redis publish error: {publish_error}", flush=True)
            logger.error(f"Redis publish error: {publish_error}", exc_info=True)
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}", flush=True)
        logger.critical(f"Critical error in Redis publishing: {e}", exc_info=True)