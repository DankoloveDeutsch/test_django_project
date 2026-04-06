# module_app/exceptions.py
from rest_framework.exceptions import APIException
from rest_framework import status


class EmployeeNotFound(APIException):
    """Сотрудник не найден"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Сотрудник не найден'
    default_code = 'employee_not_found'


class DocumentGenerationError(APIException):
    """Ошибка генерации документа"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Ошибка при генерации документа'
    default_code = 'document_generation_error'


class AccountingIntegrationError(APIException):
    """Ошибка интеграции с бухгалтерией"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Ошибка при интеграции с бухгалтерской системой'
    default_code = 'accounting_integration_error'


class ReminderAlreadySent(APIException):
    """Напоминание уже отправлено"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Напоминание уже было отправлено'
    default_code = 'reminder_already_sent'


class InvalidFileFormat(APIException):
    """Неверный формат файла"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Неверный формат файла'
    default_code = 'invalid_file_format'