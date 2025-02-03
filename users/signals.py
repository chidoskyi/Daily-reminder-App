# Signal handlers
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from api.models import Task
from users.models import Profile, CompletionStats


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """Create Profile when a new User is created"""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=Profile)
def create_profile_stats(sender, instance, created, **kwargs):
    """Create CompletionStats when a Profile is created"""
    if created:
        CompletionStats.objects.create(profile=instance)

@receiver(post_save, sender=Task)
@receiver(post_delete, sender=Task)
def update_task_stats(sender, instance, **kwargs):
    """Update completion stats when tasks are modified"""
    profile = instance.user.profile
    stats = profile.ensure_completion_stats()
    stats.update_stats()

# Connect the signals
def ready():
    """Connect signals when the app is ready"""
    post_save.connect(create_user_profile, sender=settings.AUTH_USER_MODEL)
    post_save.connect(create_profile_stats, sender=Profile)
    post_save.connect(update_task_stats, sender=Task)
    post_delete.connect(update_task_stats, sender=Task)