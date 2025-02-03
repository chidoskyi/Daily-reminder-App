import json
import sys
from django.contrib import admin
import redis
from .models import Category, Task, Reminder, QuoteSchedule
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

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'updated_at')
    search_fields = ('name', 'user__username')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)


# TaskAdmin class
@admin.register(Task)
# class TaskAdmin(admin.ModelAdmin):
class TaskAdmin(ModelAdmin):
    list_display = ('title', 'user', 'due_date', 'time', 'daily_reminder')
    list_filter = ('due_date', 'daily_reminder')
    search_fields = ('title', 'description', 'user__username')
    
class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ('title', 'end_date')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


@admin.register(Reminder)
class ReminderAdmin(ModelAdmin):
    list_display = ('title', 'user', 'reminder_datetime',  'is_completed')
    list_filter = ('is_completed', 'reminder_datetime','sent', 'user')
    search_fields = ('title', 'user__username')

@admin.register(QuoteSchedule)
class QuoteScheduleAdmin(ModelAdmin):
    list_display = ('user', 'scheduled_time', 'is_active')
    list_filter = ('is_active', 'scheduled_time')
    search_fields = ('user__username',)
