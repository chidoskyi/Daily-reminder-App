import uuid
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
