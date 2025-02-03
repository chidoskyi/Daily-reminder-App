from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from .models import User, Profile, CompletionStats

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('uid', 'email', 'username', 'is_active', 'is_staff', 'is_superuser', 'created_at')
        read_only_fields = ('uid', 'created_at')
        
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password')

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return User.objects.create(**validated_data)

class CompletionStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompletionStats
        fields = ['total', 'completed', 'active']
        read_only_fields = ['total', 'completed', 'active']

class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='pk', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.SerializerMethodField()
    completion_rate = serializers.IntegerField(source='completion_rate_percentage', read_only=True)
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id', 'email', 'username', 'display_name', 'avatar',
            'bio', 'location', 'website', 'timezone',
            'theme_preference', 'notification_preferences',
            'completion_rate', 'stats',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'username', 'created_at', 'updated_at']

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_stats(self, obj):
        """Get task statistics in a frontend-friendly format"""
        return obj.task_stats

class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating profile information"""
    class Meta:
        model = Profile
        fields = [
            'display_name', 'bio', 'location',
            'website', 'timezone', 'theme_preference',
            'notification_preferences'
        ]

    def validate_website(self, value):
        """Validate website URL format"""
        if value and not value.startswith(('http://', 'https://')):
            value = 'https://' + value
        return value

    def validate_notification_preferences(self, value):
        """Validate notification preferences structure"""
        required_keys = {'email', 'push', 'in_app'}
        if not isinstance(value, dict) or not all(key in value for key in required_keys):
            raise serializers.ValidationError(
                "Notification preferences must include 'email', 'push', and 'in_app' settings"
            )
        return value

    def validate_timezone(self, value):
        """Validate timezone"""
        import pytz
        if value not in pytz.all_timezones:
            raise serializers.ValidationError("Invalid timezone")
        return value
