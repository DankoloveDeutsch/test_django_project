# module_app/api/urls.py
"""
API маршруты
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet, basename='api-employees')
router.register(r'attendance', views.AttendanceViewSet, basename='api-attendance')
router.register(r'documents', views.DocumentViewSet, basename='api-documents')
router.register(r'document-templates', views.DocumentTemplateViewSet, basename='api-document-templates')
router.register(r'employee-documents', views.EmployeeDocumentViewSet, basename='api-employee-documents')
router.register(r'reminders', views.ReminderViewSet, basename='api-reminders')
router.register(r'reports', views.ReportViewSet, basename='api-reports')
router.register(r'accounting', views.AccountingViewSet, basename='api-accounting')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]