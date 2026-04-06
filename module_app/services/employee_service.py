# module_app/services/employee_service.py
"""
Сервис для работы с сотрудниками
"""

from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
from ..models import EmployeeProfile, WorkSchedule, Reminder


class EmployeeService:
    """Сервис для работы с сотрудниками"""

    @staticmethod
    @transaction.atomic
    def create_employee(user_data, profile_data):
        """Создание сотрудника"""
        # Создание пользователя
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', '')
        )

        # Создание профиля
        profile = EmployeeProfile.objects.create(
            user=user,
            **profile_data
        )

        # Создание графика работы по умолчанию
        default_days = ['mon', 'tue', 'wed', 'thu', 'fri']
        for day in default_days:
            WorkSchedule.objects.create(
                employee=profile,
                day=day,
                start_time='09:00',
                end_time='18:00'
            )

        # Создание напоминания о медосмотре
        Reminder.objects.create(
            employee=profile,
            reminder_type='medical',
            title='Медицинский осмотр',
            due_date=timezone.now().date() + timezone.timedelta(days=365),
            priority='high'
        )

        return profile

    @staticmethod
    @transaction.atomic
    def update_employee(profile_id, data):
        """Обновление данных сотрудника"""
        profile = EmployeeProfile.objects.get(id=profile_id)

        # Обновление пользователя
        user = profile.user
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        user.save()

        # Обновление профиля
        for key, value in data.items():
            if key not in ['first_name', 'last_name', 'email']:
                setattr(profile, key, value)
        profile.save()

        return profile

    @staticmethod
    def dismiss_employee(profile_id, dismissal_date, reason):
        """Увольнение сотрудника"""
        profile = EmployeeProfile.objects.get(id=profile_id)
        profile.is_active = False
        profile.dismissal_date = dismissal_date
        profile.save()

        return profile

    @staticmethod
    def get_employee_stats(profile_id):
        """Получение статистики по сотруднику"""
        profile = EmployeeProfile.objects.get(id=profile_id)

        return {
            'total_hours': profile.total_hours,
            'documents_count': profile.personal_documents.count(),
            'reminders_count': profile.reminders.filter(is_completed=False).count(),
            'attendance_days': profile.attendance_logs.count()
        }

    @staticmethod
    def search_employees(query, filters=None):
        """Поиск сотрудников"""
        employees = EmployeeProfile.objects.all()

        if query:
            employees = employees.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(position__icontains=query) |
                Q(department__icontains=query) |
                Q(employee_code__icontains=query)
            )

        if filters:
            if filters.get('department'):
                employees = employees.filter(department=filters['department'])
            if filters.get('is_active') is not None:
                employees = employees.filter(is_active=filters['is_active'])
            if filters.get('hire_date_from'):
                employees = employees.filter(hire_date__gte=filters['hire_date_from'])
            if filters.get('hire_date_to'):
                employees = employees.filter(hire_date__lte=filters['hire_date_to'])

        return employees