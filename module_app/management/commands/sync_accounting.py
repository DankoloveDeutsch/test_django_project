# module_app/management/commands/sync_accounting.py
from django.core.management.base import BaseCommand
from module_app.models import AccountingIntegration
from module_app.utils.accounting_api import sync_to_1c
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Синхронизация с бухгалтерской системой 1С'

    def add_arguments(self, parser):
        parser.add_argument('--check', action='store_true', help='Только проверить, не отправлять')
        parser.add_argument('--retry-failed', action='store_true', help='Повторить отправку для ошибочных')

    def handle(self, *args, **options):
        self.stdout.write("🔄 Синхронизация с 1С...")

        if options['retry_failed']:
            operations = AccountingIntegration.objects.filter(status='error')
        else:
            operations = AccountingIntegration.objects.filter(status='pending')

        self.stdout.write(f"Найдено операций для отправки: {operations.count()}")

        if options['check']:
            for op in operations:
                self.stdout.write(
                    f"  - {op.employee.full_name}: {op.get_operation_type_display()} ({op.operation_date})")
            return

        success_count = 0
        for operation in operations:
            try:
                result = sync_to_1c(operation)
                if result['success']:
                    operation.status = 'sent'
                    operation.external_id = result.get('external_id')
                    operation.save()
                    success_count += 1
                    self.stdout.write(f"✅ Отправлено: {operation}")
                else:
                    operation.status = 'error'
                    operation.error_message = result.get('error', 'Неизвестная ошибка')
                    operation.save()
                    self.stdout.write(f"❌ Ошибка: {operation} - {operation.error_message}")
            except Exception as e:
                operation.status = 'error'
                operation.error_message = str(e)
                operation.save()
                self.stdout.write(f"❌ Ошибка: {operation} - {e}")
                logger.error(f"Ошибка синхронизации {operation.id}: {e}")

        self.stdout.write(f"\n✅ Успешно отправлено: {success_count}")