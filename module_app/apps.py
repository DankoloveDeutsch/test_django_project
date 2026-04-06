# module_app/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ModuleAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'module_app'
    verbose_name = _('Управление табельным учетом')

    def ready(self):
        # Импортируем сигналы
        try:
            import module_app.signals
        except Exception as e:
            print(f"Warning: Could not import signals - {e}")

        # Регистрируем проверки
        try:
            from django.core import checks
            from . import validators
            checks.register(validators.check_environment)
        except Exception as e:
            print(f"Warning: Could not register checks - {e}")

        print(f"✅ Приложение '{self.verbose_name}' загружено")