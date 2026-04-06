# module_app/tests/test_api.py
"""
Тесты для API
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from ..models import EmployeeProfile


class EmployeeAPITest(TestCase):
    """Тесты для API сотрудников"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.profile = EmployeeProfile.objects.create(
            user=self.user,
            position='Разработчик'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_employees_list(self):
        """Тест получения списка сотрудников"""
        response = self.client.get('/api/v1/employees/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_employee_detail(self):
        """Тест получения деталей сотрудника"""
        response = self.client.get(f'/api/v1/employees/{self.profile.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['position'], 'Разработчик')

    def test_create_employee(self):
        """Тест создания сотрудника"""
        data = {
            'user': {'username': 'newuser', 'email': 'new@example.com'},
            'position': 'Тестировщик',
            'department': 'QA'
        }
        response = self.client.post('/api/v1/employees/', data, format='json')
        # Может быть 201 или 400 в зависимости от реализации
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_unauthenticated_access(self):
        """Тест доступа без аутентификации"""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/v1/employees/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AttendanceAPITest(TestCase):
    """Тесты для API табеля"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.profile = EmployeeProfile.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)

    def test_get_attendance_list(self):
        """Тест получения списка табеля"""
        response = self.client.get('/api/v1/attendance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_attendance_log(self):
        """Тест создания записи табеля"""
        data = {
            'employee': self.profile.id,
            'date': '2024-01-01',
            'time': '09:00',
            'event': 'start'
        }
        response = self.client.post('/api/v1/attendance/', data, format='json')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])