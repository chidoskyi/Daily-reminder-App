from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from .models import Task, Reminder, QuoteSchedule
from rest_framework.response import Response
from rest_framework import status
from .utils import publish_to_redis
import logging
logger = logging.getLogger(__name__)
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
        serializer.save(user=self.request.user)



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
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Save the reminder and associate it with the logged-in user
            reminder = serializer.save(user=request.user)

            # Use the centralized publish_to_redis function
            if not publish_to_redis(reminder):
                logger.error(f"Failed to publish reminder {reminder.uid} to Redis")

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['post'])
    def mark_sent(self, request, pk=None):
        """
        Mark a reminder as sent with proper error handling and logging.
        """
        try:
            reminder = self.get_object()
            if reminder.sent:
                return Response(
                    {"message": "Reminder already marked as sent"},
                    status=status.HTTP_200_OK
                )
            
            reminder.sent = True
            reminder.save()
            
            # Publish the update to Redis
            publish_to_redis(reminder, action='completed')
            
            logger.info(f"Reminder {reminder.uid} marked as sent successfully")
            return Response(
                {"message": "Reminder marked as sent"},
                status=status.HTTP_200_OK
            )
            
        except Reminder.DoesNotExist:
            logger.error(f"Attempt to mark non-existent reminder as sent: {pk}")
            return Response(
                {"error": "Reminder not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error marking reminder {pk} as sent: {str(e)}")
            return Response(
                {"error": "Failed to mark reminder as sent"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """
        Mark a reminder as completed when the scheduled time is reached.
        Notify the user when the reminder is completed.
        """
        try:
            reminder = self.get_object()
            current_time = datetime.now(timezone.utc)

            if reminder.reminder_datetime > current_time:
                return Response(
                    {"message": "Scheduled time has not been reached yet"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if reminder.mark_is_completed:
                return Response(
                    {"message": "Reminder already marked as completed"},
                    status=status.HTTP_200_OK
                )

            # Mark as completed and notify user
            reminder.is_completed = True
            reminder.save()
            publish_to_redis(reminder, action="completed")

            logger.info(f"Reminder {reminder.uid} marked as completed successfully")
            # Notify user (e.g., via email or other notification systems)
            self.notify_user(reminder)

            return Response(
                {"message": "Reminder marked as completed"},
                status=status.HTTP_200_OK
            )

        except Reminder.DoesNotExist:
            logger.error(f"Attempt to mark non-existent reminder as completed: {pk}")
            return Response(
                {"error": "Reminder not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error marking reminder {pk} as completed: {str(e)}")
            return Response(
                {"error": "Failed to mark reminder as completed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
