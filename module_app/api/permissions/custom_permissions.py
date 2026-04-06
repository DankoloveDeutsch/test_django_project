# module_app/api/permissions/custom_permissions.py
"""
Кастомные права доступа для API
"""

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение: администратор или только чтение

    - Администратор может выполнять любые операции
    - Обычные пользователи могут только читать данные
    """

    def has_permission(self, request, view):
        # Разрешаем безопасные методы (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Для остальных методов проверяем права администратора
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        # Разрешаем безопасные методы
        if request.method in permissions.SAFE_METHODS:
            return True

        # Для остальных методов проверяем права администратора
        return request.user and request.user.is_staff


class IsHRManager(permissions.BasePermission):
    """
    Разрешение: только HR-менеджер

    HR-менеджер может управлять сотрудниками и их документами
    """

    def has_permission(self, request, view):
        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_manage_employees')
        )

    def has_object_permission(self, request, view, obj):
        # HR-менеджер может работать с любыми объектами сотрудников
        if hasattr(obj, 'employee'):
            obj_to_check = obj.employee
        else:
            obj_to_check = obj

        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_manage_employees')
        )


class IsDepartmentHead(permissions.BasePermission):
    """
    Разрешение: руководитель отдела

    Руководитель отдела может управлять сотрудниками своего отдела
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Определяем сотрудника
        if hasattr(obj, 'employee'):
            employee = obj.employee
        elif hasattr(obj, 'department'):
            employee = obj
        else:
            return False

        # Проверяем, что пользователь является руководителем отдела
        return (
                request.user.is_staff or
                (hasattr(request.user, 'employeeprofile') and
                 request.user.employeeprofile.department == employee.department and
                 request.user.has_perm('module_app.can_manage_department'))
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение: владелец или только чтение

    Пользователь может редактировать только свои данные
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Разрешаем безопасные методы
        if request.method in permissions.SAFE_METHODS:
            return True

        # Проверяем владельца
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'employee') and hasattr(obj.employee, 'user'):
            return obj.employee.user == request.user

        return False


class CanSignDocuments(permissions.BasePermission):
    """
    Разрешение: может подписывать документы

    Пользователи с этим правом могут подписывать документы
    """

    def has_permission(self, request, view):
        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_sign_documents')
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class CanGenerateReports(permissions.BasePermission):
    """
    Разрешение: может генерировать отчеты

    Пользователи с этим правом могут создавать и экспортировать отчеты
    """

    def has_permission(self, request, view):
        # Генерация отчетов доступна для GET и POST методов
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_generate_reports')
        )


class CanManageEmployees(permissions.BasePermission):
    """
    Разрешение: может управлять сотрудниками

    Пользователи с этим правом могут создавать, редактировать и удалять сотрудников
    """

    def has_permission(self, request, view):
        # GET запросы доступны всем
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_manage_employees')
        )


class CanViewAuditLog(permissions.BasePermission):
    """
    Разрешение: может просматривать журнал аудита

    Только администраторы и специально назначенные пользователи
    """

    def has_permission(self, request, view):
        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_view_audit_log')
        )


class CanSyncAccounting(permissions.BasePermission):
    """
    Разрешение: может синхронизировать с бухгалтерией

    Только администраторы и пользователи с правом на интеграцию
    """

    def has_permission(self, request, view):
        # GET запросы (просмотр статуса) доступны администраторам
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_staff

        # POST/PUT запросы требуют специального права
        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_sync_accounting')
        )


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Разрешение: аутентифицированный пользователь или только чтение

    Комбинированное разрешение для публичных данных
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsAdminUser(permissions.BasePermission):
    """
    Разрешение: только администратор

    Упрощенная версия для проверки прав администратора
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class CanEditOwnProfile(permissions.BasePermission):
    """
    Разрешение: может редактировать свой профиль

    Пользователь может редактировать только свой профиль
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Проверяем, что объект принадлежит пользователю
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif isinstance(obj, EmployeeProfile):
            return obj.user == request.user

        return False


class CanManageDocuments(permissions.BasePermission):
    """
    Разрешение: может управлять документами

    Пользователи с этим правом могут создавать, редактировать и удалять документы
    """

    def has_permission(self, request, view):
        # GET запросы доступны всем
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_manage_documents')
        )


class CanManageReminders(permissions.BasePermission):
    """
    Разрешение: может управлять напоминаниями

    Пользователи с этим правом могут создавать и редактировать напоминания
    """

    def has_permission(self, request, view):
        # GET запросы доступны всем
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_manage_reminders')
        )

    def has_object_permission(self, request, view, obj):
        # Владелец напоминания может управлять им
        if hasattr(obj, 'employee') and hasattr(obj.employee, 'user'):
            if obj.employee.user == request.user:
                return True

        return self.has_permission(request, view)


class CanViewStatistics(permissions.BasePermission):
    """
    Разрешение: может просматривать статистику

    Только руководители и администраторы
    """

    def has_permission(self, request, view):
        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_view_statistics')
        )


class CanExportData(permissions.BasePermission):
    """
    Разрешение: может экспортировать данные

    Только пользователи с правом на экспорт
    """

    def has_permission(self, request, view):
        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_export_data')
        )


class CanImportData(permissions.BasePermission):
    """
    Разрешение: может импортировать данные

    Только пользователи с правом на импорт (обычно администраторы)
    """

    def has_permission(self, request, view):
        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_import_data')
        )


class CanManageSystemSettings(permissions.BasePermission):
    """
    Разрешение: может управлять настройками системы

    Только суперпользователи и администраторы
    """

    def has_permission(self, request, view):
        return request.user and (
                request.user.is_superuser or
                request.user.is_staff and request.user.has_perm('module_app.can_manage_settings')
        )


class CanManageBackups(permissions.BasePermission):
    """
    Разрешение: может управлять резервным копированием

    Только администраторы
    """

    def has_permission(self, request, view):
        return request.user and (
                request.user.is_staff and
                request.user.has_perm('module_app.can_manage_backups')
        )


# ============ КОМБИНИРОВАННЫЕ РАЗРЕШЕНИЯ ============

class IsAdminOrManager(permissions.BasePermission):
    """
    Разрешение: администратор или менеджер

    Комбинация прав администратора и HR-менеджера
    """

    def has_permission(self, request, view):
        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_manage_employees')
        )


class IsAdminOrDepartmentHead(permissions.BasePermission):
    """
    Разрешение: администратор или руководитель отдела

    Комбинация прав администратора и руководителя отдела
    """

    def has_permission(self, request, view):
        return request.user and (
                request.user.is_staff or
                request.user.has_perm('module_app.can_manage_department')
        )


class IsAdminOrOwner(permissions.BasePermission):
    """
    Разрешение: администратор или владелец

    Администратор может всё, владелец может управлять своими данными
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        # Проверка владельца
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'employee') and hasattr(obj.employee, 'user'):
            return obj.employee.user == request.user

        return False


class IsAdminOrReadOnlyForOthers(permissions.BasePermission):
    """
    Разрешение: администратор для записи, остальные только чтение

    Администратор может изменять чужие данные, остальные только свои
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff:
            return True

        # Не-администраторы могут изменять только свои данные
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'employee') and hasattr(obj.employee, 'user'):
            return obj.employee.user == request.user

        return False


# ============ ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ ============

class AllowAny(permissions.BasePermission):
    """
    Разрешение для всех (публичный доступ)
    """

    def has_permission(self, request, view):
        return True


class IsAuthenticated(permissions.BasePermission):
    """
    Разрешение только для аутентифицированных пользователей
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated