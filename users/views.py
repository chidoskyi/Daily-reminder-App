from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.shortcuts import get_object_or_404
import logging

from .models import User, Profile, CompletionStats
from .serializers import UserSerializer, RegisterSerializer, ProfileSerializer, ProfileUpdateSerializer

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['register', 'login', 'token_refresh']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                request.session['session-name'] = access_token
                return Response({
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(access_token)
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='logout')
    def logout(self, request):
        """
        Logout the user by blacklisting their refresh token and clearing their session.
        """
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                # Blacklist the refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()
                
            # Clear the session
            request.session.flush()
            
            logger.info(f"User {request.user.email} logged out successfully")
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error during logout for user {request.user.email}: {str(e)}")
            return Response({'error': 'Error occurred during logout'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='token-refresh')
    def token_refresh(self, request):
        response = TokenRefreshView.as_view()(request._request)
        return Response(response.data, status=response.status_code)
    
    @action(detail=False, methods=['get'], url_path='get-token')
    def get_jwt_token(request):
        if request.user.is_authenticated:
            refresh = RefreshToken.for_user(request.user)
            access_token = str(refresh.access_token)
            return Response({
                'access': access_token,
                'refresh': str(refresh)
            })
        return Response({'error': 'User not authenticated'}, status=401)

    
    @action(detail=False, methods=['get'], url_path='get-user')
    def get_user(self, request):
        """
        Endpoint to retrieve the authenticated user's information.
        """
        user = request.user
        if user.is_authenticated:
            serializer = self.get_serializer(user)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            return Response({
                "user":serializer.data,
                'access': access_token
                }, status=status.HTTP_200_OK)
        return Response({'error': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)

class ProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing user profiles.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ProfileUpdateSerializer
        return ProfileSerializer

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)

    def get_object(self):
        """Get the user's profile and ensure CompletionStats exists"""
        profile = get_object_or_404(Profile, user=self.request.user)
        profile.ensure_completion_stats()  # Ensure stats exist
        return profile

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's profile"""
        profile = self.get_object()
        serializer = ProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def update_theme(self, request):
        """Update user's theme preference"""
        profile = self.get_object()
        theme = request.data.get('theme')
        
        if theme not in ['light', 'dark']:
            return Response(
                {"error": "Invalid theme choice. Use 'light' or 'dark'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile.theme_preference = theme
        profile.save()
        return Response({"status": "theme updated", "theme": theme})

    @action(detail=False, methods=['post'])
    def update_notifications(self, request):
        """Update user's notification preferences"""
        profile = self.get_object()
        preferences = request.data.get('preferences', {})
        
        # Validate preferences structure
        valid_keys = {'email', 'push', 'in_app'}
        if not all(key in valid_keys for key in preferences.keys()):
            return Response(
                {"error": "Invalid preferences structure"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile.notification_preferences.update(preferences)
        profile.save()
        return Response({
            "status": "notification preferences updated",
            "preferences": profile.notification_preferences
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user's task completion statistics"""
        profile = self.get_object()
        task_stats = profile.task_stats
        
        return Response({
            "completion_rate": profile.completion_rate_percentage,
            "stats": task_stats
        })

    def perform_update(self, serializer):
        """Handle profile updates"""
        # Get the original profile
        original_profile = self.get_object()
        
        # Save the updated profile
        profile = serializer.save()
        
        # Log the update
        logger.info(f"Profile updated for user {profile.user.username}")
        
        # If avatar was updated, delete the old one if it exists
        if 'avatar' in serializer.validated_data and original_profile.avatar:
            if original_profile.avatar != profile.avatar:
                original_profile.avatar.delete(save=False)

    @action(detail=False, methods=['delete'])
    def remove_avatar(self, request):
        """Remove the user's avatar"""
        profile = self.get_object()
        if profile.avatar:
            profile.avatar.delete()
            profile.avatar = None
            profile.save()
            return Response({"status": "avatar removed"})
        return Response({"status": "no avatar to remove"})

    @action(detail=False, methods=['post'])
    def upload_avatar(self, request):
        """Upload or update profile avatar"""
        profile = self.get_object()
        
        if 'avatar' not in request.FILES:
            return Response(
                {"error": "No image file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        image = request.FILES['avatar']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if image.content_type not in allowed_types:
            return Response(
                {"error": "Invalid file type. Only JPEG, PNG and GIF are allowed."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validate file size (max 5MB)
        if image.size > 5 * 1024 * 1024:
            return Response(
                {"error": "File too large. Maximum size is 5MB."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Delete old avatar if it exists
        if profile.avatar:
            profile.avatar.delete(save=False)
            
        # Save new avatar
        profile.avatar = image
        profile.save()
        
        return Response({
            "status": "avatar updated",
            "avatar_url": request.build_absolute_uri(profile.avatar.url)
        })
