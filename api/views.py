from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from .models import Task, Reminder, QuoteSchedule, Category
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
from .utils import publish_to_redis
import logging

logger = logging.getLogger(__name__)
from .serializers import (
    TaskSerializer, 
    ReminderSerializer, 
    QuoteScheduleSerializer,
    CategorySerializer,
    TaskDetailSerializer,
    ReminderDetailSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing categories.
    Allows users to create, list, update, and delete their categories.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Check for duplicate category names for this user
        name = serializer.validated_data['name']
        if Category.objects.filter(user=self.request.user, name__iexact=name).exists():
            raise serializer.ValidationError({"name": "You already have a category with this name"})
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics about categories"""
        categories = self.get_queryset().annotate(
            total_tasks=Count('task'),
            active_tasks=Count('task', filter=Q(task__completed=False)),
            completed_tasks=Count('task', filter=Q(task__completed=True))
        )
        data = [{
            'id': cat.id,
            'name': cat.name,
            'total_tasks': cat.total_tasks,
            'active_tasks': cat.active_tasks,
            'completed_tasks': cat.completed_tasks
        } for cat in categories]
        return Response(data)

class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks.
    Provides CRUD operations and additional actions for task management.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category__name']
    ordering_fields = ['due_date', 'priority', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return TaskDetailSerializer
        return TaskSerializer

    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user)
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
            
        # Filter by completion status
        completed = self.request.query_params.get('completed')
        if completed is not None:
            queryset = queryset.filter(completed=completed.lower() == 'true')
            
        return queryset

    def perform_create(self, serializer):
        task = serializer.save(user=self.request.user)
        logger.info(f"Task created: {task.title} (ID: {task.uid})")

    def perform_destroy(self, instance):
        """Handle task deletion and cleanup associated reminders"""
        # Get all active reminders for this task
        active_reminders = instance.reminders.filter(
            sent=False,
            is_active=True
        )
        
        # Notify Redis about each reminder being cancelled
        for reminder in active_reminders:
            if not publish_to_redis(reminder, action='cancelled'):
                logger.error(f"Failed to publish reminder cancellation {reminder.uid} to Redis")
        
        # Log the deletion
        logger.info(f"Task deleted: {instance.title} (ID: {instance.uid})")
        
        # Delete the task (this will cascade delete all reminders)
        instance.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_update(self, serializer):
        """Handle task updates and reschedule reminders if needed"""
        # Get the original task before update
        original_task = self.get_object()
        original_due_date = original_task.due_date
        original_time = original_task.time
        
        # Save the updated task
        task = serializer.save()
        
        # Check if due_date or time has changed
        if (task.due_date != original_due_date or 
            task.time != original_time):
            
            logger.info(f"Task {task.uid} schedule updated: {task.due_date} {task.time}")
            
            # Store existing reminders for notification
            future_reminders = list(task.reminders.filter(
                reminder_datetime__gt=timezone.now(),
                sent=False
            ))
            
            # Store original datetimes before deletion
            for reminder in future_reminders:
                reminder.original_datetime = reminder.reminder_datetime
            
            # Delete existing future reminders
            task.reminders.filter(
                reminder_datetime__gt=timezone.now(),
                sent=False
            ).delete()
            
            # Create new reminders based on updated schedule
            from .signals import create_reminder_from_task
            create_reminder_from_task(sender=Task, instance=task, created=False)
            
            # Get new reminders and notify Redis about the schedule change
            new_reminders = task.reminders.filter(reminder_datetime__gt=timezone.now())
            
            # Notify Redis about each rescheduled reminder
            from .utils import publish_to_redis
            for reminder in new_reminders:
                if not publish_to_redis(reminder, action='rescheduled'):
                    logger.error(f"Failed to publish rescheduled reminder {reminder.uid} to Redis")
            
            logger.info(f"Successfully rescheduled {new_reminders.count()} reminders for task {task.uid}")

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark a task and all its reminders as completed"""
        task = self.get_object()
        if task.completed:
            return Response({"message": "Task is already completed"})
            
        task.completed = True
        task.save()
        
        # Mark all associated reminders as completed and notify Redis
        reminders = task.reminders.all()
        reminders.update(is_completed=True, sent=True)
        
        # Notify Redis about completed reminders
        from .utils import publish_to_redis
        for reminder in reminders:
            if not publish_to_redis(reminder, action='completed'):
                logger.error(f"Failed to publish completed reminder {reminder.uid} to Redis")
        
        return Response({"status": "task and associated reminders marked as completed"})

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get tasks grouped by category"""
        categories = Category.objects.filter(user=self.request.user)
        data = {}
        for category in categories:
            tasks = self.get_queryset().filter(category=category)
            data[category.name] = TaskSerializer(tasks, many=True).data
        return Response(data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming tasks"""
        days = int(request.query_params.get('days', 7))
        due_date = timezone.now().date() + timezone.timedelta(days=days)
        
        tasks = self.get_queryset().filter(
            completed=False,
            due_date__lte=due_date,
            due_date__gte=timezone.now().date()
        ).order_by('due_date', 'time')
        
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

class ReminderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reminders.
    Provides CRUD operations and additional actions for reminder management.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'task__title']
    ordering_fields = ['reminder_datetime', 'created_at']
    ordering = ['reminder_datetime']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return ReminderDetailSerializer
        return ReminderSerializer

    def get_queryset(self):
        queryset = Reminder.objects.filter(user=self.request.user)
        
        # Filter by task
        task_id = self.request.query_params.get('task')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
            
        # Filter by completion status
        is_completed = self.request.query_params.get('is_completed')
        if is_completed is not None:
            queryset = queryset.filter(is_completed=is_completed.lower() == 'true')
            
        # Filter by sent status
        sent = self.request.query_params.get('sent')
        if sent is not None:
            queryset = queryset.filter(sent=sent.lower() == 'true')
            
        return queryset

    def perform_create(self, serializer):
        reminder = serializer.save(user=self.request.user)
        if not publish_to_redis(reminder, action='created'):
            logger.error(f"Failed to publish reminder {reminder.uid} to Redis")

    def perform_update(self, serializer):
        """Handle reminder updates and reschedule if datetime changed"""
        original_reminder = self.get_object()
        original_datetime = original_reminder.reminder_datetime
        
        # Save the updated reminder
        reminder = serializer.save()
        
        # Check if datetime has changed
        if reminder.reminder_datetime != original_datetime:
            logger.info(f"Reminder {reminder.uid} rescheduled: {reminder.reminder_datetime}")
            
            # Store original datetime for Redis notification
            reminder.original_datetime = original_datetime
            
            # Publish rescheduled action to Redis
            if not publish_to_redis(reminder, action='rescheduled'):
                logger.error(f"Failed to publish rescheduled reminder {reminder.uid} to Redis")
        else:
            # If only other fields were updated
            if not publish_to_redis(reminder, action='updated'):
                logger.error(f"Failed to publish reminder update {reminder.uid} to Redis")

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a reminder without marking it as sent"""
        reminder = self.get_object()
        
        # Check if reminder can be cancelled
        if reminder.sent:
            return Response(
                {"message": "Cannot cancel a reminder that has already been sent"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if reminder.is_completed:
            return Response(
                {"message": "Cannot cancel a completed reminder"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark reminder as inactive but keep the record
        reminder.is_active = False
        reminder.save()
        
        # Notify Redis about cancellation
        if not publish_to_redis(reminder, action='cancelled'):
            logger.error(f"Failed to publish reminder cancellation {reminder.uid} to Redis")
        
        return Response({"status": "reminder cancelled successfully"})

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule a reminder to a new datetime"""
        reminder = self.get_object()
        
        # Validate new datetime
        try:
            new_datetime = timezone.datetime.fromisoformat(request.data.get('reminder_datetime'))
            if timezone.is_naive(new_datetime):
                new_datetime = timezone.make_aware(new_datetime)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid datetime format. Please use ISO format (YYYY-MM-DDTHH:MM:SS)"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if reminder can be rescheduled
        if reminder.sent:
            return Response(
                {"message": "Cannot reschedule a reminder that has already been sent"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if reminder.is_completed:
            return Response(
                {"message": "Cannot reschedule a completed reminder"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store original datetime for Redis notification
        original_datetime = reminder.reminder_datetime
        
        # Update reminder
        reminder.reminder_datetime = new_datetime
        reminder.is_active = True  # Ensure reminder is active
        reminder.save()
        
        # Add original datetime for Redis notification
        reminder.original_datetime = original_datetime
        
        # Notify Redis about rescheduling
        if not publish_to_redis(reminder, action='rescheduled'):
            logger.error(f"Failed to publish rescheduled reminder {reminder.uid} to Redis")
        
        return Response({
            "status": "reminder rescheduled successfully",
            "new_datetime": new_datetime.isoformat()
        })

    @action(detail=True, methods=['post'])
    def mark_sent(self, request, pk=None):
        """Mark a reminder as sent"""
        reminder = self.get_object()
        if reminder.sent:
            return Response({"message": "Reminder already marked as sent"})
            
        reminder.sent = True
        reminder.is_completed = True
        reminder.save()
        
        if not publish_to_redis(reminder, action='sent'):
            logger.error(f"Failed to publish reminder sent status {reminder.uid} to Redis")
            
        return Response({"status": "reminder marked as sent"})

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's reminders"""
        today = timezone.now().date()
        reminders = self.get_queryset().filter(
            reminder_datetime__date=today,
            is_completed=False,
            is_active=True  # Only get active reminders
        ).order_by('reminder_datetime')
        
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue reminders"""
        now = timezone.now()
        reminders = self.get_queryset().filter(
            reminder_datetime__lt=now,
            is_completed=False,
            sent=False,
            is_active=True  # Only get active reminders
        ).order_by('reminder_datetime')
        
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)

class QuoteScheduleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing quote schedules."""
    serializer_class = QuoteScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return QuoteSchedule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Ensure only one schedule per user
        if QuoteSchedule.objects.filter(user=self.request.user).exists():
            raise serializer.ValidationError({"error": "You already have a quote schedule"})
        serializer.save(user=self.request.user)
