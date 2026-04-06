# module_app/api/__init__.py
"""
API модуль для системы управления табельным учетом
"""

from .views import *
from .urls import urlpatterns

__all__ = ['urlpatterns']