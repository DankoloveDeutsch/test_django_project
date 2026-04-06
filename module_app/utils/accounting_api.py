# module_app/utils/accounting_api.py
"""
Интеграция с бухгалтерской системой 1С
"""

import json
import requests
import logging
from datetime import datetime
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def sync_to_1c(operation):
    """
    Синхронизация операции с 1С

    Args:
        operation: объект AccountingIntegration

    Returns:
        dict: результат синхронизации
    """
    api_url = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('API_URL')
    api_key = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('API_KEY')
    timeout = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('TIMEOUT', 30)

    if not api_url:
        return {'success': False, 'error': 'API_URL не настроен'}

    # Формирование данных для отправки
    payload = {
        'operation_id': operation.id,
        'operation_type': operation.operation_type,
        'operation_date': operation.operation_date.isoformat(),
        'employee': {
            'code': operation.employee.employee_code,
            'full_name': operation.employee.full_name,
            'position': operation.employee.position,
            'department': operation.employee.department,
            'hire_date': operation.employee.hire_date.isoformat() if operation.employee.hire_date else None,
            'dismissal_date': operation.employee.dismissal_date.isoformat() if operation.employee.dismissal_date else None,
            'salary': str(operation.employee.salary) if operation.employee.salary else None
        },
        'data': operation.data,
        'timestamp': datetime.now().isoformat()
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    try:
        response = requests.post(
            f"{api_url}/api/v1/sync",
            json=payload,
            headers=headers,
            timeout=timeout
        )

        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'external_id': result.get('external_id'),
                'message': result.get('message', 'Успешно')
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text}'
            }

    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Таймаут подключения к 1С'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Ошибка подключения к 1С'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_1c_connection_status():
    """
    Проверка статуса подключения к 1С

    Returns:
        dict: статус подключения
    """
    api_url = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('API_URL')

    if not api_url:
        return {
            'connected': False,
            'error': 'API_URL не настроен'
        }

    try:
        response = requests.get(f"{api_url}/api/v1/health", timeout=5)

        if response.status_code == 200:
            return {
                'connected': True,
                'message': 'Подключение успешно',
                'version': response.json().get('version', 'unknown')
            }
        else:
            return {
                'connected': False,
                'error': f'HTTP {response.status_code}'
            }

    except requests.exceptions.Timeout:
        return {'connected': False, 'error': 'Таймаут подключения'}
    except requests.exceptions.ConnectionError:
        return {'connected': False, 'error': 'Ошибка подключения'}
    except Exception as e:
        return {'connected': False, 'error': str(e)}


def send_employee_data(employee, action):
    """
    Отправка данных о сотруднике в 1С

    Args:
        employee: объект EmployeeProfile
        action: действие (create, update, delete)

    Returns:
        dict: результат отправки
    """
    api_url = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('API_URL')
    api_key = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('API_KEY')

    if not api_url:
        return {'success': False, 'error': 'API_URL не настроен'}

    payload = {
        'action': action,
        'employee': {
            'code': employee.employee_code,
            'full_name': employee.full_name,
            'first_name': employee.user.first_name,
            'last_name': employee.user.last_name,
            'position': employee.position,
            'department': employee.department,
            'phone': employee.phone,
            'email': employee.user.email,
            'hire_date': employee.hire_date.isoformat() if employee.hire_date else None,
            'dismissal_date': employee.dismissal_date.isoformat() if employee.dismissal_date else None,
            'salary': str(employee.salary) if employee.salary else None,
            'tax_id': employee.tax_id,
            'snils': employee.snils
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    try:
        response = requests.post(
            f"{api_url}/api/v1/employees",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code in [200, 201]:
            result = response.json()
            return {
                'success': True,
                'external_id': result.get('external_id')
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}'
            }

    except Exception as e:
        return {'success': False, 'error': str(e)}


def sync_attendance_data(employee, year, month):
    """
    Синхронизация данных табеля с 1С

    Args:
        employee: объект EmployeeProfile
        year: год
        month: месяц

    Returns:
        dict: результат синхронизации
    """
    from ..models import AttendanceLog

    logs = AttendanceLog.objects.filter(
        employee=employee,
        date__year=year,
        date__month=month
    ).order_by('date')

    total_hours = logs.aggregate(total=models.Sum('hours'))['total'] or 0

    api_url = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('API_URL')
    api_key = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('API_KEY')

    if not api_url:
        return {'success': False, 'error': 'API_URL не настроен'}

    payload = {
        'employee_code': employee.employee_code,
        'year': year,
        'month': month,
        'total_hours': total_hours,
        'days': logs.values('date').distinct().count(),
        'logs': [
            {
                'date': log.date.isoformat(),
                'start_time': log.time.isoformat() if log.event == 'start' else None,
                'end_time': log.time.isoformat() if log.event == 'end' else None,
                'hours': log.hours
            }
            for log in logs
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    try:
        response = requests.post(
            f"{api_url}/api/v1/attendance",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return {'success': True}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def sync_salary_data(employee, month, year, salary):
    """
    Синхронизация данных о зарплате с 1С

    Args:
        employee: объект EmployeeProfile
        month: месяц
        year: год
        salary: сумма зарплаты

    Returns:
        dict: результат синхронизации
    """
    api_url = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('API_URL')
    api_key = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('API_KEY')

    if not api_url:
        return {'success': False, 'error': 'API_URL не настроен'}

    payload = {
        'employee_code': employee.employee_code,
        'period': f"{month:02d}.{year}",
        'salary': str(salary),
        'tax_id': employee.tax_id,
        'snils': employee.snils
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    try:
        response = requests.post(
            f"{api_url}/api/v1/salary",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return {'success': True}
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}

    except Exception as e:
        return {'success': False, 'error': str(e)}