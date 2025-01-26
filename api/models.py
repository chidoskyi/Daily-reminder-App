from django.core.exceptions import ValidationError
from users.models import User
from django.db import models
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

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
    recurrence_pattern = models.CharField(max_length=50, choices=RECURRENCE_CHOICES, blank=True)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    time = models.TimeField()
    daily_reminder = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError('End date cannot be before start date.')
    
   
class Reminder(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    reminder_datetime = models.DateTimeField()
    sent = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    
    
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