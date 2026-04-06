# module_app/api/serializers/attendance_serializers.py
"""
Сериализаторы для учета рабочего времени
"""

from rest_framework import serializers
from ...models import AttendanceLog, MonthlyReport, WorkSchedule
from .employee_serializers import EmployeeListSerializer


class WorkScheduleSerializer(serializers.ModelSerializer):
    """Сериализатор для графика работы"""
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = WorkSchedule
        fields = ['id', 'day', 'day_display', 'start_time', 'end_time']


class AttendanceLogSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для записей табеля"""
    event_display = serializers.CharField(source='get_event_display', read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = AttendanceLog
        fields = [
            'id', 'employee', 'employee_name', 'date', 'time',
            'event', 'event_display', 'hours'
        ]
        read_only_fields = ['hours']


class AttendanceLogDetailSerializer(AttendanceLogSerializer):
    """Детальный сериализатор для записей табеля"""
    employee_detail = EmployeeListSerializer(source='employee', read_only=True)

    class Meta(AttendanceLogSerializer.Meta):
        fields = AttendanceLogSerializer.Meta.fields + ['employee_detail']


class MonthlyReportSerializer(serializers.ModelSerializer):
    """Сериализатор для месячного отчета"""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    total_hours_formatted = serializers.SerializerMethodField()
    overtime_hours_formatted = serializers.SerializerMethodField()
    month_year = serializers.SerializerMethodField()

    class Meta:
        model = MonthlyReport
        fields = [
            'id', 'employee', 'employee_name', 'month', 'month_year',
            'total_hours', 'total_hours_formatted',
            'overtime_hours', 'overtime_hours_formatted'
        ]

    def get_total_hours_formatted(self, obj):
        return f"{obj.total_hours:.2f} ч."

    def get_overtime_hours_formatted(self, obj):
        return f"{obj.overtime_hours:.2f} ч."

    def get_month_year(self, obj):
        return obj.month


class AttendanceStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики посещаемости"""
    total_hours = serializers.FloatField()
    average_hours_per_day = serializers.FloatField()
    work_days = serializers.IntegerField()
    overtime_hours = serializers.FloatField()
    attendance_rate = serializers.FloatField()

    class Meta:
        fields = '__all__'


class TodayAttendanceSerializer(serializers.Serializer):
    """Сериализатор для отметок за сегодня"""
    logs = AttendanceLogSerializer(many=True)
    current_status = serializers.DictField()
    total_hours = serializers.FloatField()
    break_hours = serializers.FloatField()
    net_hours = serializers.FloatField()

    class Meta:
        fields = '__all__'