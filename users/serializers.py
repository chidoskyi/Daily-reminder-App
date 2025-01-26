from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from .models import User

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
