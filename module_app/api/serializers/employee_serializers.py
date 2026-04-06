# module_app/api/serializers/employee_serializers.py
"""
Сериализаторы для сотрудников
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from ...models import EmployeeProfile, WorkSchedule


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class WorkScheduleSerializer(serializers.ModelSerializer):
    """Сериализатор для графика работы"""
    day_display = serializers.CharField(source='get_day_display', read_only=True)

    class Meta:
        model = WorkSchedule
        fields = ['id', 'day', 'day_display', 'start_time', 'end_time']


class EmployeeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка сотрудников"""
    full_name = serializers.CharField(source='full_name', read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'full_name', 'employee_code', 'position',
            'department', 'phone', 'hire_date', 'is_active'
        ]


class EmployeeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для сотрудника"""
    full_name = serializers.CharField(source='full_name', read_only=True)
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source='user', queryset=User.objects.all(), write_only=True
    )

    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'user', 'user_id', 'full_name', 'employee_code',
            'position', 'department', 'phone', 'address', 'birth_date',
            'hire_date', 'dismissal_date', 'employment_type', 'salary',
            'bank_account', 'tax_id', 'snils', 'profile_picture', 'is_active'
        ]
        read_only_fields = ['id', 'employee_code']


class EmployeeDetailSerializer(EmployeeSerializer):
    """Детальный сериализатор для сотрудника"""
    schedules = WorkScheduleSerializer(many=True, read_only=True)
    total_hours = serializers.FloatField(read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta(EmployeeSerializer.Meta):
        fields = EmployeeSerializer.Meta.fields + ['schedules', 'total_hours', 'age']