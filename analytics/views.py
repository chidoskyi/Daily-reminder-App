from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import UserProductivity, TaskAnalytics, CategoryPerformance, DailyUserSummary
from .serializers import UserProductivitySerializer, TaskAnalyticsSerializer, CategoryPerformanceSerializer, DailyUserSummarySerializer
from api.models import Task, Category

class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['GET'])
    def user_productivity(self, request):
        user = request.user
        last_30_days = timezone.now().date() - timedelta(days=30)
        productivity = UserProductivity.objects.filter(user=user, date__gte=last_30_days)
        serializer = UserProductivitySerializer(productivity, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def task_completion_rate(self, request):
        user = request.user
        total_tasks = Task.objects.filter(user=user).count()
        completed_tasks = Task.objects.filter(user=user, completed=True).count()
        completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        return Response({'completion_rate': completion_rate})

    @action(detail=False, methods=['GET'])
    def category_performance(self, request):
        user = request.user
        categories = Category.objects.filter(user=user)
        performance = []
        for category in categories:
            total_tasks = Task.objects.filter(category=category).count()
            completed_tasks = Task.objects.filter(category=category, completed=True).count()
            avg_completion_time = TaskAnalytics.objects.filter(task__category=category).aggregate(Avg('time_to_complete'))['time_to_complete__avg']
            performance.append({
                'category': category.name,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'average_completion_time': avg_completion_time
            })
        return Response(performance)

    @action(detail=False, methods=['GET'])
    def daily_summary(self, request):
        user = request.user
        today = timezone.now().date()
        summary, created = DailyUserSummary.objects.get_or_create(user=user, date=today)
        serializer = DailyUserSummarySerializer(summary)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def productivity_trend(self, request):
        user = request.user
        last_30_days = timezone.now().date() - timedelta(days=30)
        trend = UserProductivity.objects.filter(user=user, date__gte=last_30_days).values('date').annotate(
            tasks_completed=Sum('tasks_completed'),
            total_time_spent=Sum('total_time_spent')
        ).order_by('date')
        return Response(list(trend))

class TaskAnalyticsViewSet(viewsets.ModelViewSet):
    queryset = TaskAnalytics.objects.all()
    serializer_class = TaskAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TaskAnalytics.objects.filter(task__user=self.request.user)

class CategoryPerformanceViewSet(viewsets.ModelViewSet):
    queryset = CategoryPerformance.objects.all()
    serializer_class = CategoryPerformanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CategoryPerformance.objects.filter(category__user=self.request.user)

