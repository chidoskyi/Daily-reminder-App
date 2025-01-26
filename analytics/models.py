from datetime import timedelta
from django.db import models
from users.models import User
from api.models import Task, Category

class UserProductivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    tasks_completed = models.IntegerField(default=0)
    total_time_spent = models.DurationField(default=timedelta())

class TaskAnalytics(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    time_to_complete = models.DurationField(null=True, blank=True)
    number_of_edits = models.IntegerField(default=0)
    completed_on_time = models.BooleanField(default=False)

class CategoryPerformance(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    average_completion_time = models.DurationField(null=True, blank=True)

class DailyUserSummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    tasks_created = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    total_time_logged = models.DurationField(default=timedelta())

