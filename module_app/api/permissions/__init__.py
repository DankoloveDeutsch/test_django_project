# module_app/api/permissions/__init__.py
"""
Права доступа для API
"""

from .custom_permissions import (
    IsAdminOrReadOnly,
    IsHRManager,
    IsDepartmentHead,
    IsOwnerOrReadOnly,
    CanSignDocuments,
    CanGenerateReports,
    CanManageEmployees,
    CanViewAuditLog,
    CanSyncAccounting
)

__all__ = [
    'IsAdminOrReadOnly',
    'IsHRManager',
    'IsDepartmentHead',
    'IsOwnerOrReadOnly',
    'CanSignDocuments',
    'CanGenerateReports',
    'CanManageEmployees',
    'CanViewAuditLog',
    'CanSyncAccounting'
]