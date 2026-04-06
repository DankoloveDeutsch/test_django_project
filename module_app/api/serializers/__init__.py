# module_app/api/serializers/__init__.py
"""
API сериализаторы для системы управления табельным учетом
"""

# Абсолютные импорты из основного приложения
from module_app.models import (
    EmployeeProfile, WorkSchedule, AttendanceLog, MonthlyReport,
    DocumentTemplate, GeneratedDocument, EmployeeDocument,
    Reminder, AccountingIntegration, GovernmentReport, AuditLog
)

# Импорты из подпапок
from .employee_serializers import (
    UserSerializer,
    EmployeeListSerializer,
    EmployeeSerializer,
    EmployeeDetailSerializer,
    WorkScheduleSerializer as EmpWorkScheduleSerializer
)

from .attendance_serializers import (
    AttendanceLogSerializer,
    AttendanceLogDetailSerializer,
    MonthlyReportSerializer,
    TodayAttendanceSerializer,
    AttendanceStatsSerializer
)

from .document_serializers import (
    DocumentTemplateSerializer,
    DocumentTemplateDetailSerializer,
    GeneratedDocumentSerializer,
    GeneratedDocumentDetailSerializer,
    EmployeeDocumentSerializer,
    EmployeeDocumentDetailSerializer,
    DocumentGenerationSerializer,
    BulkDocumentGenerationSerializer
)

from .report_serializers import (
    EmployeeStatisticsSerializer,
    AttendanceStatisticsSerializer,
    DocumentStatisticsSerializer,
    DepartmentReportSerializer,
    OvertimeReportSerializer,
    MonthlyReportDataSerializer,
    MonthlyReportSummarySerializer,
    MonthlyReportSerializer as MonthlyReportFullSerializer,
    YearlyReportDataSerializer,
    YearlyReportSummarySerializer,
    YearlyReportSerializer,
    DashboardStatsSerializer
)

from .reminder_serializers import ReminderSerializer
from .accounting_serializers import AccountingIntegrationSerializer

__all__ = [
    # Models
    'EmployeeProfile',
    'WorkSchedule',
    'AttendanceLog',
    'MonthlyReport',
    'DocumentTemplate',
    'GeneratedDocument',
    'EmployeeDocument',
    'Reminder',
    'AccountingIntegration',

    # Employee serializers
    'UserSerializer',
    'EmployeeListSerializer',
    'EmployeeSerializer',
    'EmployeeDetailSerializer',
    'EmpWorkScheduleSerializer',

    # Attendance serializers
    'AttendanceLogSerializer',
    'AttendanceLogDetailSerializer',
    'MonthlyReportSerializer',
    'TodayAttendanceSerializer',
    'AttendanceStatsSerializer',

    # Document serializers
    'DocumentTemplateSerializer',
    'DocumentTemplateDetailSerializer',
    'GeneratedDocumentSerializer',
    'GeneratedDocumentDetailSerializer',
    'EmployeeDocumentSerializer',
    'EmployeeDocumentDetailSerializer',
    'DocumentGenerationSerializer',
    'BulkDocumentGenerationSerializer',

    # Report serializers
    'EmployeeStatisticsSerializer',
    'AttendanceStatisticsSerializer',
    'DocumentStatisticsSerializer',
    'DepartmentReportSerializer',
    'OvertimeReportSerializer',
    'MonthlyReportDataSerializer',
    'MonthlyReportSummarySerializer',
    'MonthlyReportFullSerializer',
    'YearlyReportDataSerializer',
    'YearlyReportSummarySerializer',
    'YearlyReportSerializer',
    'DashboardStatsSerializer',

    # Reminder serializer
    'ReminderSerializer',

    # Accounting serializer
    'AccountingIntegrationSerializer'
]