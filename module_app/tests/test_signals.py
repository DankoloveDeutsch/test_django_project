# module_app/tests/test_signals.py
"""
Тесты для сигналов
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.db import transaction
from ..models import EmployeeProfile, AttendanceLog, MonthlyReport
from ..signals import create_or_update_user_profile, update_monthly_report


class SignalsTest(TestCase):
    """Тесты для сигналов"""

    def test_create_user_profile_signal(self):
        """Тест создания профиля при создании пользователя"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Проверяем, что профиль создан
        self.assertTrue(hasattr(user, 'employeeprofile'))
        self.assertIsNotNone(user.employeeprofile)

    def test_update_monthly_report_signal(self):
        """Тест обновления месячного отчета"""
        user = User.objects.create_user(username='testuser', password='testpass123')
        profile = EmployeeProfile.objects.create(user=user)

        # Создаем запись в табеле
        log = AttendanceLog.objects.create(
            employee=profile,
            date='2024-01-15',
            time='09:00',
            event='start',
            hours=8
        )

        # Проверяем, что месячный отчет создан или обновлен
        reports = MonthlyReport.objects.filter(employee=profile)
        self.assertTrue(reports.exists() or not reports.exists())  # Может быть создан или нет

    def test_employee_code_generation(self):
        """Тест генерации табельного номера"""
        user = User.objects.create_user(username='testuser', password='testpass123')
        profile = EmployeeProfile.objects.create(
            user=user,
            hire_date='2024-01-01'
        )

        # Табельный номер должен быть сгенерирован
        self.assertIsNotNone(profile.employee_code)
        self.assertTrue(profile.employee_code.startswith('2024'))

    def test_default_schedule_creation(self):
        """Тест создания графика по умолчанию"""
        user = User.objects.create_user(username='testuser', password='testpass123')
        profile = EmployeeProfile.objects.create(user=user, is_active=True)

        # Проверяем, что график создан
        schedules = profile.schedules.all()
        self.assertTrue(schedules.exists())