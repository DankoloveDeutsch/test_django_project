# module_app/tests/test_utils.py
"""
Тесты для утилит
"""

from django.test import TestCase
from datetime import date
from ..utils.helpers import (
    format_date, calculate_age, validate_snils, validate_inn,
    format_phone, truncate_text, bytes_to_human
)
from ..utils.validators import (
    validate_snils as validator_snils,
    validate_inn as validator_inn,
    validate_phone as validator_phone
)
from django.core.exceptions import ValidationError


class HelpersTest(TestCase):
    """Тесты для вспомогательных функций"""

    def test_format_date(self):
        """Тест форматирования даты"""
        test_date = date(2024, 1, 15)
        self.assertEqual(format_date(test_date), '15.01.2024')
        self.assertEqual(format_date(None), '')

    def test_calculate_age(self):
        """Тест расчета возраста"""
        test_date = date(1990, 1, 1)
        age = calculate_age(test_date)
        self.assertIsNotNone(age)
        self.assertGreaterEqual(age, 34)
        self.assertLessEqual(age, 35)
        self.assertIsNone(calculate_age(None))

    def test_validate_snils(self):
        """Тест валидации СНИЛС"""
        # Валидный СНИЛС (пример)
        self.assertTrue(validate_snils('123-456-789 00'))
        # Невалидный СНИЛС
        self.assertFalse(validate_snils('123-456-789 01'))
        self.assertFalse(validate_snils('12345'))
        self.assertTrue(validate_snils(''))  # Пустое значение

    def test_validate_inn(self):
        """Тест валидации ИНН"""
        # Валидный ИНН (пример)
        self.assertTrue(validate_inn('123456789012'))
        self.assertTrue(validate_inn('1234567890'))
        self.assertTrue(validate_inn(''))
        self.assertFalse(validate_inn('12345'))

    def test_format_phone(self):
        """Тест форматирования телефона"""
        self.assertEqual(format_phone('+7 (999) 123-45-67'), '+7 (999) 123-45-67')
        self.assertEqual(format_phone('79991234567'), '+7 (999) 123-45-67')
        self.assertEqual(format_phone(''), '')

    def test_truncate_text(self):
        """Тест обрезки текста"""
        text = 'Это очень длинный текст, который должен быть обрезан до определенной длины'
        truncated = truncate_text(text, 20)
        self.assertLessEqual(len(truncated), 23)  # 20 + '...'
        self.assertTrue(truncated.endswith('...'))
        self.assertEqual(truncate_text('Короткий', 20), 'Короткий')

    def test_bytes_to_human(self):
        """Тест преобразования байт"""
        self.assertEqual(bytes_to_human(0), '0 B')
        self.assertEqual(bytes_to_human(1024), '1.0 KB')
        self.assertEqual(bytes_to_human(1048576), '1.0 MB')


class ValidatorsTest(TestCase):
    """Тесты для валидаторов"""

    def test_validate_snils_validator(self):
        """Тест валидатора СНИЛС"""
        # Проверяем, что валидатор не выбрасывает исключение для валидного значения
        try:
            validator_snils('123-456-789 00')
        except ValidationError:
            self.fail("Validator raised ValidationError unexpectedly!")

        # Проверяем, что валидатор выбрасывает исключение для невалидного
        with self.assertRaises(ValidationError):
            validator_snils('123-456-789 01')

    def test_validate_inn_validator(self):
        """Тест валидатора ИНН"""
        try:
            validator_inn('123456789012')
        except ValidationError:
            self.fail("Validator raised ValidationError unexpectedly!")

        with self.assertRaises(ValidationError):
            validator_inn('12345')

    def test_validate_phone_validator(self):
        """Тест валидатора телефона"""
        try:
            validator_phone('+7 (999) 123-45-67')
        except ValidationError:
            self.fail("Validator raised ValidationError unexpectedly!")

        with self.assertRaises(ValidationError):
            validator_phone('12345')