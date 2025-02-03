from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from users.views import ProfileViewSet, UserViewSet
from api.views import TaskViewSet, ReminderViewSet, QuoteScheduleViewSet, CategoryViewSet
from analytics.views import AnalyticsViewSet, TaskAnalyticsViewSet, CategoryPerformanceViewSet

# Router for user-related endpoints
users_router = DefaultRouter()
users_router.register(r'users', UserViewSet, basename='users')
users_router.register(r'profile', ProfileViewSet, basename='profile')

# Router for task-related endpoints
v1_router = DefaultRouter()
v1_router.register(r'tasks', TaskViewSet, basename='task')
v1_router.register(r'reminders', ReminderViewSet, basename='reminder')
v1_router.register(r'categories', CategoryViewSet, basename='category')
v1_router.register(r'quote-schedules', QuoteScheduleViewSet, basename='quote-schedule')

v2_router = DefaultRouter()
v2_router.register(r'analytics', AnalyticsViewSet, basename='analytics')
v2_router.register(r'task-analytics', TaskAnalyticsViewSet)
v2_router.register(r'category-performance', CategoryPerformanceViewSet)

# Define the urlpatterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(users_router.urls)),  # Users endpoints under /api/
    path('api/', include(v1_router.urls)),  # Tasks, reminders, and quote-schedules under /api/v1/
    path('api/', include(v2_router.urls)),  # Tasks, reminders, and quote-schedules under /api/v1/
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
