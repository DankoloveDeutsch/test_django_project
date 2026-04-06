# module_app/context_processors.py
from django.conf import settings
from .models import Reminder, EmployeeProfile


def notifications_count(request):
    """Количество непрочитанных уведомлений"""
    if request.user.is_authenticated:
        try:
            profile = request.user.employeeprofile
            count = Reminder.objects.filter(
                employee=profile,
                is_sent=False,
                is_completed=False
            ).count()
            return {'notifications_count': count}
        except EmployeeProfile.DoesNotExist:
            return {'notifications_count': 0}
    return {'notifications_count': 0}


def company_info(request):
    """Информация о компании"""
    return {
        'company_name': getattr(settings, 'COMPANY_NAME', 'ООО "Ромашка"'),
        'company_logo': getattr(settings, 'COMPANY_LOGO', '/static/images/logo.png'),
        'company_site': getattr(settings, 'COMPANY_SITE', 'https://company.ru'),
        'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@company.ru'),
        'support_phone': getattr(settings, 'SUPPORT_PHONE', '+7 (999) 123-45-67'),
    }


def user_permissions(request):
    """Права пользователя для шаблонов"""
    if request.user.is_authenticated:
        return {
            'is_admin': request.user.is_staff,
            'is_hr': request.user.has_perm('module_app.can_manage_employees'),
            'can_edit': request.user.has_perm('module_app.can_edit_documents'),
        }
    return {}


def current_year(request):
    """Текущий год для шаблонов"""
    from django.utils import timezone
    return {'current_year': timezone.now().year}