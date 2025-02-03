from django.utils import timezone
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from users.models import User
from django.db import models
import uuid
from django.db.models import Q

class Category(models.Model):
    name = models.CharField(
        max_length=100,
        help_text="Name of the category"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='categories',
        help_text="User who created this category"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']
        unique_together = ['name', 'user']  # Prevent duplicate category names per user

    def __str__(self):
        return f"{self.name} (Created by: {self.user.username})"

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    RECURRENCE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_recurring = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, choices=RECURRENCE_CHOICES, blank=True, null=True)
    snooze_times = models.JSONField(
        default=list,  # Will store list of minutes like [30, 10, 5]
        blank=True,
        help_text="List of minutes before the reminder to send snooze notifications"
    )
    description = models.TextField()
    due_date = models.DateField()
    time = models.TimeField()
    daily_reminder = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    def clean(self):
        # Validate due_date is not in the past
        if self.due_date and self.due_date < timezone.now().date():
            raise ValidationError('Due date cannot be in the past.')
        
        # Validate recurrence pattern is set when is_recurring is True
        if self.is_recurring and not self.recurrence_pattern:
            raise ValidationError('Recurrence pattern must be set for recurring tasks.')
        
        # Validate snooze times are positive integers
        if self.snooze_times:
            if not isinstance(self.snooze_times, list):
                raise ValidationError('Snooze times must be a list of integers.')
            for time in self.snooze_times:
                if not isinstance(time, int) or time <= 0:
                    raise ValidationError('Snooze times must be positive integers.')

class Reminder(models.Model):
    
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="reminders")
    title = models.CharField(max_length=200)
    reminder_datetime = models.DateTimeField()
    sent = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_snooze = models.BooleanField(default=False)
    snooze_minutes = models.IntegerField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def clean(self):
        super().clean()
        if not self.reminder_datetime:
            raise ValidationError({
                'reminder_datetime': 'Reminder datetime is required.'
            })

        # Ensure the datetime is timezone-aware
        if timezone.is_naive(self.reminder_datetime):
            self.reminder_datetime = timezone.make_aware(self.reminder_datetime)
        
        # Get current time (timezone-aware)
        now = timezone.now()
        
        # For new reminders, ensure datetime is in the future
        if not self.pk and self.reminder_datetime <= now:
            raise ValidationError({
                'reminder_datetime': 'Reminder datetime must be at least 1 minute in the future.'
            })
        
        # For existing reminders being updated
        elif self.pk:
            # Allow updating other fields even if datetime has passed
            pass

    def save(self, *args, **kwargs):
        self.clean()
        
        # Handle existing reminders
        if self.pk is not None:
            now = timezone.now()
            # Mark as completed if datetime has passed
            if self.reminder_datetime <= now or self.sent:
                self.is_completed = True
        
        super().save(*args, **kwargs)
        
        
    @classmethod
    def update_completed_status(cls):
        """
        Update is_completed status for reminders where:
        1. reminder_datetime has passed OR
        2. reminder has been sent
        Returns the number of reminders updated.
        """
        current_time = timezone.now()
        updated_count = cls.objects.filter(
            # Using Q objects with OR operator (|) to combine conditions
            (Q(reminder_datetime__lte=current_time) | Q(sent=True)) & 
            Q(is_completed=False)
        ).update(is_completed=True)
        return updated_count

    class Meta:
        indexes = [
            models.Index(fields=['reminder_datetime', 'is_completed']),
            models.Index(fields=['sent', 'is_completed']),  # Added new index for sent field
        ]
        ordering = ['reminder_datetime']

    
    
class QuoteSchedule(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    scheduled_time = models.TimeField()  # Daily time to send quotes
    is_active = models.BooleanField(default=True)
    

# class TaskTemplate(models.Model):
#     name = models.CharField(max_length=200)
#     description = models.TextField(blank=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

# class TimeLog(models.Model):
#     task = models.ForeignKey(Task, on_delete=models.CASCADE)
#     start_time = models.DateTimeField()
#     end_time = models.DateTimeField(null=True, blank=True)
#     duration = models.DurationField(null=True, blank=True)

# class UserProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     points = models.IntegerField(default=0)
#     streak = models.IntegerField(default=0)
#     theme_preference = models.CharField(max_length=10, default='light')
#     notification_preference = models.JSONField(default=dict)

# class SharedTask(models.Model):
#     task = models.ForeignKey(Task, on_delete=models.CASCADE)
#     shared_with = models.ForeignKey(User, on_delete=models.CASCADE)
#     can_edit = models.BooleanField(default=False)

# class Comment(models.Model):
#     task = models.ForeignKey(Task, on_delete=models.CASCADE)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     content = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)