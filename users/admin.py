from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # Define the fields to display in the admin interface
    list_display = ('email', 'username', 'uid', 'is_staff', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('email', 'username', 'uid')
    ordering = ('email',)

    # Define the fields to use when editing a user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username',)}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),  # Remove non-editable fields
    )
    
    # Define the fields to use when creating a user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

# Register the custom user model with the admin interface
admin.site.register(User, CustomUserAdmin)
