# module_app/services/attendance_service.py
"""
Сервис для учета рабочего времени
"""

from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from ..models import AttendanceLog, MonthlyReport


class AttendanceService:
    """Сервис для учета рабочего времени"""

    @staticmethod
    def log_attendance(employee_id, event):
        """Отметка времени"""
        profile = EmployeeProfile.objects.get(id=employee_id)
        today = timezone.now().date()
        now = timezone.now().time()

        # Проверка возможности отметки
        if not AttendanceService.can_mark(profile.id, event):
            raise ValueError(f'Невозможно отметить событие {event}')

        return AttendanceLog.objects.create(
            employee=profile,
            date=today,
            time=now,
            event=event
        )

    @staticmethod
    def can_mark(employee_id, event):
        """Проверка возможности отметки"""
        profile = EmployeeProfile.objects.get(id=employee_id)
        today = timezone.now().date()

        logs = AttendanceLog.objects.filter(employee=profile, date=today).order_by('time')
        last_event = logs.last()

        if event == 'start':
            return not logs.filter(event='start').exists()
        if event == 'break':
            return last_event and last_event.event == 'start' and not logs.filter(event='break').exists()
        if event == 'resume':
            return last_event and last_event.event == 'break'
        if event == 'end':
            return last_event and last_event.event in ['start', 'resume'] and not logs.filter(event='end').exists()

        return False

    @staticmethod
    def get_today_stats(employee_id):
        """Получение статистики за сегодня"""
        profile = EmployeeProfile.objects.get(id=employee_id)
        today = timezone.now().date()

        logs = AttendanceLog.objects.filter(employee=profile, date=today).order_by('time')

        total_hours = 0
        break_hours = 0

        start_log = logs.filter(event='start').first()
        end_log = logs.filter(event='end').first()

        if start_log and end_log:
            start_time = datetime.combine(today, start_log.time)
            end_time = datetime.combine(today, end_log.time)
            total_hours = (end_time - start_time).total_seconds() / 3600

        break_logs = logs.filter(event='break')
        for break_log in break_logs:
            resume_log = logs.filter(event='resume', time__gt=break_log.time).first()
            if resume_log:
                break_start = datetime.combine(today, break_log.time)
                break_end = datetime.combine(today, resume_log.time)
                break_hours += (break_end - break_start).total_seconds() / 3600

        net_hours = total_hours - break_hours

        return {
            'logs': logs,
            'total_hours': round(total_hours, 2),
            'break_hours': round(break_hours, 2),
            'net_hours': round(net_hours, 2)
        }

    @staticmethod
    def get_monthly_stats(employee_id, year, month):
        """Получение статистики за месяц"""
        profile = EmployeeProfile.objects.get(id=employee_id)

        logs = AttendanceLog.objects.filter(
            employee=profile,
            date__year=year,
            date__month=month
        )

        total_hours = logs.aggregate(Sum('hours'))['hours__sum'] or 0
        work_days = logs.filter(event='end').count()

        return {
            'total_hours': round(total_hours, 2),
            'work_days': work_days,
            'avg_hours_per_day': round(total_hours / work_days, 2) if work_days else 0
        }

    @staticmethod
    def calculate_overtime(employee_id, year, month):
        """Расчет переработок"""
        stats = AttendanceService.get_monthly_stats(employee_id, year, month)
        norm = 160  # Норма часов в месяц
        overtime = max(0, stats['total_hours'] - norm)

        return round(overtime, 2)

    @staticmethod
    def update_monthly_report(employee_id, year, month):
        """Обновление месячного отчета"""
        from ..models import MonthlyReport

        profile = EmployeeProfile.objects.get(id=employee_id)
        month_str = f"{month:02d}.{year}"

        total_hours = AttendanceService.get_monthly_stats(employee_id, year, month)['total_hours']
        overtime = AttendanceService.calculate_overtime(employee_id, year, month)

        report, created = MonthlyReport.objects.update_or_create(
            employee=profile,
            month=month_str,
            defaults={
                'total_hours': total_hours,
                'overtime_hours': overtime
            }
        )

        return report