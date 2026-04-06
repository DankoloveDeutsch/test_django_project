# module_app/management/commands/migration_monitor.py
from django.core.management.base import BaseCommand
from django.db import connection
import time


class Command(BaseCommand):
    help = 'Мониторинг выполнения миграций'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("📊 МОНИТОРИНГ СОСТОЯНИЯ БАЗЫ ДАННЫХ")
        self.stdout.write("=" * 80)

        # Проверка размера таблиц
        self.stdout.write("\n📁 РАЗМЕРЫ ТАБЛИЦ:")
        self.stdout.write("-" * 60)

        with connection.cursor() as cursor:
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT 
                        tablename,
                        pg_size_pretty(pg_total_relation_size(tablename)) as size
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(tablename) DESC
                    LIMIT 10
                """)

                for row in cursor.fetchall():
                    self.stdout.write(f"  📊 {row[0]:<35} {row[1]:>10}")

        # Проверка количества записей
        models_to_check = [
            'app_employeeprofile',
            'app_attendancelog',
            'app_generateddocument',
            'app_employeedocument',
            'app_reminder'
        ]

        self.stdout.write("\n📈 КОЛИЧЕСТВО ЗАПИСЕЙ:")
        self.stdout.write("-" * 60)

        with connection.cursor() as cursor:
            for table in models_to_check:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f"  • {table:<30} {count:>10} записей")
                except Exception as e:
                    self.stdout.write(f"  ⚠️ {table:<30} Ошибка: {str(e)}")

        self.stdout.write("\n✅ Мониторинг завершен")