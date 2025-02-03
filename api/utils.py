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
        
        # Format snooze time display if applicable
        snooze_display = ""
        if reminder.is_snooze and reminder.snooze_minutes:
            if reminder.snooze_minutes >= 60:
                hours = reminder.snooze_minutes // 60
                mins = reminder.snooze_minutes % 60
                snooze_display = f"{hours}h{f' {mins}m' if mins else ''}"
            else:
                snooze_display = f"{reminder.snooze_minutes}m"
        
        message = {
            'reminder_id': str(reminder.uid),
            'title': reminder.title,
            'user_id': str(reminder.user.uid),
            'reminder_datetime': reminder_datetime.isoformat(),
            'email': reminder.user.email,
            'sent': str(reminder.sent).lower(),
            'action': action,
            'schedule_time': str(int(reminder_datetime.timestamp())),
            'access_token': access_token,
            'is_snooze': str(reminder.is_snooze).lower(),
            'snooze_minutes': str(reminder.snooze_minutes) if reminder.snooze_minutes is not None else '',
            'snooze_display': snooze_display,
            'snooze_times': json.dumps(reminder.task.snooze_times) if reminder.task.snooze_times else '[]',
            'task_id': str(reminder.task.uid),
            'priority': reminder.task.priority,
            'is_completed': str(reminder.is_completed).lower()
        }

        logger.debug(f"Prepared message for Redis: reminder_id={message['reminder_id']}, "
                    f"datetime={message['reminder_datetime']}, "
                    f"is_snooze={message['is_snooze']}")
        
        # Publish to Redis Stream
        stream_id = redis_client.xadd('reminders', message)
        logger.info(f"Published to Redis Stream with ID: {stream_id}")
        
        return True
        
    except Exception as e:
        logger.critical(f"Critical error in Redis publishing: {e}", exc_info=True)
        return False