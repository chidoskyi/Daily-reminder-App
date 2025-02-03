import uuid
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

# Create your models here.
class User(AbstractUser):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']
    
    # Adding custom related_name to avoid clashes with the built-in User model
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',  # Custom related name for groups
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_permissions_set',  # Custom related name for user_permissions
        blank=True
    )
    
    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    display_name = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True
    )
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        blank=True
    )
    theme_preference = models.CharField(
        max_length=20,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='dark'
    )
    notification_preferences = models.JSONField(
        default=dict,
        help_text="User's notification preferences"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Set default notification preferences if not set
        if not self.notification_preferences:
            self.notification_preferences = {
                "email": True,
                "push": True,
                "in_app": True
            }
        super().save(*args, **kwargs)
    
    def ensure_completion_stats(self):
        """Ensure CompletionStats exists for this profile"""
        stats, created = CompletionStats.objects.get_or_create(profile=self)
        return stats
    
    @property
    def completion_rate_percentage(self):
        """Calculate the task completion rate as a percentage"""
        stats = self.ensure_completion_stats()
        return stats.completion_rate
    
    @property
    def task_stats(self):
        """Get task statistics"""
        stats = self.ensure_completion_stats()
        stats.update_stats()  # Ensure stats are up to date
        return {
            'total': {
                'count': stats.total,
                'label': stats.total_label
            },
            'completed': {
                'count': stats.completed,
                'label': stats.completed_label
            },
            'active': {
                'count': stats.active,
                'label': stats.active_label
            }
        }

class CompletionStats(models.Model):
    """Track user's task completion statistics"""
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='completion_stats'
    )
    total = models.PositiveIntegerField(default=0)
    completed = models.PositiveIntegerField(default=0)
    active = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Completion Statistics"
        verbose_name_plural = "Completion Statistics"

    def __str__(self):
        return f"Stats for {self.profile.user.username}"
    
    def update_stats(self):
        """Update statistics based on user's tasks"""
        from api.models import Task
        user = self.profile.user
        
        # Calculate task statistics
        self.total = Task.objects.filter(user=user).count()
        self.completed = Task.objects.filter(user=user, completed=True).count()
        self.active = Task.objects.filter(
            user=user,
            completed=False
        ).count()
        
        self.save()

    @property
    def completion_rate(self):
        """Calculate completion rate as a percentage"""
        if self.total == 0:
            return 0
        return int((self.completed / self.total) * 100)

    @property
    def total_label(self):
        return "All tasks"
    
    @property
    def completed_label(self):
        return "Finished tasks"
    
    @property
    def active_label(self):
        return "Pending tasks"

class BioDetails(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='bio_details'
    )
    bio = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Bio details for {self.profile.user.username}"

class CompletionRate(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='completion_rate_profile', 
        
    )
    total = models.PositiveIntegerField(default=0)
    completed = models.PositiveIntegerField(default=0)
    active = models.PositiveIntegerField(default=0)

    @property
    def total_label(self):
        return "All reminders"
    
    @property
    def completed_label(self):
        return "Finished stats"
    
    @property
    def active_label(self):
        return "Funding tasks"

    def __str__(self):
        return f"Completion stats for {self.profile.user.username}"