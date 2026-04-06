# module_app/tests/test_models.py
"""
Тесты для моделей
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from ..models import EmployeeProfile, AttendanceLog, Reminder


class EmployeeProfileModelTest(TestCase):
    """Тесты для модели EmployeeProfile"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Тест',
            last_name='Пользователь'
        )

    def test_create_employee_profile(self):
        """Тест создания профиля сотрудника"""
        profile = EmployeeProfile.objects.create(
            user=self.user,
            position='Разработчик',
            department='IT'
        )

        self.assertEqual(profile.user.username, 'testuser')
        self.assertEqual(profile.position, 'Разработчик')
        self.assertEqual(profile.full_name, 'Тест Пользователь')
        self.assertTrue(profile.is_active)

    def test_employee_code_generation(self):
        """Тест генерации табельного номера"""
        profile = EmployeeProfile.objects.create(
            user=self.user,
            hire_date=timezone.now().date()
        )
        self.assertIsNotNone(profile.employee_code)

    def test_total_hours_property(self):
        """Тест свойства total_hours"""
        profile = EmployeeProfile.objects.create(user=self.user)

        AttendanceLog.objects.create(
            employee=profile,
            date=timezone.now().date(),
            time=timezone.now().time(),
            event='start',
            hours=8
        )

        self.assertEqual(profile.total_hours, 8)

    def test_age_property(self):
        """Тест свойства age"""
        from datetime import date
        profile = EmployeeProfile.objects.create(
            user=self.user,
            birth_date=date(1990, 1, 1)
        )

        self.assertIsNotNone(profile.age)


class ReminderModelTest(TestCase):
    """Тесты для модели Reminder"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.profile = EmployeeProfile.objects.create(user=self.user)

    def test_create_reminder(self):
        """Тест создания напоминания"""
        reminder = Reminder.objects.create(
            employee=self.profile,
            reminder_type='medical',
            title='Медицинский осмотр',
            due_date=timezone.now().date() + timezone.timedelta(days=30),
            priority='high'
        )

        self.assertEqual(reminder.employee, self.profile)
        self.assertEqual(reminder.title, 'Медицинский осмотр')
        self.assertFalse(reminder.is_sent)
        self.assertFalse(reminder.is_completed)

    def test_should_notify(self):
        """Тест метода should_notify"""
        reminder = Reminder.objects.create(
            employee=self.profile,
            reminder_type='medical',
            title='Медицинский осмотр',
            due_date=timezone.now().date() + timezone.timedelta(days=5),
            reminder_days_before=7,
            priority='high'
        )

        self.assertTrue(reminder.should_notify())

        reminder.is_sent = True
        self.assertFalse(reminder.should_notify())

        reminder.is_sent = False
        reminder.is_completed = True
        self.assertFalse(reminder.should_notify())