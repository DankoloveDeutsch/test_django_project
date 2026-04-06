# module_app/utils/notification.py
"""
Отправка уведомлений (Email, Telegram, SMS)
"""

import os
import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import requests

logger = logging.getLogger(__name__)


def send_email(subject, message, to_email, html_message=None):
    """
    Отправка email

    Args:
        subject: тема письма
        message: текст письма
        to_email: получатель
        html_message: HTML версия письма

    Returns:
        bool: успешность отправки
    """
    try:
        if html_message:
            email = EmailMultiAlternatives(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email])
            email.attach_alternative(html_message, "text/html")
            email.send()
        else:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email])
        return True
    except Exception as e:
        logger.error(f"Error sending email to {to_email}: {e}")
        return False


def send_telegram(message, chat_id=None):
    """
    Отправка сообщения в Telegram

    Args:
        message: текст сообщения
        chat_id: ID чата (опционально)

    Returns:
        bool: успешность отправки
    """
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not bot_token:
        logger.warning("Telegram bot token not configured")
        return False

    if not chat_id:
        chat_id = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', None)

    if not chat_id:
        logger.warning("Telegram chat ID not configured")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False


def send_reminder_notification(reminder):
    """
    Отправка уведомления о напоминании

    Args:
        reminder: объект Reminder
    """
    # Формируем сообщение
    subject = f"Напоминание: {reminder.title}"

    context = {
        'reminder': reminder,
        'employee': reminder.employee,
        'days_left': (reminder.due_date - reminder.due_date.today()).days
    }

    message = render_to_string('module_app/emails/reminder.txt', context)
    html_message = render_to_string('module_app/emails/reminder.html', context)

    # Отправка email
    if reminder.employee.user.email:
        send_email(subject, message, reminder.employee.user.email, html_message)

    # Отправка Telegram (для администраторов)
    telegram_message = f"🔔 <b>Напоминание</b>\n\n{reminder.title}\nСотрудник: {reminder.employee.full_name}\nДата: {reminder.due_date.strftime('%d.%m.%Y')}"
    send_telegram(telegram_message)


def send_document_notification(document):
    """
    Отправка уведомления о новом документе

    Args:
        document: объект GeneratedDocument
    """
    subject = f"Новый документ: {document.get_document_type_display()} №{document.document_number}"

    context = {
        'document': document,
        'employee': document.employee
    }

    message = render_to_string('module_app/emails/document.txt', context)
    html_message = render_to_string('module_app/emails/document.html', context)

    if document.employee.user.email:
        send_email(subject, message, document.employee.user.email, html_message)


def send_employee_notification(employee, action):
    """
    Отправка уведомления о действии с сотрудником

    Args:
        employee: объект EmployeeProfile
        action: действие (hire, dismissal, update)
    """
    messages = {
        'hire': f"Вы приняты на работу в должности {employee.position}",
        'dismissal': f"Ваше трудовое соглашение расторгнуто",
        'update': "Данные вашего профиля обновлены"
    }

    subject = f"Уведомление: {messages.get(action, 'Изменение статуса')}"
    message = messages.get(action, '')

    if employee.user.email:
        send_email(subject, message, employee.user.email)


def send_error_notification(error_message, context=None):
    """
    Отправка уведомления об ошибке администраторам

    Args:
        error_message: текст ошибки
        context: дополнительный контекст
    """
    admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
    if not admin_emails:
        return

    subject = f"[ERROR] {error_message[:50]}"
    message = f"Ошибка: {error_message}\n\nКонтекст: {context}"

    for email in admin_emails:
        send_email(subject, message, email)


def send_bulk_notifications(reminders):
    """
    Массовая отправка уведомлений

    Args:
        reminders: QuerySet напоминаний

    Returns:
        dict: результаты отправки
    """
    results = {
        'total': reminders.count(),
        'sent': 0,
        'failed': 0,
        'errors': []
    }

    for reminder in reminders:
        try:
            send_reminder_notification(reminder)
            reminder.is_sent = True
            reminder.sent_at = timezone.now()
            reminder.save()
            results['sent'] += 1
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'reminder_id': reminder.id,
                'error': str(e)
            })

    return results