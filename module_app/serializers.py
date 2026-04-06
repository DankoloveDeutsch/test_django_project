# module_app/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone

from .models import (
    ModuleRecord, EmployeeProfile, WorkSchedule, AttendanceLog,
    MonthlyReport, DocumentTemplate, GeneratedDocument, EmployeeDocument,
    Reminder, AccountingIntegration, GovernmentReport, AuditLog
)


# ============ СЕРИАЛИЗАТОР ПОЛЬЗОВАТЕЛЯ ============
class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'is_active', 'date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


# ============ СЕРИАЛИЗАТОРЫ ДЛЯ СОТРУДНИКОВ ============
class WorkScheduleSerializer(serializers.ModelSerializer):
    """Сериализатор для графика работы"""
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = WorkSchedule
        fields = ['id', 'day', 'day_display', 'start_time', 'end_time']


class AttendanceLogSerializer(serializers.ModelSerializer):
    """Сериализатор для табеля учета"""
    event_display = serializers.CharField(source='get_event_display', read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = AttendanceLog
        fields = ['id', 'employee', 'employee_name', 'date', 'time', 'event', 'event_display', 'hours']


class MonthlyReportSerializer(serializers.ModelSerializer):
    """Сериализатор для месячного отчета"""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = MonthlyReport
        fields = ['id', 'employee', 'employee_name', 'month', 'total_hours', 'overtime_hours']


class EmployeeProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля сотрудника"""
    user = UserSerializer(read_only=True)
    full_name = serializers.CharField(source='full_name', read_only=True)
    age = serializers.IntegerField(read_only=True)
    total_hours = serializers.FloatField(read_only=True)
    schedules = WorkScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'user', 'full_name', 'employee_code', 'position', 'department',
            'phone', 'address', 'birth_date', 'age', 'hire_date', 'dismissal_date',
            'employment_type', 'salary', 'bank_account', 'tax_id', 'snils',
            'profile_picture', 'is_active', 'total_hours', 'schedules'
        ]
        read_only_fields = ['id', 'employee_code', 'total_hours']


class EmployeeProfileListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка сотрудников (краткий)"""
    full_name = serializers.CharField(source='full_name', read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = ['id', 'full_name', 'employee_code', 'position', 'department', 'is_active']


# ============ СЕРИАЛИЗАТОРЫ ДЛЯ ДОКУМЕНТОВ ============
class DocumentTemplateSerializer(serializers.ModelSerializer):
    """Сериализатор для шаблонов документов"""
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)

    class Meta:
        model = DocumentTemplate
        fields = ['id', 'name', 'template_type', 'template_type_display', 'content', 'variables', 'is_active',
                  'created_at']


class GeneratedDocumentSerializer(serializers.ModelSerializer):
    """Сериализатор для сгенерированных документов"""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = GeneratedDocument
        fields = [
            'id', 'employee', 'employee_name', 'document_type', 'document_type_display',
            'document_number', 'document_date', 'content', 'file', 'status', 'status_display',
            'signed_by', 'signed_at', 'notes'
        ]
        read_only_fields = ['document_number', 'document_date']


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    """Сериализатор для личных документов сотрудника"""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeDocument
        fields = [
            'id', 'employee', 'employee_name', 'document_type', 'document_type_display',
            'title', 'file', 'file_url', 'upload_date', 'expiry_date', 'description',
            'is_active', 'is_expired'
        ]
        read_only_fields = ['upload_date']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


# ============ СЕРИАЛИЗАТОРЫ ДЛЯ НАПОМИНАНИЙ ============
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
            'title', 'description', 'due_date', 'reminder_days_before', 'priority',
            'priority_display', 'is_sent', 'is_completed', 'should_notify'
        ]
        read_only_fields = ['sent_at', 'completed_at']

        def get_days_until_due(self, obj):
            if obj.due_date:
                delta = obj.due_date - timezone.now().date()
                return delta.days
            return None


# ============ СЕРИАЛИЗАТОРЫ ДЛЯ ИНТЕГРАЦИИ ============
class AccountingIntegrationSerializer(serializers.ModelSerializer):
    """Сериализатор для интеграции с бухгалтерией"""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AccountingIntegration
        fields = [
            'id', 'employee', 'employee_name', 'operation_type', 'operation_type_display',
            'operation_date', 'data', 'status', 'status_display', 'error_message',
            'created_at', 'processed_at'
        ]


class GovernmentReportSerializer(serializers.ModelSerializer):
    """Сериализатор для интеграции с бухгалтерией"""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    operation_type_display = serializers.CharField(source='get_operation_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AccountingIntegration
        fields = [
            'id', 'employee', 'employee_name', 'operation_type', 'operation_type_display',
            'operation_date', 'data', 'status', 'status_display', 'external_id',
            'error_message', 'created_at', 'processed_at'
        ]
        read_only_fields = ['created_at', 'processed_at']


# ============ СЕРИАЛИЗАТОР ДЛЯ АУДИТА ============
class AuditLogSerializer(serializers.ModelSerializer):
    """Сериализатор для журнала аудита"""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'username', 'action', 'model_name', 'object_repr', 'changes', 'ip_address',
                  'created_at']