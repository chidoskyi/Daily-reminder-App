from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, ReminderViewSet, CategoryViewSet, QuoteScheduleViewSet

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'reminders', ReminderViewSet, basename='reminder')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'quote-schedules', QuoteScheduleViewSet, basename='quote-schedule')

urlpatterns = [
    path('', include(router.urls)),
] 