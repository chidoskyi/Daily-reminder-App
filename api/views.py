from rest_framework import viewsets, permissions
from .utils import publish_to_redis
from .models import Task, Reminder, QuoteSchedule
from .serializers import TaskSerializer, ReminderSerializer, QuoteScheduleSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only tasks for the logged-in user
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Set the logged-in user as the task owner
        task = serializer.save(user=self.request.user)
        
        # Publish the task to Redis
        publish_to_redis(task)  # Call the standalone function


class ReminderViewSet(viewsets.ModelViewSet):
    queryset = Reminder.objects.all()
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only reminders for the logged-in user
        return Reminder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Set the logged-in user as the reminder owner
        serializer.save(user=self.request.user)


class QuoteScheduleViewSet(viewsets.ModelViewSet):
    queryset = QuoteSchedule.objects.all()
    serializer_class = QuoteScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only the quote schedule for the logged-in user
        return QuoteSchedule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Ensure the quote schedule is associated with the logged-in user
        serializer.save(user=self.request.user)
