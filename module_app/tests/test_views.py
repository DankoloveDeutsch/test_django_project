# module_app/tests/test_views.py
"""
Тесты для представлений
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from ..models import EmployeeProfile


class AuthViewsTest(TestCase):
    """Тесты для представлений аутентификации"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_login_page(self):
        """Тест страницы входа"""
        response = self.client.get(reverse('module_app:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'module_app/auth/login.html')

    def test_login_success(self):
        """Тест успешного входа"""
        response = self.client.post(reverse('module_app:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('module_app:dashboard'))

    def test_login_failed(self):
        """Тест неудачного входа"""
        response = self.client.post(reverse('module_app:login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверное имя пользователя или пароль')

    def test_logout(self):
        """Тест выхода из системы"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('module_app:logout'))
        self.assertRedirects(response, reverse('module_app:login'))

    def test_register_page(self):
        """Тест страницы регистрации"""
        response = self.client.get(reverse('module_app:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'module_app/auth/register.html')

    def test_register_success(self):
        """Тест успешной регистрации"""
        response = self.client.post(reverse('module_app:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'Новый',
            'last_name': 'Пользователь',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        self.assertRedirects(response, reverse('module_app:profile'))
        self.assertTrue(User.objects.filter(username='newuser').exists())


class EmployeeViewsTest(TestCase):
    """Тесты для представлений сотрудников"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        self.profile = EmployeeProfile.objects.create(
            user=self.user,
            position='Разработчик'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_employee_list(self):
        """Тест списка сотрудников"""
        response = self.client.get(reverse('module_app:employee_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'module_app/employees/list.html')

    def test_employee_detail(self):
        """Тест детальной карточки сотрудника"""
        response = self.client.get(reverse('module_app:employee_detail', args=[self.profile.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'module_app/employees/detail.html')

    def test_employee_create(self):
        """Тест создания сотрудника"""
        response = self.client.get(reverse('module_app:employee_create'))
        self.assertEqual(response.status_code, 200)

        # Создание нового пользователя для сотрудника
        new_user = User.objects.create_user(
            username='newemployee',
            password='testpass123',
            first_name='Новый',
            last_name='Сотрудник'
        )

        response = self.client.post(reverse('module_app:employee_create'), {
            'user': new_user.id,
            'position': 'Тестировщик',
            'department': 'QA',
            'hire_date': '2024-01-01'
        })
        self.assertRedirects(response, reverse('module_app:employee_list'))


class DashboardViewTest(TestCase):
    """Тесты для дашборда"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_dashboard_authenticated(self):
        """Тест дашборда для авторизованного пользователя"""
        response = self.client.get(reverse('module_app:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'module_app/dashboard.html')

    def test_dashboard_unauthenticated(self):
        """Тест дашборда для неавторизованного пользователя"""
        self.client.logout()
        response = self.client.get(reverse('module_app:dashboard'))
        self.assertRedirects(response, f"{reverse('module_app:login')}?next={reverse('module_app:dashboard')}")