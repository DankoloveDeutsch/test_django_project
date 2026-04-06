# module_app/services/accounting_service.py
"""
Сервис для интеграции с бухгалтерской системой (1С)
"""

import json
import requests
from datetime import datetime
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from ..models import AccountingIntegration, EmployeeProfile


class AccountingService:
    """Сервис для интеграции с бухгалтерской системой"""

    @staticmethod
    @transaction.atomic
    def create_operation(employee_id, operation_type, operation_date, data):
        """
        Создание операции для отправки в бухгалтерию

        Args:
            employee_id: ID сотрудника
            operation_type: тип операции (hire/dismissal/vacation/etc)
            operation_date: дата операции
            data: дополнительные данные в формате JSON

        Returns:
            AccountingIntegration: созданная операция
        """
        employee = EmployeeProfile.objects.get(id=employee_id)

        # Добавляем стандартные данные
        standard_data = {
            'employee_code': employee.employee_code,
            'full_name': employee.full_name,
            'position': employee.position,
            'department': employee.department,
            'salary': str(employee.salary) if employee.salary else None
        }
        standard_data.update(data)

        return AccountingIntegration.objects.create(
            employee=employee,
            operation_type=operation_type,
            operation_date=operation_date,
            data=standard_data,
            status='pending'
        )

    @staticmethod
    def sync_pending_operations():
        """
        Синхронизация ожидающих операций с бухгалтерской системой

        Returns:
            dict: результаты синхронизации
        """
        operations = AccountingIntegration.objects.filter(status='pending')

        results = {
            'total': operations.count(),
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for operation in operations:
            try:
                success = AccountingService._send_to_1c(operation)
                if success:
                    operation.status = 'sent'
                    operation.processed_at = timezone.now()
                    operation.save()
                    results['success'] += 1
                else:
                    operation.status = 'error'
                    operation.error_message = 'Ошибка отправки в 1С'
                    operation.save()
                    results['failed'] += 1
                    results['errors'].append({
                        'id': operation.id,
                        'employee': operation.employee.full_name,
                        'type': operation.get_operation_type_display(),
                        'error': operation.error_message
                    })
            except Exception as e:
                operation.status = 'error'
                operation.error_message = str(e)
                operation.save()
                results['failed'] += 1
                results['errors'].append({
                    'id': operation.id,
                    'employee': operation.employee.full_name,
                    'type': operation.get_operation_type_display(),
                    'error': str(e)
                })

        return results

    @staticmethod
    def _send_to_1c(operation):
        """
        Отправка операции в 1С (внутренний метод)

        Args:
            operation: объект AccountingIntegration

        Returns:
            bool: успешность отправки
        """
        # Настройки интеграции из settings
        api_url = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('API_URL')
        api_key = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('API_KEY')

        if not api_url:
            raise ValueError('API_URL для 1С не настроен')

        # Формирование данных для отправки
        payload = {
            'operation_type': operation.operation_type,
            'operation_date': operation.operation_date.isoformat(),
            'employee': operation.data,
            'timestamp': datetime.now().isoformat()
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        try:
            response = requests.post(
                f"{api_url}/sync",
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                operation.external_id = result.get('external_id')
                return True
            else:
                raise Exception(f'HTTP {response.status_code}: {response.text}')

        except requests.exceptions.Timeout:
            raise Exception('Таймаут подключения к 1С')
        except requests.exceptions.ConnectionError:
            raise Exception('Ошибка подключения к 1С')
        except Exception as e:
            raise Exception(f'Ошибка отправки: {str(e)}')

    @staticmethod
    def get_connection_status():
        """
        Проверка статуса подключения к 1С

        Returns:
            dict: статус подключения
        """
        api_url = getattr(settings, 'ACCOUNTING_INTEGRATION', {}).get('API_URL')

        if not api_url:
            return {'connected': False, 'error': 'API_URL не настроен'}

        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                return {'connected': True, 'message': 'Подключение успешно'}
            else:
                return {'connected': False, 'error': f'HTTP {response.status_code}'}
        except requests.exceptions.Timeout:
            return {'connected': False, 'error': 'Таймаут подключения'}
        except requests.exceptions.ConnectionError:
            return {'connected': False, 'error': 'Ошибка подключения'}
        except Exception as e:
            return {'connected': False, 'error': str(e)}

    @staticmethod
    def retry_failed_operations():
        """
        Повторная отправка ошибочных операций

        Returns:
            dict: результаты повторной отправки
        """
        operations = AccountingIntegration.objects.filter(status='error')

        results = {
            'total': operations.count(),
            'success': 0,
            'failed': 0
        }

        for operation in operations:
            try:
                success = AccountingService._send_to_1c(operation)
                if success:
                    operation.status = 'sent'
                    operation.error_message = ''
                    operation.processed_at = timezone.now()
                    operation.save()
                    results['success'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                operation.error_message = str(e)
                operation.save()
                results['failed'] += 1

        return results

    @staticmethod
    def get_operation_statistics():
        """Получение статистики по операциям"""
        return {
            'total': AccountingIntegration.objects.count(),
            'pending': AccountingIntegration.objects.filter(status='pending').count(),
            'sent': AccountingIntegration.objects.filter(status='sent').count(),
            'processed': AccountingIntegration.objects.filter(status='processed').count(),
            'error': AccountingIntegration.objects.filter(status='error').count(),
            'by_type': {
                op_type: AccountingIntegration.objects.filter(operation_type=op_type).count()
                for op_type, _ in AccountingIntegration.OPERATION_TYPES
            }
        }

    @staticmethod
    def send_hire_data(employee_id):
        """
        Отправка данных о приеме сотрудника

        Args:
            employee_id: ID сотрудника
        """
        employee = EmployeeProfile.objects.get(id=employee_id)

        data = {
            'hire_date': employee.hire_date.isoformat() if employee.hire_date else None,
            'employment_type': employee.employment_type,
            'probation_period': 3 if employee.employment_type == 'probation' else None
        }

        return AccountingService.create_operation(
            employee_id=employee_id,
            operation_type='hire',
            operation_date=employee.hire_date or timezone.now().date(),
            data=data
        )

    @staticmethod
    def send_dismissal_data(employee_id, reason):
        """
        Отправка данных об увольнении сотрудника

        Args:
            employee_id: ID сотрудника
            reason: причина увольнения
        """
        employee = EmployeeProfile.objects.get(id=employee_id)

        data = {
            'dismissal_date': employee.dismissal_date.isoformat() if employee.dismissal_date else None,
            'reason': reason
        }

        return AccountingService.create_operation(
            employee_id=employee_id,
            operation_type='dismissal',
            operation_date=employee.dismissal_date or timezone.now().date(),
            data=data
        )

    @staticmethod
    def send_vacation_data(employee_id, start_date, end_date):
        """
        Отправка данных об отпуске сотрудника

        Args:
            employee_id: ID сотрудника
            start_date: дата начала отпуска
            end_date: дата окончания отпуска
        """
        data = {
            'vacation_start': start_date.isoformat(),
            'vacation_end': end_date.isoformat(),
            'vacation_days': (end_date - start_date).days + 1
        }

        return AccountingService.create_operation(
            employee_id=employee_id,
            operation_type='vacation',
            operation_date=start_date,
            data=data
        )

    @staticmethod
    def send_salary_change(employee_id, new_salary, effective_date):
        """
        Отправка данных об изменении зарплаты

        Args:
            employee_id: ID сотрудника
            new_salary: новая зарплата
            effective_date: дата начала действия
        """
        employee = EmployeeProfile.objects.get(id=employee_id)

        data = {
            'old_salary': str(employee.salary) if employee.salary else None,
            'new_salary': str(new_salary),
            'effective_date': effective_date.isoformat()
        }

        # Обновляем зарплату в системе
        employee.salary = new_salary
        employee.save()

        return AccountingService.create_operation(
            employee_id=employee_id,
            operation_type='salary_change',
            operation_date=effective_date,
            data=data
        )