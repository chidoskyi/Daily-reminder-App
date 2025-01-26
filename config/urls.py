from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from api.views import TaskViewSet, ReminderViewSet, QuoteScheduleViewSet

# Router for user-related endpoints
users_router = DefaultRouter()
users_router.register(r'users', UserViewSet, basename='users')

# Router for task-related endpoints
v1_router = DefaultRouter()
v1_router.register(r'tasks', TaskViewSet, basename='task')
v1_router.register(r'reminders', ReminderViewSet, basename='reminder')
v1_router.register(r'quote-schedules', QuoteScheduleViewSet, basename='quote-schedule')

# Define the urlpatterns
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(users_router.urls)),  # Users endpoints under /api/
    path('api/', include(v1_router.urls)),  # Tasks, reminders, and quote-schedules under /api/v1/
]
