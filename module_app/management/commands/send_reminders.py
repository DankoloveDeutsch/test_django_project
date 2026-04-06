# module_app/management/commands/send_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from module_app.models import Reminder
from module_app.utils.notification import send_reminder_notification
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Отправка активных напоминаний'

    def add_arguments(self, parser):
        parser.add_argument('--check', action='store_true', help='Только проверить, не отправлять')
        parser.add_argument('--dry-run', action='store_true', help='Пробный запуск без отправки')

    def handle(self, *args, **options):
        self.stdout.write("🔔 Проверка напоминаний...")

        reminders = Reminder.objects.filter(
            is_sent=False,
            is_completed=False,
            due_date__gte=timezone.now().date()
        )

        to_send = [r for r in reminders if r.should_notify()]

        self.stdout.write(f"Найдено напоминаний: {reminders.count()}")
        self.stdout.write(f"Требуют отправки: {len(to_send)}")

        if options['check']:
            for r in to_send:
                self.stdout.write(f"  - {r.employee.full_name}: {r.title} (до {r.due_date})")
            return

        if options['dry_run']:
            self.stdout.write("Пробный запуск (отправка отключена)")
            return

        sent_count = 0
        for reminder in to_send:
            try:
                send_reminder_notification(reminder)
                reminder.is_sent = True
                reminder.sent_at = timezone.now()
                reminder.save()
                sent_count += 1
                self.stdout.write(f"✅ Отправлено: {reminder.title} для {reminder.employee.full_name}")
            except Exception as e:
                self.stdout.write(f"❌ Ошибка: {reminder.title} - {e}")
                logger.error(f"Ошибка отправки напоминания {reminder.id}: {e}")

        self.stdout.write(f"\n✅ Отправлено напоминаний: {sent_count}")