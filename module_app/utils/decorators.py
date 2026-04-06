# module_app/utils/decorators.py
"""
Декораторы для проверки прав доступа
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def admin_required(view_func):
    """Декоратор: только для администраторов"""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('module_app:login')
        if not request.user.is_staff:
            messages.error(request, 'Доступ запрещен. Требуются права администратора.')
            return redirect('module_app:dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


def hr_manager_required(view_func):
    """Декоратор: только для HR-менеджеров"""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('module_app:login')
        if not request.user.has_perm('module_app.can_manage_employees') and not request.user.is_staff:
            messages.error(request, 'Доступ запрещен. Требуются права HR-менеджера.')
            return redirect('module_app:dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper


def login_required_ajax(view_func):
    """Декоратор: проверка авторизации для AJAX запросов"""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.http import JsonResponse
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        return view_func(request, *args, **kwargs)

    return wrapper


def log_activity(view_func):
    """Декоратор: логирование действий пользователя"""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from ..models import AuditLog

        response = view_func(request, *args, **kwargs)

        if request.user.is_authenticated and request.method != 'GET':
            AuditLog.objects.create(
                user=request.user,
                action=request.method.lower(),
                model_name=view_func.__name__,
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return response

    return wrapper