from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CompletionRate, User, Profile, CompletionStats, BioDetails
from unfold.admin import ModelAdmin

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'is_active', 'is_staff', 'created_at')
    list_filter = ('is_active', 'is_staff', 'created_at')
    search_fields = ('email', 'username')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ('user', 'display_name', 'location', 'theme_preference', 'created_at')
    list_filter = ('theme_preference', 'created_at')
    search_fields = ('user__email', 'user__username', 'display_name', 'location')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'display_name', 'avatar')
        }),
        ('Personal Details', {
            'fields': ('bio', 'location', 'website', 'timezone')
        }),
        ('Preferences', {
            'fields': ('theme_preference', 'notification_preferences')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CompletionStats)
class CompletionStatsAdmin(ModelAdmin):
    list_display = ('profile', 'total', 'completed', 'active', 'completion_rate', 'updated_at')
    readonly_fields = ('total', 'completed', 'active', 'completion_rate', 'updated_at')
    search_fields = ('profile__user__email', 'profile__user__username')
    ordering = ('-total',)
    
    def completion_rate(self, obj):
        return f"{obj.completion_rate}%"
    completion_rate.short_description = "Completion Rate"
    
    def has_add_permission(self, request):
        return False  # Stats are created automatically

@admin.register(BioDetails)
class BioDetailsAdmin(ModelAdmin):
    list_display = ('profile', 'location', 'timezone')
    search_fields = ('profile__user__email', 'profile__user__username', 'location')
    list_filter = ('timezone',)
    
@admin.register(CompletionRate)
class CompletionRateAdmin(ModelAdmin):
    list_display = ('profile', 'total', 'completed', 'active')
    readonly_fields = ('total', 'completed', 'active')
    search_fields = ('profile__user__username',)
    ordering = ('-total',)

