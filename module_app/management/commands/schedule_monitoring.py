# module_app/management/commands/schedule_monitoring.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
import time
import signal
import sys


class Command(BaseCommand):
    help = 'Запуск мониторинга миграций по расписанию'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=3600, help='Интервал запуска в секундах')
        parser.add_argument('--once', action='store_true', help='Выполнить один раз и завершить')

    def handle(self, *args, **options):
        interval = options['interval']
        once = options['once']

        self.stdout.write(f"🔄 Запуск планировщика мониторинга (интервал: {interval} сек)")

        def signal_handler(sig, frame):
            self.stdout.write("\n⏹️ Остановка планировщика...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            if once:
                self.run_monitoring()
            else:
                while True:
                    self.run_monitoring()
                    self.stdout.write(f"💤 Ожидание {interval} секунд...")
                    time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write("\n⏹️ Планировщик остановлен")

    def run_monitoring(self):
        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(f"📊 Запуск мониторинга: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"{'=' * 60}")

        try:
            call_command('migration_monitor')
            self.stdout.write("✅ Мониторинг успешно выполнен\n")
        except Exception as e:
            self.stdout.write(f"❌ Ошибка мониторинга: {e}\n")