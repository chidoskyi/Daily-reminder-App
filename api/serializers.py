from rest_framework import serializers
from .models import Task, Reminder, QuoteSchedule


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ('uid',)


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = '__all__'
        read_only_fields = ('uid','user',)


class QuoteScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteSchedule
        fields = '__all__'
        read_only_fields = ('uid',)
