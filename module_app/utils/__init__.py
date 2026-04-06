# module_app/utils/__init__.py
"""
Утилиты для системы управления табельным учетом
"""

from .document_generator import render_document_template

from .excel_export import export_to_excel, import_from_excel
from .notification import send_email, send_telegram, send_reminder_notification
from .helpers import format_date, calculate_age, validate_snils, validate_inn, format_phone, truncate_text, bytes_to_human
from .decorators import admin_required, hr_manager_required
from .validators import validate_snils, validate_inn, validate_phone, validate_birth_date, validate_hire_date

# Пробуем импортировать функции из report_generator
try:
    from .report_generator import generate_monthly_report_pdf, generate_annual_report, generate_government_report_pdf, generate_department_report_pdf
except ImportError as e:
    print(f"Warning: Could not import report_generator functions: {e}")
    generate_monthly_report_pdf = None
    generate_annual_report = None
    generate_government_report_pdf = None
    generate_department_report_pdf = None

# Пробуем импортировать функции из pdf_export
try:
    from .pdf_export import export_to_pdf, export_employee_card_pdf
except ImportError as e:
    print(f"Warning: Could not import pdf_export functions: {e}")
    export_to_pdf = None
    export_employee_card_pdf = None

# Пробуем импортировать функции из document_generator
try:
    from .document_generator import generate_document_pdf
except ImportError as e:
    print(f"Warning: Could not import document_generator functions: {e}")
    generate_document_pdf = None

__all__ = [
    'render_document_template',
    'generate_document_pdf',
    'generate_monthly_report_pdf',
    'generate_annual_report',
    'generate_government_report_pdf',
    'generate_department_report_pdf',
    'export_to_excel',
    'import_from_excel',
    'export_to_pdf',
    'export_employee_card_pdf',
    'send_email',
    'send_telegram',
    'send_reminder_notification',
    'format_date',
    'calculate_age',
    'validate_snils',
    'validate_inn',
    'validate_phone',
    'validate_birth_date',
    'validate_hire_date',
    'format_phone',
    'truncate_text',
    'bytes_to_human',
    'admin_required',
    'hr_manager_required'
]