import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from api.utils import publish_to_redis
from .models import Reminder, Task
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

def log_reminder_creation(task, reminder_type, date_time):
    """Helper function to log reminder creation details"""
    logger.info(f"""
    Creating {reminder_type} Reminder:
    Task: {task.title}
    DateTime: {date_time}
    Daily Reminder: {task.daily_reminder}
    Is Recurring: {task.is_recurring}
    Pattern: {task.recurrence_pattern}
    """)

@receiver(post_save, sender=Task)
def create_reminder_from_task(sender, instance, created, **kwargs):
    """
    Signal to create a Reminder instance when a Task is created.
    Handles recurring tasks and daily reminders with improved error handling.
    """
    try:
        current_time = timezone.now()
        # Make base_reminder_datetime timezone-aware
        base_reminder_datetime = timezone.make_aware(
            datetime.combine(instance.due_date, instance.time)
        )
        
        logger.info(f"""
        Task Save Signal Triggered:
        Task: {instance.title}
        Due Date: {instance.due_date}
        Time: {instance.time}
        Daily Reminder: {instance.daily_reminder}
        Is Recurring: {instance.is_recurring}
        Pattern: {instance.recurrence_pattern}
        """)

        # Create initial reminder only if it's a new task or not yet created
        if created:
            log_reminder_creation(instance, "Initial", base_reminder_datetime)
            create_single_reminder(instance, base_reminder_datetime)

        # Handle daily reminders
        if instance.daily_reminder:
            logger.info("Processing daily reminders...")
            current_date = timezone.now().date()
            reminders_created = 0
            
            while current_date <= instance.due_date:
                # Make reminder_datetime timezone-aware
                reminder_datetime = timezone.make_aware(
                    datetime.combine(current_date, instance.time)
                )
                
                # Skip if it's the same as initial reminder or in the past
                if reminder_datetime != base_reminder_datetime and reminder_datetime > current_time:
                    log_reminder_creation(instance, "Daily", reminder_datetime)
                    create_single_reminder(instance, reminder_datetime, is_daily=True)
                    reminders_created += 1
                
                current_date += timedelta(days=1)
            
            logger.info(f"Created {reminders_created} daily reminders")

        # Handle recurring reminders
        elif instance.is_recurring and instance.recurrence_pattern:
            logger.info("Processing recurring reminders...")
            next_reminder_date = instance.due_date
            reminders_created = 0
            
            step = {
                'daily': timedelta(days=1),
                'weekly': timedelta(weeks=1),
                'monthly': timedelta(days=30)
            }.get(instance.recurrence_pattern)
            
            if step:
                for _ in range(5):  # Create next 5 occurrences
                    next_reminder_date += step
                    # Make next_reminder_datetime timezone-aware
                    next_reminder_datetime = timezone.make_aware(
                        datetime.combine(next_reminder_date, instance.time)
                    )
                    if next_reminder_datetime > current_time:
                        log_reminder_creation(instance, "Recurring", next_reminder_datetime)
                        create_single_reminder(instance, next_reminder_datetime, is_recurring=True)
                        reminders_created += 1
                
                logger.info(f"Created {reminders_created} recurring reminders")

    except Exception as e:
        logger.error(f"Error in create_reminder_from_task: {str(e)}", exc_info=True)
        raise

def create_single_reminder(task, reminder_datetime, is_recurring=False, is_daily=False):
    """Helper function to create a single reminder instance with error handling"""
    try:
        # Ensure reminder_datetime is timezone-aware
        if reminder_datetime.tzinfo is None:
            reminder_datetime = timezone.make_aware(reminder_datetime)
            
        current_time = timezone.now()
        
        # Check if reminder already exists
        existing_reminder = Reminder.objects.filter(
            task=task,
            reminder_datetime=reminder_datetime,
            is_snooze=False  # Only check for main reminder
        ).first()
        
        if existing_reminder:
            logger.info(f"Main reminder already exists for {task.title} at {reminder_datetime}")
            return existing_reminder
            
        reminder_type = "Recurring" if is_recurring else "Daily" if is_daily else ""
        title_prefix = f"{reminder_type} Reminder: " if reminder_type else "Reminder: "
        
        # Create main reminder
        reminder = Reminder.objects.create(
            user=task.user,
            task=task,
            title=f"{title_prefix}{task.title}",
            reminder_datetime=reminder_datetime,
            sent=False,
            is_completed=False,
            is_snooze=False,
            snooze_minutes=None
        )
        logger.info(f"Created main reminder: {reminder.uid} for {reminder_datetime}")
        
        # Handle snooze reminders
        if task.snooze_times and isinstance(task.snooze_times, list):
            # Sort snooze times in descending order to create furthest notifications first
            sorted_snooze_times = sorted([int(t) for t in task.snooze_times], reverse=True)
            
            for snooze_minutes in sorted_snooze_times:
                if not isinstance(snooze_minutes, (int, float)):
                    logger.warning(f"Invalid snooze time format: {snooze_minutes}. Skipping.")
                    continue
                    
                # Calculate snooze datetime
                snooze_datetime = reminder_datetime - timezone.timedelta(minutes=int(snooze_minutes))
                
                # Only create snooze reminder if it's in the future
                if snooze_datetime > current_time:
                    # Check if snooze reminder already exists
                    existing_snooze = Reminder.objects.filter(
                        task=task,
                        reminder_datetime=snooze_datetime,
                        is_snooze=True
                    ).first()
                    
                    if existing_snooze:
                        logger.info(f"Snooze reminder already exists for {snooze_minutes} minutes before task")
                        continue
                    
                    # Format snooze time for display
                    if snooze_minutes >= 60:
                        hours = snooze_minutes // 60
                        mins = snooze_minutes % 60
                        time_display = f"{hours}h{f' {mins}m' if mins else ''}"
                    else:
                        time_display = f"{snooze_minutes}m"
                    
                    snooze_reminder = Reminder.objects.create(
                        user=task.user,
                        task=task,
                        title=f"Early Reminder: {task.title} (in {time_display})",
                        reminder_datetime=snooze_datetime,
                        sent=False,
                        is_completed=False,
                        is_snooze=True,
                        snooze_minutes=snooze_minutes
                    )
                    logger.info(f"Created snooze reminder: {snooze_reminder.uid} for {time_display} before task")
        
        return reminder
        
    except Exception as e:
        logger.error(f"Error creating reminder: {str(e)}", exc_info=True)
        raise

@receiver(post_save, sender=Reminder)
def reminder_post_save(sender, instance, created, **kwargs):
    """Signal handler for Reminder model saves with enhanced error handling"""
    try:
        logger.info(f"""
        === REMINDER POST SAVE SIGNAL ===
        Reminder ID: {instance.uid}
        Title: {instance.title}
        DateTime: {instance.reminder_datetime}
        Is new: {created}
        Sent status: {instance.sent}
        Priority: {instance.task.priority}
        Is Recurring: {instance.task.is_recurring}
        Pattern: {instance.task.recurrence_pattern}
        Daily Reminder: {instance.task.daily_reminder}
        """)
        
        if not instance.sent:
            action = 'created' if created else 'scheduled'
            success = publish_to_redis(instance, action=action)
            
            if success:
                logger.info(f"Successfully published reminder {instance.uid} to Redis")
            else:
                logger.error(f"Failed to publish reminder {instance.uid} to Redis")
        else:
            logger.info(f"Reminder {instance.uid} already sent, skipping Redis publish")
            
    except Exception as e:
        logger.error(f"Error in reminder_post_save: {str(e)}", exc_info=True)
        raise
