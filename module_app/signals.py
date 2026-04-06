# module_app/signals.py
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
import logging

from .models import (
    EmployeeProfile, AttendanceLog, MonthlyReport,
    EmployeeDocument, Reminder, GeneratedDocument,
    WorkSchedule, AccountingIntegration
)

logger = logging.getLogger(__name__)

print("Сигналы загружены")


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Создание профиля сотрудника при создании пользователя"""
    try:
        if created:
            EmployeeProfile.objects.create(user=instance)
            logger.info(f"Создан профиль для пользователя {instance.username}")
    except Exception as e:
        logger.error(f"Ошибка при создании профиля: {e}")


@receiver(pre_save, sender=EmployeeProfile)
def generate_employee_code(sender, instance, **kwargs):
    """Генерация табельного номера"""
    if not instance.employee_code and instance.hire_date:
        year = instance.hire_date.year
        with transaction.atomic():
            count = EmployeeProfile.objects.filter(hire_date__year=year).count() + 1
            instance.employee_code = f"{year}{count:04d}"


@receiver(post_save, sender=EmployeeProfile)
def create_default_schedule(sender, instance, created, **kwargs):
    """Создание графика работы по умолчанию для нового сотрудника"""
    if created and instance.is_active:
        default_days = ['mon', 'tue', 'wed', 'thu', 'fri']
        for day in default_days:
            WorkSchedule.objects.get_or_create(
                employee=instance,
                day=day,
                defaults={'start_time': '09:00', 'end_time': '18:00'}
            )
        logger.info(f"Создан график работы для сотрудника {instance.full_name}")


@receiver(post_save, sender=AttendanceLog)
def update_monthly_report(sender, instance, **kwargs):
    """Обновление месячного отчета при добавлении записи в табеле"""
    try:
        employee = instance.employee
        log_date = instance.date
        month_str = log_date.strftime('%B %Y')

        logs_aggregate = AttendanceLog.objects.filter(
            employee=employee,
            date__year=log_date.year,
            date__month=log_date.month
        ).aggregate(total_hours=models.Sum('hours'))

        total_hours = logs_aggregate['total_hours'] or 0
        overtime_hours = max(0, total_hours - 160)

        report, created = MonthlyReport.objects.update_or_create(
            employee=employee,
            month=month_str,
            defaults={
                'total_hours': round(total_hours, 2),
                'overtime_hours': round(overtime_hours, 2)
            }
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении отчета: {e}")


@receiver(post_save, sender=EmployeeDocument)
def create_reminder_for_document_expiry(sender, instance, created, **kwargs):
    """Создание напоминания при добавлении документа с датой истечения"""
    if instance.expiry_date and instance.is_active:
        Reminder.objects.get_or_create(
            employee=instance.employee,
            related_document=instance,
            reminder_type='document_expiry',
            defaults={
                'title': f'Истекает срок документа: {instance.title}',
                'due_date': instance.expiry_date,
                'reminder_days_before': 30,
                'priority': 'high'
            }
        )
        logger.info(f"Создано напоминание о документе {instance.title}")


@receiver(pre_save, sender=EmployeeProfile)
def validate_dismissal(sender, instance, **kwargs):
    """Проверка и обработка увольнения сотрудника"""
    if instance.id:
        old_instance = EmployeeProfile.objects.get(id=instance.id)
        if old_instance.is_active and not instance.is_active:
            if not instance.dismissal_date:
                instance.dismissal_date = timezone.now().date()

            AccountingIntegration.objects.create(
                employee=instance,
                operation_type='dismissal',
                operation_date=instance.dismissal_date,
                data={'dismissal_date': str(instance.dismissal_date)},
                status='pending'
            )
            logger.info(f"Создана запись об увольнении для {instance.full_name}")