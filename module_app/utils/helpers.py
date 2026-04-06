# module_app/utils/helpers.py
"""
Вспомогательные функции
"""

import re
from datetime import date, datetime
from django.utils import timezone


def format_date(date_obj, format_str='%d.%m.%Y'):
    """Форматирование даты"""
    if not date_obj:
        return ''
    return date_obj.strftime(format_str)


def format_datetime(dt, format_str='%d.%m.%Y %H:%M'):
    """Форматирование даты и времени"""
    if not dt:
        return ''
    return dt.strftime(format_str)


def calculate_age(birth_date):
    """Расчет возраста"""
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def calculate_experience(hire_date, dismissal_date=None):
    """Расчет стажа работы"""
    if not hire_date:
        return None

    end_date = dismissal_date or date.today()
    delta = end_date - hire_date

    years = delta.days // 365
    months = (delta.days % 365) // 30
    days = (delta.days % 365) % 30

    return {'years': years, 'months': months, 'days': days}


def validate_snils(snils):
    """Валидация СНИЛС"""
    if not snils:
        return True

    # Очистка от разделителей
    snils_clean = re.sub(r'[\s\-]', '', snils)

    # Проверка формата
    if not re.match(r'^\d{11}$', snils_clean):
        return False

    # Проверка контрольной суммы
    number = int(snils_clean[:9])
    checksum = int(snils_clean[9:])

    if number < 1000000:
        return checksum == number

    sum_digits = 0
    for i in range(9):
        sum_digits += int(snils_clean[i]) * (9 - i)

    if sum_digits < 100:
        return checksum == sum_digits
    elif sum_digits == 100:
        return checksum == 0
    else:
        calculated = sum_digits % 101
        if calculated == 100:
            calculated = 0
        return checksum == calculated


def validate_inn(inn):
    """Валидация ИНН"""
    if not inn:
        return True

    inn_clean = re.sub(r'\s', '', inn)

    # Проверка формата
    if not re.match(r'^\d{10}$|^\d{12}$', inn_clean):
        return False

    # Проверка контрольной суммы для 10-значного ИНН
    if len(inn_clean) == 10:
        coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        sum_digits = sum(int(inn_clean[i]) * coefficients[i] for i in range(9))
        control = sum_digits % 11
        if control > 9:
            control %= 10
        return control == int(inn_clean[9])

    # Проверка контрольной суммы для 12-значного ИНН
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

        return control1 == int(inn_clean[10]) and control2 == int(inn_clean[11])

    return False


def validate_phone(phone):
    """Валидация телефона"""
    if not phone:
        return True

    phone_clean = re.sub(r'[\s\-\(\)\+]', '', phone)
    return bool(re.match(r'^7\d{10}$|^8\d{10}$', phone_clean))


def format_phone(phone):
    """Форматирование телефона"""
    if not phone:
        return ''

    phone_clean = re.sub(r'[\s\-\(\)\+]', '', phone)
    if len(phone_clean) == 11 and phone_clean.startswith('7'):
        return f'+7 ({phone_clean[1:4]}) {phone_clean[4:7]}-{phone_clean[7:9]}-{phone_clean[9:11]}'
    if len(phone_clean) == 11 and phone_clean.startswith('8'):
        return f'+7 ({phone_clean[1:4]}) {phone_clean[4:7]}-{phone_clean[7:9]}-{phone_clean[9:11]}'

    return phone


def format_snils(snils):
    """Форматирование СНИЛС"""
    if not snils:
        return ''

    snils_clean = re.sub(r'[\s\-]', '', snils)
    if len(snils_clean) == 11:
        return f'{snils_clean[:3]}-{snils_clean[3:6]}-{snils_clean[6:9]} {snils_clean[9:11]}'

    return snils


def format_inn(inn):
    """Форматирование ИНН"""
    if not inn:
        return ''

    inn_clean = re.sub(r'\s', '', inn)
    return inn_clean


def truncate_text(text, length=100, suffix='...'):
    """Обрезка текста"""
    if not text:
        return ''
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + suffix


def bytes_to_human(size_bytes):
    """Преобразование байт в человекочитаемый формат"""
    if size_bytes == 0:
        return '0 B'

    size_names = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1

    return f'{size_bytes:.1f} {size_names[i]}'