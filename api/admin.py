import json
import sys
from django.contrib import admin
import redis
from .models import Task, Reminder, QuoteSchedule
from unfold.admin import ModelAdmin
from .utils import publish_to_redis  # Import the standalone function
from config.settings import REDIS_URL, REDIS_PORT, REDIS_PASSWORD, PORT
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)

if not PORT:
    PORT = "8080"
    print("PORT was empty. Defaulting to 8080.", flush=True)
    logger.info("PORT was empty. Set to default: 8080.")

try:
    redis_client = redis.Redis(
        host=REDIS_URL, 
        port=REDIS_PORT, 
        db=0, 
        password=REDIS_PASSWORD  # Add the password here
    )
    redis_client.ping()
    print("Redis connection successful", flush=True)
    logger.info("Redis connection established")
except Exception as e:
    print(f"Redis connection failed: {e}", flush=True)
    logger.error(f"Redis connection error: {e}")


# TaskAdmin class
@admin.register(Task)
# class TaskAdmin(admin.ModelAdmin):
class TaskAdmin(ModelAdmin):
    list_display = ('title', 'user', 'start_date', 'end_date', 'time', 'daily_reminder')
    list_filter = ('start_date', 'end_date', 'daily_reminder')
    search_fields = ('title', 'description', 'user__username')

    def save_model(self, request, obj, form, change):
        print(">>>>>> SAVE MODEL CALLED <<<<<<", flush=True)
        logger.debug("Save model method triggered")
        
        try:
            # First save the model
            super().save_model(request, obj, form, change)
            
            # Then publish to Redis
            publish_to_redis(obj)  # Call the standalone function
        except Exception as e:
            print(f"ERROR in save_model: {e}", flush=True)
            logger.error(f"Error in save_model: {e}", exc_info=True)

@admin.register(Reminder)
class ReminderAdmin(ModelAdmin):
    list_display = ('title', 'user', 'reminder_datetime', 'is_completed')
    list_filter = ('is_completed', 'reminder_datetime')
    search_fields = ('title', 'user__username')

@admin.register(QuoteSchedule)
class QuoteScheduleAdmin(ModelAdmin):
    list_display = ('user', 'scheduled_time', 'is_active')
    list_filter = ('is_active', 'scheduled_time')
    search_fields = ('user__username',)
