# module_app/permissions.py
from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение: администратор или только чтение"""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsHRManager(permissions.BasePermission):
    """Разрешение: только HR-менеджер"""

    def has_permission(self, request, view):
        return request.user and request.user.has_perm('module_app.can_manage_employees')


class IsDepartmentHead(permissions.BasePermission):
    """Разрешение: руководитель отдела"""

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'employee'):
            employee = obj.employee
        elif hasattr(obj, 'department'):
            employee = obj
        else:
            return False

        return (request.user == employee.user or
                request.user.has_perm('module_app.can_manage_department'))


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Разрешение: владелец или только чтение"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'employee'):
            return obj.employee.user == request.user
        return False


class CanSignDocuments(permissions.BasePermission):
    """Разрешение: может подписывать документы"""

    def has_permission(self, request, view):
        return request.user and request.user.has_perm('module_app.can_sign_documents')