# module_app/api/serializers/report_serializers.py
"""
Сериализаторы для отчетов
"""

from rest_framework import serializers


class EmployeeStatisticsSerializer(serializers.Serializer):
    """Сериализатор для статистики по сотрудникам"""
    total_employees = serializers.IntegerField()
    active_employees = serializers.IntegerField()
    dismissed_employees = serializers.IntegerField()
    employees_on_probation = serializers.IntegerField()
    average_age = serializers.FloatField()
    average_salary = serializers.DecimalField(max_digits=10, decimal_places=2)
    departments_count = serializers.IntegerField()

    class Meta:
        fields = '__all__'


class DepartmentStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики по отделам"""
    name = serializers.CharField()
    employee_count = serializers.IntegerField()
    total_hours = serializers.FloatField()
    avg_hours = serializers.FloatField()
    overtime_hours = serializers.FloatField()
    efficiency = serializers.FloatField()


class AttendanceStatisticsSerializer(serializers.Serializer):
    """Сериализатор для статистики посещаемости"""
    total_hours_this_month = serializers.FloatField()
    average_hours_per_day = serializers.FloatField()
    total_overtime_this_month = serializers.FloatField()
    attendance_rate = serializers.FloatField()
    most_active_employees = serializers.ListField(child=serializers.DictField())
    department_stats = DepartmentStatsSerializer(many=True)

    class Meta:
        fields = '__all__'


class DocumentStatisticsSerializer(serializers.Serializer):
    """Сериализатор для статистики документов"""
    total_documents = serializers.IntegerField()
    expired_documents = serializers.IntegerField()
    expiring_soon_documents = serializers.IntegerField()
    documents_by_type = serializers.DictField()
    documents_by_status = serializers.DictField()
    total_documents_size = serializers.CharField()

    class Meta:
        fields = '__all__'


class MonthlyReportDataSerializer(serializers.Serializer):
    """Сериализатор для данных месячного отчета"""
    employee_id = serializers.IntegerField()
    full_name = serializers.CharField()
    position = serializers.CharField()
    department = serializers.CharField()
    total_hours = serializers.FloatField()
    norm_hours = serializers.IntegerField()
    overtime_hours = serializers.FloatField()
    percentage = serializers.FloatField()


class MonthlyReportSummarySerializer(serializers.Serializer):
    """Сериализатор для сводки месячного отчета"""
    total_employees = serializers.IntegerField()
    total_hours = serializers.FloatField()
    total_overtime = serializers.FloatField()
    avg_hours = serializers.FloatField()
    avg_overtime = serializers.FloatField()
    avg_percentage = serializers.FloatField()


class MonthlyReportSerializer(serializers.Serializer):
    """Сериализатор для полного месячного отчета"""
    data = MonthlyReportDataSerializer(many=True)
    summary = MonthlyReportSummarySerializer()
    chart_labels = serializers.ListField(child=serializers.CharField())
    chart_data = serializers.ListField(child=serializers.FloatField())


class YearlyReportDataSerializer(serializers.Serializer):
    """Сериализатор для данных годового отчета"""
    month = serializers.IntegerField()
    name = serializers.CharField()
    total_hours = serializers.FloatField()
    overtime = serializers.FloatField()
    norm_hours = serializers.IntegerField()
    percentage = serializers.FloatField()


class YearlyReportSummarySerializer(serializers.Serializer):
    """Сериализатор для сводки годового отчета"""
    total_hours = serializers.FloatField()
    total_norm = serializers.IntegerField()
    total_overtime = serializers.FloatField()
    avg_monthly_hours = serializers.FloatField()
    avg_monthly_overtime = serializers.FloatField()


class YearlyReportSerializer(serializers.Serializer):
    """Сериализатор для полного годового отчета"""
    monthly_data = YearlyReportDataSerializer(many=True)
    summary = YearlyReportSummarySerializer()


class DepartmentReportSerializer(serializers.Serializer):
    """Сериализатор для отчета по отделам"""
    name = serializers.CharField()
    employee_count = serializers.IntegerField()
    total_hours = serializers.FloatField()
    avg_hours = serializers.FloatField()
    overtime_hours = serializers.FloatField()
    avg_overtime = serializers.FloatField()
    efficiency = serializers.FloatField()


class DepartmentReportSummarySerializer(serializers.Serializer):
    """Сериализатор для сводки отчета по отделам"""
    total_employees = serializers.IntegerField()
    total_hours = serializers.FloatField()
    total_overtime = serializers.FloatField()
    avg_per_employee = serializers.FloatField()
    avg_overtime = serializers.FloatField()


class DepartmentReportFullSerializer(serializers.Serializer):
    """Сериализатор для полного отчета по отделам"""
    data = DepartmentReportSerializer(many=True)
    summary = DepartmentReportSummarySerializer()
    chart_labels = serializers.ListField(child=serializers.CharField())
    chart_data = serializers.ListField(child=serializers.FloatField())
    chart_overtime = serializers.ListField(child=serializers.FloatField())


class OvertimeEmployeeSerializer(serializers.Serializer):
    """Сериализатор для данных сотрудника в отчете по переработкам"""
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    department = serializers.CharField()
    total_hours = serializers.FloatField()
    norm_hours = serializers.IntegerField()
    overtime_hours = serializers.FloatField()
    overtime_percent = serializers.FloatField()


class OvertimeReportSummarySerializer(serializers.Serializer):
    """Сериализатор для сводки отчета по переработкам"""
    total_overtime = serializers.FloatField()
    employees_with_overtime = serializers.IntegerField()
    avg_overtime = serializers.FloatField()
    max_overtime = serializers.FloatField()
    min_overtime = serializers.FloatField()


class OvertimeReportSerializer(serializers.Serializer):
    """Сериализатор для полного отчета по переработкам"""
    data = OvertimeEmployeeSerializer(many=True)
    summary = OvertimeReportSummarySerializer()
    trend_labels = serializers.ListField(child=serializers.CharField())
    trend_data = serializers.ListField(child=serializers.FloatField())


class DashboardStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики дашборда"""
    total_employees = serializers.IntegerField()
    active_employees = serializers.IntegerField()
    active_reminders = serializers.IntegerField()
    expired_documents = serializers.IntegerField()
    total_hours_this_month = serializers.FloatField()
    attendance_rate = serializers.FloatField()

    class Meta:
        fields = '__all__'