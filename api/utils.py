import json
import redis
import logging
from datetime import datetime, timezone
from rest_framework_simplejwt.tokens import RefreshToken
from config.settings import REDIS_URL, REDIS_PORT, REDIS_PASSWORD

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.Redis(
    host=REDIS_URL,
    port=REDIS_PORT,
    db=0,
    password=REDIS_PASSWORD,
    socket_timeout=5,
    socket_connect_timeout=5
)

def publish_to_redis(reminder, action="created"):
    """
    Publish reminder data to Redis Stream with proper datetime handling and user authentication.
    
    Args:
        reminder: The reminder object to publish.
        action: The action associated with the reminder (e.g., "created" or "scheduled").
    """
    logger.debug("Publish to Redis method initiated")
    
    try:
        # Ensure reminder_datetime is in UTC
        if reminder.reminder_datetime.tzinfo is None:
            reminder_datetime = reminder.reminder_datetime.replace(tzinfo=timezone.utc)
        else:
            reminder_datetime = reminder.reminder_datetime.astimezone(timezone.utc)

        # Generate access token for the user
        refresh = RefreshToken.for_user(reminder.user)
        access_token = str(refresh.access_token)
        
        message = {
            'reminder_id': str(reminder.uid),
            'title': reminder.title,
            'user_id': str(reminder.user.uid),
            'reminder_datetime': reminder_datetime.isoformat(),
            'email': reminder.user.email,
            'sent': str(reminder.sent).lower(),  # Ensure boolean is converted to string
            'action': 'scheduled' if not reminder.sent else 'created',  # Set action based on sent status
            'schedule_time': str(int(reminder_datetime.timestamp())),  # Add Unix timestamp for easier scheduling
            'access_token': access_token  # Add the access token
            
        }

        logger.debug(f"Prepared message: {message}")
        
        # Publish to Redis Stream
        stream_id = redis_client.xadd('reminders', message)
        logger.info(f"Published to Redis Stream with ID: {stream_id}")
        
        return True
        
    except Exception as e:
        logger.critical(f"Critical error in Redis publishing: {e}", exc_info=True)
        return False