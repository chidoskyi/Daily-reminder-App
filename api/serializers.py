from rest_framework import serializers
from .models import Task, Reminder, Category, QuoteSchedule


class CategorySerializer(serializers.ModelSerializer):
    task_count = serializers.IntegerField(read_only=True, default=0)
    active_tasks = serializers.IntegerField(read_only=True, default=0)
    completed_tasks = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'task_count', 'active_tasks', 
            'completed_tasks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TaskSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'uid', 'title', 'description', 'category', 'category_name',
            'priority', 'due_date', 'time',
            'is_recurring', 'recurrence_pattern', 'completed',
            'daily_reminder', 'snooze_times'
        ]
        read_only_fields = ['uid']


class TaskDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    reminders = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'uid', 'title', 'description', 'category',
            'priority', 'due_date', 'time',
            'is_recurring', 'recurrence_pattern', 'completed',
            'daily_reminder', 'snooze_times', 'reminders',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['uid', 'created_at', 'updated_at']
    
    def get_reminders(self, obj):
        reminders = obj.reminders.all().order_by('reminder_datetime')
        return ReminderSerializer(reminders, many=True).data


class ReminderSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_priority = serializers.CharField(source='task.priority', read_only=True)
    category_name = serializers.CharField(source='task.category.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Reminder
        fields = [
            'uid', 'title', 'task', 'task_title', 'task_priority', 'category_name',
            'reminder_datetime', 'sent', 'is_active', 'is_snooze', 'snooze_minutes',
            'is_completed'
        ]
        read_only_fields = ['uid', 'sent', 'is_completed']
    
    def to_representation(self, instance):
        """Ensure datetime is in the correct format for Redis"""
        data = super().to_representation(instance)
        # Format datetime in ISO format for Redis
        data['reminder_datetime'] = instance.reminder_datetime.isoformat()
        # Add additional fields needed by Go service
        data['user_id'] = str(instance.user.uid)
        data['task_id'] = str(instance.task.uid)
        return data


class ReminderDetailSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    
    class Meta:
        model = Reminder
        fields = [
            'uid', 'title', 'task', 'reminder_datetime',
            'sent', 'is_active', 'is_snooze', 'snooze_minutes',
            'is_completed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uid', 'sent', 'is_completed', 'created_at', 'updated_at']


class QuoteScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteSchedule
        fields = ['uid', 'scheduled_time', 'is_active']
        read_only_fields = ['uid']
