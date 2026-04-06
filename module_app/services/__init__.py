# module_app/services/__init__.py
"""
Сервисный слой для бизнес-логики
"""

from .employee_service import EmployeeService
from .document_service import DocumentService
from .attendance_service import AttendanceService
from .reminder_service import ReminderService
from .report_service import ReportService
from .accounting_service import AccountingService

__all__ = [
    'EmployeeService',
    'DocumentService',
    'AttendanceService',
    'ReminderService',
    'ReportService',
    'AccountingService'
]