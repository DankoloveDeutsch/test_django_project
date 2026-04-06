# module_app/utils/validators.py
"""
Валидаторы для моделей и форм
"""

import re
from datetime import date, datetime
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def validate_snils(value):
    """
    Валидация СНИЛС

    Формат: XXX-XXX-XXX XX или 11 цифр
    Алгоритм проверки контрольной суммы
    """
    if not value:
        return

    # Очистка от разделителей
    snils_clean = re.sub(r'[\s\-]', '', str(value))

    # Проверка длины
    if not re.match(r'^\d{11}$', snils_clean):
        raise ValidationError(
            _('СНИЛС должен содержать 11 цифр'),
            code='invalid_snils_length'
        )

    # Проверка контрольной суммы
    number = int(snils_clean[:9])
    checksum = int(snils_clean[9:])

    if number < 1000000:
        if checksum != number:
            raise ValidationError(
                _('Неверная контрольная сумма СНИЛС'),
                code='invalid_snils_checksum'
            )
    else:
        sum_digits = 0
        for i in range(9):
            sum_digits += int(snils_clean[i]) * (9 - i)

        if sum_digits < 100:
            if checksum != sum_digits:
                raise ValidationError(
                    _('Неверная контрольная сумма СНИЛС'),
                    code='invalid_snils_checksum'
                )
        elif sum_digits == 100:
            if checksum != 0:
                raise ValidationError(
                    _('Неверная контрольная сумма СНИЛС'),
                    code='invalid_snils_checksum'
                )
        else:
            calculated = sum_digits % 101
            if calculated == 100:
                calculated = 0
            if checksum != calculated:
                raise ValidationError(
                    _('Неверная контрольная сумма СНИЛС'),
                    code='invalid_snils_checksum'
                )


def validate_inn(value):
    """
    Валидация ИНН

    Поддерживает 10-значные (юр. лица) и 12-значные (физ. лица)
    """
    if not value:
        return

    # Очистка
    inn_clean = re.sub(r'\s', '', str(value))

    # Проверка длины
    if not re.match(r'^\d{10}$|^\d{12}$', inn_clean):
        raise ValidationError(
            _('ИНН должен содержать 10 или 12 цифр'),
            code='invalid_inn_length'
        )

    # Проверка для 10-значного ИНН
    if len(inn_clean) == 10:
        coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        sum_digits = sum(int(inn_clean[i]) * coefficients[i] for i in range(9))
        control = sum_digits % 11
        if control > 9:
            control %= 10
        if control != int(inn_clean[9]):
            raise ValidationError(
                _('Неверная контрольная сумма ИНН'),
                code='invalid_inn_checksum'
            )

    # Проверка для 12-значного ИНН
    if len(inn_clean) == 12:
        coefficients1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        coefficients2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]

        sum1 = sum(int(inn_clean[i]) * coefficients1[i] for i in range(10))
        control1 = sum1 % 11
        if control1 > 9:
            control1 %= 10

        sum2 = sum(int(inn_clean[i]) * coefficients2[i] for i in range(11))
        control2 = sum2 % 11
        if control2 > 9:
            control2 %= 10

        if control1 != int(inn_clean[10]) or control2 != int(inn_clean[11]):
            raise ValidationError(
                _('Неверная контрольная сумма ИНН'),
                code='invalid_inn_checksum'
            )


def validate_phone(value):
    """
    Валидация номера телефона

    Форматы:
    - +7XXXXXXXXXX
    - 8XXXXXXXXXX
    - 7XXXXXXXXXX
    """
    if not value:
        return

    phone_clean = re.sub(r'[\s\-\(\)\+]', '', str(value))

    if not re.match(r'^7\d{10}$|^8\d{10}$', phone_clean):
        raise ValidationError(
            _('Введите номер в формате +7XXXXXXXXXX (10 цифр после кода)'),
            code='invalid_phone'
        )

    # Возвращаем в стандартном формате
    if phone_clean.startswith('8'):
        phone_clean = '7' + phone_clean[1:]


def validate_passport(value):
    """
    Валидация паспортных данных
    Формат: серия (4 цифры) + номер (6 цифр)
    """
    if not value:
        return

    passport_clean = re.sub(r'[\s\-]', '', str(value))

    if not re.match(r'^\d{10}$', passport_clean):
        raise ValidationError(
            _('Паспорт должен содержать 10 цифр: 4 цифры серии и 6 цифр номера'),
            code='invalid_passport'
        )

    series = passport_clean[:4]
    number = passport_clean[4:]

    # Проверка, что серия не нулевая
    if series == '0000':
        raise ValidationError(
            _('Неверная серия паспорта'),
            code='invalid_passport_series'
        )

    # Проверка, что номер не нулевой
    if number == '000000':
        raise ValidationError(
            _('Неверный номер паспорта'),
            code='invalid_passport_number'
        )


def validate_email(value):
    """
    Валидация email адреса
    """
    if not value:
        return

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, value):
        raise ValidationError(
            _('Введите корректный email адрес'),
            code='invalid_email'
        )


def validate_birth_date(value):
    """
    Валидация даты рождения
    - Не в будущем
    - Не менее 14 лет (для трудоустройства)
    - Не более 100 лет
    """
    if not value:
        return

    today = date.today()

    if value > today:
        raise ValidationError(
            _('Дата рождения не может быть в будущем'),
            code='birth_date_future'
        )

    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

    if age < 14:
        raise ValidationError(
            _('Возраст должен быть не менее 14 лет'),
            code='birth_date_too_young'
        )

    if age > 100:
        raise ValidationError(
            _('Возраст не может превышать 100 лет'),
            code='birth_date_too_old'
        )


def validate_hire_date(value):
    """
    Валидация даты приема
    - Не в будущем
    - Не ранее 14 лет от рождения
    """
    if not value:
        return

    today = date.today()

    if value > today:
        raise ValidationError(
            _('Дата приема не может быть в будущем'),
            code='hire_date_future'
        )


def validate_dismissal_date(hire_date, dismissal_date):
    """
    Валидация даты увольнения
    - Не ранее даты приема
    - Не в будущем
    """
    if not dismissal_date:
        return

    today = date.today()

    if dismissal_date > today:
        raise ValidationError(
            _('Дата увольнения не может быть в будущем'),
            code='dismissal_date_future'
        )

    if hire_date and dismissal_date < hire_date:
        raise ValidationError(
            _('Дата увольнения не может быть раньше даты приема'),
            code='dismissal_before_hire'
        )


def validate_salary(value):
    """
    Валидация зарплаты
    - Положительное число
    - Не превышает максимальное значение
    """
    if value is None:
        return

    if value <= 0:
        raise ValidationError(
            _('Зарплата должна быть положительным числом'),
            code='salary_negative'
        )

    if value > 10000000:
        raise ValidationError(
            _('Зарплата не может превышать 10 000 000 руб.'),
            code='salary_too_high'
        )


def validate_file_size(file, max_size_mb=10):
    """
    Валидация размера файла

    Args:
        file: загруженный файл
        max_size_mb: максимальный размер в МБ
    """
    if not file:
        return

    max_size_bytes = max_size_mb * 1024 * 1024
    if file.size > max_size_bytes:
        raise ValidationError(
            _(f'Размер файла не должен превышать {max_size_mb} МБ'),
            code='file_too_large'
        )


def validate_file_extension(file, allowed_extensions=None):
    """
    Валидация расширения файла

    Args:
        file: загруженный файл
        allowed_extensions: список разрешенных расширений
    """
    if not file:
        return

    if allowed_extensions is None:
        allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'xls', 'xlsx']

    ext = file.name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            _(f'Недопустимый формат файла. Разрешены: {", ".join(allowed_extensions)}'),
            code='invalid_file_extension'
        )


def validate_document_expiry(expiry_date, upload_date=None):
    """
    Валидация даты истечения документа
    - Не в прошлом (если документ активен)
    - Не ранее даты загрузки
    """
    if not expiry_date:
        return

    today = date.today()

    if expiry_date < today:
        raise ValidationError(
            _('Срок действия документа истек'),
            code='document_expired'
        )

    if upload_date and expiry_date <= upload_date:
        raise ValidationError(
            _('Дата истечения должна быть позже даты загрузки'),
            code='expiry_before_upload'
        )


def validate_work_time(start_time, end_time):
    """
    Валидация рабочего времени
    - Начало раньше окончания
    - Не более 12 часов в день
    """
    if not start_time or not end_time:
        return

    if start_time >= end_time:
        raise ValidationError(
            _('Время начала должно быть раньше времени окончания'),
            code='invalid_work_time'
        )

    # Расчет продолжительности
    start_dt = datetime.combine(date.today(), start_time)
    end_dt = datetime.combine(date.today(), end_time)
    hours = (end_dt - start_dt).total_seconds() / 3600

    if hours > 12:
        raise ValidationError(
            _('Рабочий день не может превышать 12 часов'),
            code='work_day_too_long'
        )


def validate_reminder_due_date(due_date):
    """
    Валидация даты напоминания
    - Не в прошлом
    """
    if not due_date:
        return

    today = date.today()

    if due_date < today:
        raise ValidationError(
            _('Дата напоминания не может быть в прошлом'),
            code='reminder_past_date'
        )


def validate_overtime_hours(overtime_hours, month_norm=160):
    """
    Валидация переработок
    - Не более 120 часов в месяц (по ТК РФ)
    """
    if overtime_hours < 0:
        raise ValidationError(
            _('Переработка не может быть отрицательной'),
            code='negative_overtime'
        )

    if overtime_hours > 120:
        raise ValidationError(
            _('Переработка не может превышать 120 часов в месяц'),
            code='overtime_exceeded'
        )


def validate_unique_employee_code(code, exclude_id=None):
    """
    Валидация уникальности табельного номера

    Args:
        code: табельный номер
        exclude_id: ID сотрудника для исключения (при редактировании)
    """
    if not code:
        return

    from ..models import EmployeeProfile

    queryset = EmployeeProfile.objects.filter(employee_code=code)
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)

    if queryset.exists():
        raise ValidationError(
            _(f'Табельный номер "{code}" уже используется'),
            code='duplicate_employee_code'
        )


def validate_employee_email(email, exclude_user_id=None):
    """
    Валидация уникальности email сотрудника

    Args:
        email: email пользователя
        exclude_user_id: ID пользователя для исключения
    """
    if not email:
        return

    from django.contrib.auth.models import User

    queryset = User.objects.filter(email=email)
    if exclude_user_id:
        queryset = queryset.exclude(id=exclude_user_id)

    if queryset.exists():
        raise ValidationError(
            _(f'Email "{email}" уже используется'),
            code='duplicate_email'
        )


def validate_document_number(document_number, exclude_id=None):
    """
    Валидация уникальности номера документа

    Args:
        document_number: номер документа
        exclude_id: ID документа для исключения
    """
    if not document_number:
        return

    from ..models import GeneratedDocument

    queryset = GeneratedDocument.objects.filter(document_number=document_number)
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)

    if queryset.exists():
        raise ValidationError(
            _(f'Документ с номером "{document_number}" уже существует'),
            code='duplicate_document_number'
        )


def validate_attendance_log(employee, date, event):
    """
    Валидация записи табеля

    Args:
        employee: сотрудник
        date: дата
        event: событие
    """
    from ..models import AttendanceLog

    today = date.today()

    if date > today:
        raise ValidationError(
            _('Дата не может быть в будущем'),
            code='attendance_future_date'
        )

    if not employee.is_active:
        raise ValidationError(
            _('Сотрудник уволен'),
            code='attendance_inactive_employee'
        )

    # Проверка последовательности событий
    last_log = AttendanceLog.objects.filter(
        employee=employee,
        date=date
    ).order_by('-time').first()

    if event == 'start' and last_log:
        raise ValidationError(
            _('Рабочий день уже начат'),
            code='attendance_already_started'
        )

    if event == 'break' and (not last_log or last_log.event not in ['start', 'resume']):
        raise ValidationError(
            _('Нельзя начать перерыв, не начав рабочий день'),
            code='attendance_break_invalid'
        )

    if event == 'resume' and (not last_log or last_log.event != 'break'):
        raise ValidationError(
            _('Нельзя продолжить работу, не начав перерыв'),
            code='attendance_resume_invalid'
        )

    if event == 'end' and (not last_log or last_log.event not in ['start', 'resume']):
        raise ValidationError(
            _('Нельзя завершить рабочий день, не начав его'),
            code='attendance_end_invalid'
        )