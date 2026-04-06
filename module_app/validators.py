# module_app/validators.py
import re
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_snils(value):
    """Валидация СНИЛС"""
    if value:
        snils_clean = re.sub(r'[\s\-]', '', value)
        if not re.match(r'^\d{11}$', snils_clean):
            raise ValidationError('СНИЛС должен содержать 11 цифр')

        # Проверка контрольной суммы
        number = int(snils_clean[:9])
        checksum = int(snils_clean[9:])

        if number < 1000000:
            if checksum != number:
                raise ValidationError('Неверная контрольная сумма СНИЛС')
        else:
            sum_digits = 0
            for i in range(9):
                sum_digits += int(snils_clean[i]) * (9 - i)

            if sum_digits < 100:
                if checksum != sum_digits:
                    raise ValidationError('Неверная контрольная сумма СНИЛС')
            elif sum_digits == 100:
                if checksum != 0:
                    raise ValidationError('Неверная контрольная сумма СНИЛС')
            else:
                calculated = sum_digits % 101
                if calculated == 100:
                    calculated = 0
                if checksum != calculated:
                    raise ValidationError('Неверная контрольная сумма СНИЛС')


def validate_inn(value):
    """Валидация ИНН"""
    if value:
        inn_clean = re.sub(r'\s', '', value)
        if not re.match(r'^\d{10}$|^\d{12}$', inn_clean):
            raise ValidationError('ИНН должен содержать 10 или 12 цифр')


def validate_phone(value):
    """Валидация телефона"""
    if value:
        phone_clean = re.sub(r'[\s\-\(\)\+]', '', value)
        if not re.match(r'^7\d{10}$|^8\d{10}$', phone_clean):
            raise ValidationError('Введите номер в формате: +7XXXXXXXXXX')


def validate_file_size(file, max_size_mb=10):
    """Валидация размера файла"""
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'Размер файла не должен превышать {max_size_mb} МБ')


def validate_file_extension(file, allowed_extensions):
    """Валидация расширения файла"""
    ext = file.name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f'Недопустимый формат файла. Разрешены: {", ".join(allowed_extensions)}')


def validate_future_date(date):
    """Валидация даты в будущем"""
    if date and date < timezone.now().date():
        raise ValidationError('Дата не может быть в прошлом')


def validate_past_date(date):
    """Валидация даты в прошлом"""
    if date and date > timezone.now().date():
        raise ValidationError('Дата не может быть в будущем')


def validate_employment_dates(hire_date, dismissal_date=None):
    """Валидация дат приема и увольнения"""
    if hire_date and dismissal_date and dismissal_date < hire_date:
        raise ValidationError('Дата увольнения не может быть раньше даты приема')


def check_environment(**kwargs):
    from django.conf import settings

    if settings.DEBUG:
        print("DEBUG mode")
    return []