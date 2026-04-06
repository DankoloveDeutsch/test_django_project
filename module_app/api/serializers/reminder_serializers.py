# module_app/api/serializers/reminder_serializers.py
"""
Сериализаторы для напоминаний (API)
"""

from rest_framework import serializers
from ...models import Reminder


class ReminderSerializer(serializers.ModelSerializer):
    """Сериализатор для напоминаний"""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    reminder_type_display = serializers.CharField(source='get_reminder_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    should_notify = serializers.BooleanField(read_only=True)
    days_until_due = serializers.SerializerMethodField()

    class Meta:
        model = Reminder
        fields = [
            'id', 'employee', 'employee_name', 'reminder_type', 'reminder_type_display',
            'title', 'description', 'due_date', 'days_until_due', 'reminder_days_before',
            'priority', 'priority_display', 'is_sent', 'sent_at', 'is_completed',
            'completed_at', 'should_notify', 'related_document', 'related_generated_doc'
        ]
        read_only_fields = ['sent_at', 'completed_at']

    def get_days_until_due(self, obj):
        if obj.due_date:
            from django.utils import timezone
            delta = obj.due_date - timezone.now().date()
            return delta.days
        return None