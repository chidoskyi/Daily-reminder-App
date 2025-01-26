from rest_framework import serializers
from .models import UserProductivity, TaskAnalytics, CategoryPerformance, DailyUserSummary

class UserProductivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProductivity
        fields = ['user', 'date', 'tasks_completed', 'total_time_spent']

class TaskAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAnalytics
        fields = ['task', 'time_to_complete', 'number_of_edits', 'completed_on_time']

class CategoryPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryPerformance
        fields = ['category', 'total_tasks', 'completed_tasks', 'average_completion_time']

class DailyUserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyUserSummary
        fields = ['user', 'date', 'tasks_created', 'tasks_completed', 'total_time_logged']
