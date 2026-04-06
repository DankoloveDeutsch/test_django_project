"""
Инициализация проекта "Система управления табельным учетом специалиста"

Этот файл делает директорию module_app_project Python-пакетом.
Здесь также настраивается Celery для фоновых задач.
"""

from __future__ import absolute_import, unicode_literals

# Импорт Celery для автоматического обнаружения задач
from .celery import app as celery_app

__all__ = ('celery_app',)

# Версия проекта
__version__ = '1.0.0'
__author__ = 'HR System Team'
__license__ = 'Proprietary'