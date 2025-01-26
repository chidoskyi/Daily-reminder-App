# tasks/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Reminder
from .utils import publish_to_redis

@receiver(post_save, sender=Reminder)
def publish_reminder(sender, instance, **kwargs):
    if not instance.sent:  # Only publish if the reminder hasn't been sent yet
        publish_to_redis(instance)