# module_app/services/report_service.py
"""
Сервис для работы с отчетами
"""

from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from ..models import EmployeeProfile, AttendanceLog, MonthlyReport, Reminder, GeneratedDocument


class ReportService:
    """Сервис для работы с отчетами"""

    @staticmethod
    def get_monthly_attendance_report(year, month, department=None):
        """
        Получение месячного отчета по посещаемости

        Args:
            year: год
            month: месяц (1-12)
            department: отдел (опционально)

        Returns:
            dict: данные отчета
        """
        employees = EmployeeProfile.objects.filter(is_active=True)
        if department:
            employees = employees.filter(department=department)

        report_data = []
        total_hours = 0
        total_overtime = 0
        total_employees = employees.count()

        for emp in employees:
            # Часы за месяц
            logs = AttendanceLog.objects.filter(
                employee=emp,
                date__year=year,
                date__month=month
            )
            total = logs.aggregate(total=Sum('hours'))['total'] or 0

            # Норма часов (обычно 160)
            norm = 160

            # Переработка
            overtime = max(0, total - norm)
            percentage = (total / norm * 100) if norm > 0 else 0

            report_data.append({
                'id': emp.id,
                'full_name': emp.full_name,
                'position': emp.position,
                'department': emp.department,
                'total_hours': round(total, 2),
                'norm_hours': norm,
                'overtime_hours': round(overtime, 2),
                'percentage': round(min(100, percentage), 1)
            })

            total_hours += total
            total_overtime += overtime

        return {
            'data': report_data,
            'summary': {
                'total_employees': total_employees,
                'total_hours': round(total_hours, 2),
                'total_overtime': round(total_overtime, 2),
                'avg_hours': round(total_hours / total_employees, 2) if total_employees else 0,
                'avg_overtime': round(total_overtime / total_employees, 2) if total_employees else 0
            }
        }

    @staticmethod
    def get_yearly_attendance_report(year, department=None):
        """
        Получение годового отчета по посещаемости

        Args:
            year: год
            department: отдел (опционально)

        Returns:
            dict: данные отчета
        """
        monthly_data = []
        total_hours = 0
        total_norm = 0
        total_overtime = 0

        for month in range(1, 13):
            monthly = ReportService.get_monthly_attendance_report(year, month, department)
            monthly_data.append({
                'month': month,
                'name': ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                         'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][month - 1],
                'total_hours': monthly['summary']['total_hours'],
                'overtime': monthly['summary']['total_overtime'],
                'norm_hours': monthly['summary']['total_employees'] * 160,
                'percentage': (monthly['summary']['total_hours'] / (monthly['summary']['total_employees'] * 160) * 100)
                if monthly['summary']['total_employees'] else 0
            })

            total_hours += monthly['summary']['total_hours']
            total_norm += monthly['summary']['total_employees'] * 160
            total_overtime += monthly['summary']['total_overtime']

        return {
            'monthly_data': monthly_data,
            'summary': {
                'total_hours': round(total_hours, 2),
                'total_norm': total_norm,
                'total_overtime': round(total_overtime, 2),
                'avg_monthly_hours': round(total_hours / 12, 2),
                'avg_monthly_overtime': round(total_overtime / 12, 2)
            }
        }

    @staticmethod
    def get_overtime_report(year, month=None, department=None):
        """
        Получение отчета по переработкам

        Args:
            year: год
            month: месяц (опционально)
            department: отдел (опционально)

        Returns:
            dict: данные отчета
        """
        employees = EmployeeProfile.objects.filter(is_active=True)
        if department:
            employees = employees.filter(department=department)

        overtime_data = []
        total_overtime = 0
        employees_with_overtime = 0

        for emp in employees:
            if month:
                # За конкретный месяц
                logs = AttendanceLog.objects.filter(
                    employee=emp,
                    date__year=year,
                    date__month=month
                )
                total = logs.aggregate(total=Sum('hours'))['total'] or 0
                norm = 160
                overtime = max(0, total - norm)

                if overtime > 0:
                    employees_with_overtime += 1

                overtime_data.append({
                    'id': emp.id,
                    'full_name': emp.full_name,
                    'department': emp.department,
                    'total_hours': round(total, 2),
                    'norm_hours': norm,
                    'overtime_hours': round(overtime, 2),
                    'overtime_percent': round(overtime / norm * 100, 1)
                })
                total_overtime += overtime
            else:
                # За год
                year_overtime = 0
                for m in range(1, 13):
                    logs = AttendanceLog.objects.filter(
                        employee=emp,
                        date__year=year,
                        date__month=m
                    )
                    total = logs.aggregate(total=Sum('hours'))['total'] or 0
                    norm = 160
                    year_overtime += max(0, total - norm)

                if year_overtime > 0:
                    employees_with_overtime += 1

                overtime_data.append({
                    'id': emp.id,
                    'full_name': emp.full_name,
                    'department': emp.department,
                    'total_hours': 0,  # Не рассчитываем для года
                    'norm_hours': 12 * 160,
                    'overtime_hours': round(year_overtime, 2),
                    'overtime_percent': round(year_overtime / (12 * 160) * 100, 1)
                })
                total_overtime += year_overtime

        # Сортировка по переработкам (по убыванию)
        overtime_data.sort(key=lambda x: x['overtime_hours'], reverse=True)

        return {
            'data': overtime_data,
            'summary': {
                'total_overtime': round(total_overtime, 2),
                'employees_with_overtime': employees_with_overtime,
                'avg_overtime': round(total_overtime / len(overtime_data), 2) if overtime_data else 0,
                'max_overtime': overtime_data[0]['overtime_hours'] if overtime_data else 0,
                'min_overtime': overtime_data[-1]['overtime_hours'] if overtime_data else 0
            }
        }

    @staticmethod
    def get_department_report(year, quarter=None):
        """
        Получение отчета по отделам

        Args:
            year: год
            quarter: квартал (1-4) или None для всего года

        Returns:
            dict: данные отчета
        """
        departments = EmployeeProfile.objects.filter(is_active=True).values_list('department', flat=True).distinct()

        department_data = []
        total_employees = 0
        total_hours = 0
        total_overtime = 0

        for dept in departments:
            employees = EmployeeProfile.objects.filter(department=dept, is_active=True)
            dept_employees = employees.count()
            total_employees += dept_employees

            # Расчет часов
            dept_hours = 0
            dept_overtime = 0

            for emp in employees:
                if quarter:
                    # За квартал
                    months = range((quarter - 1) * 3 + 1, quarter * 3 + 1)
                    for month in months:
                        logs = AttendanceLog.objects.filter(
                            employee=emp,
                            date__year=year,
                            date__month=month
                        )
                        total = logs.aggregate(total=Sum('hours'))['total'] or 0
                        dept_hours += total
                        dept_overtime += max(0, total - 160)
                else:
                    # За год
                    monthly_reports = MonthlyReport.objects.filter(employee=emp)
                    dept_hours += sum(r.total_hours for r in monthly_reports)
                    dept_overtime += sum(r.overtime_hours for r in monthly_reports)

            avg_hours = dept_hours / dept_employees if dept_employees else 0
            avg_overtime = dept_overtime / dept_employees if dept_employees else 0

            department_data.append({
                'name': dept or 'Без отдела',
                'employee_count': dept_employees,
                'total_hours': round(dept_hours, 2),
                'avg_hours': round(avg_hours, 2),
                'overtime_hours': round(dept_overtime, 2),
                'avg_overtime': round(avg_overtime, 2),
                'efficiency': round(min(100, (dept_hours / (dept_employees * 160 * (3 if quarter else 12)) * 100)), 1)
            })

            total_hours += dept_hours
            total_overtime += dept_overtime

        return {
            'data': department_data,
            'summary': {
                'total_employees': total_employees,
                'total_hours': round(total_hours, 2),
                'total_overtime': round(total_overtime, 2),
                'avg_per_employee': round(total_hours / total_employees, 2) if total_employees else 0,
                'avg_overtime': round(total_overtime / total_employees, 2) if total_employees else 0
            }
        }

    @staticmethod
    def get_document_statistics():
        """Получение статистики по документам"""
        today = timezone.now().date()

        return {
            'total_documents': GeneratedDocument.objects.count(),
            'by_status': {
                'draft': GeneratedDocument.objects.filter(status='draft').count(),
                'generated': GeneratedDocument.objects.filter(status='generated').count(),
                'signed': GeneratedDocument.objects.filter(status='signed').count(),
                'sent': GeneratedDocument.objects.filter(status='sent').count(),
                'archived': GeneratedDocument.objects.filter(status='archived').count()
            },
            'by_type': {
                doc_type: GeneratedDocument.objects.filter(document_type=doc_type).count()
                for doc_type, _ in GeneratedDocument.DOCUMENT_STATUS
            },
            'expiring_documents': EmployeeDocument.objects.filter(
                expiry_date__isnull=False,
                expiry_date__lte=today + timedelta(days=30),
                is_active=True
            ).count(),
            'expired_documents': EmployeeDocument.objects.filter(
                expiry_date__lt=today,
                is_active=True
            ).count()
        }

    @staticmethod
    def get_reminder_statistics():
        """Получение статистики по напоминаниям"""
        today = timezone.now().date()

        return {
            'total': Reminder.objects.count(),
            'active': Reminder.objects.filter(is_completed=False).count(),
            'completed': Reminder.objects.filter(is_completed=True).count(),
            'overdue': Reminder.objects.filter(due_date__lt=today, is_completed=False).count(),
            'due_today': Reminder.objects.filter(due_date=today, is_completed=False).count(),
            'due_week': Reminder.objects.filter(
                due_date__gte=today,
                due_date__lte=today + timedelta(days=7),
                is_completed=False
            ).count()
        }