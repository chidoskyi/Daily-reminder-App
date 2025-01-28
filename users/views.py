from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import User
from .serializers import UserSerializer, RegisterSerializer

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
