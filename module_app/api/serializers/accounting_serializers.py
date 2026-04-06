# module_app/api/serializers/accounting_serializers.py
"""
Сериализаторы для интеграции с бухгалтерией (API)
"""

from rest_framework import serializers
from ...models import AccountingIntegration


class AccountingIntegrationSerializer(serializers.ModelSerializer):
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