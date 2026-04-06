# module_app/tests/test_serializers.py
"""
Тесты для сериализаторов
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from ..models import EmployeeProfile
from ..serializers import EmployeeProfileSerializer, UserSerializer


class UserSerializerTest(TestCase):
    """Тесты для UserSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Тест',
            last_name='Пользователь',
            email='test@example.com'
        )

    def test_serializer_fields(self):
        """Тест полей сериализатора"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data

        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Тест')
        self.assertEqual(data['last_name'], 'Пользователь')
        self.assertEqual(data['full_name'], 'Тест Пользователь')

    def test_full_name_without_names(self):
        """Тест полного имени без имени и фамилии"""
        user = User.objects.create_user(username='onlyusername', password='testpass123')
        serializer = UserSerializer(instance=user)
        self.assertEqual(serializer.data['full_name'], 'onlyusername')


class EmployeeProfileSerializerTest(TestCase):
    """Тесты для EmployeeProfileSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Тест',
            last_name='Пользователь'
        )
        self.profile = EmployeeProfile.objects.create(
            user=self.user,
            position='Разработчик',
            department='IT',
            phone='+7 (999) 123-45-67'
        )

    def test_serializer_fields(self):
        """Тест полей сериализатора"""
        serializer = EmployeeProfileSerializer(instance=self.profile)
        data = serializer.data

        self.assertEqual(data['position'], 'Разработчик')
        self.assertEqual(data['department'], 'IT')
        self.assertEqual(data['phone'], '+7 (999) 123-45-67')
        self.assertEqual(data['full_name'], 'Тест Пользователь')

    def test_read_only_fields(self):
        """Тест полей только для чтения"""
        serializer = EmployeeProfileSerializer(instance=self.profile)
        data = serializer.data

        # Проверяем, что employee_code существует (может быть None)
        self.assertIn('employee_code', data)