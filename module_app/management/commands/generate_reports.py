# module_app/management/commands/generate_reports.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from module_app.models import GovernmentReport
from module_app.utils.report_generator import generate_government_report
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Генерация отчетов для государственных органов'

    def add_arguments(self, parser):
        parser.add_argument('--report-type', type=str, help='Тип отчета (pension_fund/tax_service/social_fund)')
        parser.add_argument('--period', type=str, help='Период (например: 01.2025)')
        parser.add_argument('--auto', action='store_true', help='Автоматическая генерация для всех типов')

    def handle(self, *args, **options):
        self.stdout.write("📊 Генерация отчетов...")

        if options['auto']:
            # Автоматическая генерация за прошлый месяц
            last_month = timezone.now().date().replace(day=1) - timezone.timedelta(days=1)
            period = last_month.strftime('%m.%Y')
            types = ['pension_fund', 'tax_service', 'social_fund']

            for report_type in types:
                self.generate_report(report_type, period)

        elif options['report_type'] and options['period']:
            self.generate_report(options['report_type'], options['period'])

        else:
            self.stdout.write("Укажите --report-type и --period или используйте --auto")

    def generate_report(self, report_type, period):
        self.stdout.write(f"Генерация отчета: {report_type} за {period}")

        try:
            report = generate_government_report(report_type, period)
            self.stdout.write(f"✅ Отчет создан: {report.report_file.url}")
        except Exception as e:
            self.stdout.write(f"❌ Ошибка: {e}")
            logger.error(f"Ошибка генерации отчета {report_type}: {e}")