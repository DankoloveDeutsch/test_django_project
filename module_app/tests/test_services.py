# module_app/tests/test_services.py
"""
Тесты для сервисов
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from ..models import EmployeeProfile, Reminder
from ..services.employee_service import EmployeeService
from ..services.reminder_service import ReminderService
from ..services.document_service import DocumentService
from ..services.attendance_service import AttendanceService


class EmployeeServiceTest(TestCase):
    """Тесты для EmployeeService"""

    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Тест',
            'last_name': 'Пользователь'
        }
        self.profile_data = {
            'position': 'Разработчик',
            'department': 'IT'
        }

    def test_create_employee(self):
        """Тест создания сотрудника"""
        profile = EmployeeService.create_employee(self.user_data, self.profile_data)

        self.assertIsNotNone(profile)
        self.assertEqual(profile.position, 'Разработчик')
        self.assertEqual(profile.department, 'IT')
        self.assertTrue(profile.is_active)
        self.assertIsNotNone(profile.employee_code)

    def test_update_employee(self):
        """Тест обновления сотрудника"""
        profile = EmployeeService.create_employee(self.user_data, self.profile_data)

        updated = EmployeeService.update_employee(profile.id, {
            'position': 'Старший разработчик',
            'department': 'Development'
        })

        self.assertEqual(updated.position, 'Старший разработчик')
        self.assertEqual(updated.department, 'Development')

    def test_dismiss_employee(self):
        """Тест увольнения сотрудника"""
        profile = EmployeeService.create_employee(self.user_data, self.profile_data)
        dismissal_date = timezone.now().date()

        dismissed = EmployeeService.dismiss_employee(profile.id, dismissal_date, 'По собственному желанию')

        self.assertFalse(dismissed.is_active)
        self.assertEqual(dismissed.dismissal_date, dismissal_date)

    def test_get_employee_stats(self):
        """Тест получения статистики сотрудника"""
        profile = EmployeeService.create_employee(self.user_data, self.profile_data)
        stats = EmployeeService.get_employee_stats(profile.id)

        self.assertIn('total_hours', stats)
        self.assertIn('documents_count', stats)
        self.assertIn('reminders_count', stats)


class ReminderServiceTest(TestCase):
    """Тесты для ReminderService"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.profile = EmployeeProfile.objects.create(user=self.user)

    def test_create_reminder(self):
        """Тест создания напоминания"""
        reminder = ReminderService.create_reminder(
            employee_id=self.profile.id,
            reminder_type='medical',
            title='Медицинский осмотр',
            due_date=timezone.now().date() + timedelta(days=30),
            priority='high'
        )

        self.assertIsNotNone(reminder)
        self.assertEqual(reminder.title, 'Медицинский осмотр')
        self.assertFalse(reminder.is_sent)
        self.assertFalse(reminder.is_completed)

    def test_get_active_reminders(self):
        """Тест получения активных напоминаний"""
        ReminderService.create_reminder(
            employee_id=self.profile.id,
            reminder_type='medical',
            title='Медицинский осмотр',
            due_date=timezone.now().date() + timedelta(days=30),
            priority='high'
        )

        active = ReminderService.get_active_reminders()
        self.assertEqual(active.count(), 1)

    def test_complete_reminder(self):
        """Тест отметки напоминания как выполненного"""
        reminder = ReminderService.create_reminder(
            employee_id=self.profile.id,
            reminder_type='medical',
            title='Медицинский осмотр',
            due_date=timezone.now().date() + timedelta(days=30),
            priority='high'
        )

        completed = ReminderService.complete_reminder(reminder.id)
        self.assertTrue(completed.is_completed)
        self.assertIsNotNone(completed.completed_at)


class AttendanceServiceTest(TestCase):
    """Тесты для AttendanceService"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.profile = EmployeeProfile.objects.create(user=self.user)

    def test_can_mark_start(self):
        """Тест возможности отметки начала работы"""
        can_start = AttendanceService.can_mark(self.profile.id, 'start')
        self.assertTrue(can_start)

    def test_can_mark_end_without_start(self):
        """Тест невозможности отметки окончания без начала"""
        can_end = AttendanceService.can_mark(self.profile.id, 'end')
        self.assertFalse(can_end)

    def test_log_attendance_start(self):
        """Тест отметки начала работы"""
        log = AttendanceService.log_attendance(self.profile.id, 'start')
        self.assertIsNotNone(log)
        self.assertEqual(log.event, 'start')

    def test_get_today_stats(self):
        """Тест получения статистики за сегодня"""
        stats = AttendanceService.get_today_stats(self.profile.id)
        self.assertIn('total_hours', stats)
        self.assertIn('break_hours', stats)
        self.assertIn('net_hours', stats)