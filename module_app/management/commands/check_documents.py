# module_app/management/commands/check_documents.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from module_app.models import EmployeeDocument, Reminder
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Проверка документов с истекающим сроком'

    def add_arguments(self, parser):
        parser.add_argument('--verify', action='store_true', help='Проверить и создать напоминания')
        parser.add_argument('--days', type=int, default=30, help='Количество дней для проверки')

    def handle(self, *args, **options):
        self.stdout.write("📄 Проверка документов...")

        today = timezone.now().date()
        check_date = today + timezone.timedelta(days=options['days'])

        expiring_docs = EmployeeDocument.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=check_date,
            is_active=True
        )

        self.stdout.write(f"Найдено документов с истекающим сроком: {expiring_docs.count()}")

        if options['verify']:
            created = 0
            for doc in expiring_docs:
                reminder, created_flag = Reminder.objects.get_or_create(
                    employee=doc.employee,
                    related_document=doc,
                    reminder_type='document_expiry',
                    defaults={
                        'title': f'Истекает срок документа: {doc.title}',
                        'due_date': doc.expiry_date,
                        'reminder_days_before': options['days'],
                        'priority': 'high'
                    }
                )
                if created_flag:
                    created += 1
                    self.stdout.write(f"  ✅ Создано напоминание: {doc.title}")

            self.stdout.write(f"\n✅ Создано напоминаний: {created}")