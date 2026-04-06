# module_app/services/reminder_service.py
"""
Сервис для работы с напоминаниями
"""

from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from ..models import Reminder, EmployeeProfile, EmployeeDocument
from ..utils.notification import send_reminder_notification


class ReminderService:
    """Сервис для работы с напоминаниями"""

    @staticmethod
    @transaction.atomic
    def create_reminder(employee_id, reminder_type, title, due_date,
                        description='', priority='medium', reminder_days_before=7,
                        related_document_id=None, related_generated_doc_id=None):
        """
        Создание напоминания

        Args:
            employee_id: ID сотрудника
            reminder_type: тип напоминания
            title: заголовок
            due_date: дата исполнения
            description: описание
            priority: приоритет (low/medium/high/critical)
            reminder_days_before: напомнить за N дней
            related_document_id: ID связанного документа
            related_generated_doc_id: ID связанного сгенерированного документа

        Returns:
            Reminder: созданное напоминание
        """
        employee = EmployeeProfile.objects.get(id=employee_id)

        reminder = Reminder.objects.create(
            employee=employee,
            reminder_type=reminder_type,
            title=title,
            description=description,
            due_date=due_date,
            reminder_days_before=reminder_days_before,
            priority=priority,
            related_document_id=related_document_id,
            related_generated_doc_id=related_generated_doc_id
        )

        # Если напоминание критическое и срок близок, отправляем сразу
        if priority == 'critical' and reminder.should_notify():
            send_reminder_notification(reminder)
            reminder.is_sent = True
            reminder.sent_at = timezone.now()
            reminder.save()

        return reminder

    @staticmethod
    def get_active_reminders(employee_id=None):
        """Получение активных напоминаний"""
        queryset = Reminder.objects.filter(is_completed=False)

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        return queryset.order_by('due_date', '-priority')

    @staticmethod
    def get_reminders_due_soon(days=7):
        """Получение напоминаний, которые скоро истекают"""
        today = timezone.now().date()
        due_date_limit = today + timedelta(days=days)

        return Reminder.objects.filter(
            due_date__gte=today,
            due_date__lte=due_date_limit,
            is_completed=False,
            is_sent=False
        ).order_by('due_date')

    @staticmethod
    @transaction.atomic
    def complete_reminder(reminder_id):
        """Отметка напоминания как выполненного"""
        reminder = Reminder.objects.get(id=reminder_id)
        reminder.is_completed = True
        reminder.completed_at = timezone.now()
        reminder.save()
        return reminder

    @staticmethod
    @transaction.atomic
    def send_pending_reminders():
        """Отправка всех ожидающих напоминаний"""
        reminders = Reminder.objects.filter(
            is_sent=False,
            is_completed=False
        )

        sent_count = 0
        for reminder in reminders:
            if reminder.should_notify():
                send_reminder_notification(reminder)
                reminder.is_sent = True
                reminder.sent_at = timezone.now()
                reminder.save()
                sent_count += 1

        return sent_count

    @staticmethod
    def auto_create_reminders():
        """
        Автоматическое создание напоминаний
        - Для дней рождения
        - Для истекающих документов
        - Для окончания испытательного срока
        """
        created_count = 0
        today = timezone.now().date()

        # Дни рождения (за 7 дней)
        upcoming_birthdays = EmployeeProfile.objects.filter(
            birth_date__isnull=False,
            is_active=True
        )

        for emp in upcoming_birthdays:
            birthday_this_year = emp.birth_date.replace(year=today.year)
            if today <= birthday_this_year <= today + timedelta(days=7):
                reminder, created = Reminder.objects.get_or_create(
                    employee=emp,
                    reminder_type='birthday',
                    due_date=birthday_this_year,
                    defaults={
                        'title': f'День рождения {emp.full_name}',
                        'description': 'Поздравьте сотрудника с днем рождения!',
                        'reminder_days_before': 1,
                        'priority': 'medium'
                    }
                )
                if created:
                    created_count += 1

        # Истекающие документы
        expiring_docs = EmployeeDocument.objects.filter(
            expiry_date__isnull=False,
            expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=30),
            is_active=True
        )

        for doc in expiring_docs:
            reminder, created = Reminder.objects.get_or_create(
                employee=doc.employee,
                related_document=doc,
                reminder_type='document_expiry',
                defaults={
                    'title': f'Истекает срок документа: {doc.title}',
                    'description': f'Документ {doc.title} истекает {doc.expiry_date}',
                    'due_date': doc.expiry_date,
                    'reminder_days_before': 30,
                    'priority': 'high'
                }
            )
            if created:
                created_count += 1

        # Окончание испытательного срока
        probation_end_date = today - timedelta(days=3)  # За 3 дня до окончания
        probation_employees = EmployeeProfile.objects.filter(
            employment_type='probation',
            hire_date__lte=probation_end_date,
            is_active=True
        )

        for emp in probation_employees:
            end_date = emp.hire_date + timedelta(days=90)  # 3 месяца
            if today <= end_date <= today + timedelta(days=7):
                reminder, created = Reminder.objects.get_or_create(
                    employee=emp,
                    reminder_type='probation_end',
                    due_date=end_date,
                    defaults={
                        'title': f'Окончание испытательного срока: {emp.full_name}',
                        'description': f'Испытательный срок заканчивается {end_date}',
                        'reminder_days_before': 3,
                        'priority': 'high'
                    }
                )
                if created:
                    created_count += 1

        return created_count

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
            'due_this_week': Reminder.objects.filter(
                due_date__gte=today,
                due_date__lte=today + timedelta(days=7),
                is_completed=False
            ).count(),
            'by_priority': {
                'critical': Reminder.objects.filter(priority='critical', is_completed=False).count(),
                'high': Reminder.objects.filter(priority='high', is_completed=False).count(),
                'medium': Reminder.objects.filter(priority='medium', is_completed=False).count(),
                'low': Reminder.objects.filter(priority='low', is_completed=False).count()
            }
        }