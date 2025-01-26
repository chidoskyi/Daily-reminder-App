from users.models import User
from django.db import models
import uuid

class Task(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    time = models.TimeField()
    daily_reminder = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
   
class Reminder(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    datetime = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    
    
class QuoteSchedule(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    scheduled_time = models.TimeField()  # Daily time to send quotes
    is_active = models.BooleanField(default=True)