# module_app/urls.py
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'module_app'

urlpatterns = [
    # ============ ГЛАВНЫЕ СТРАНИЦЫ ============
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('home/', views.home, name='home'),

    # ============ АУТЕНТИФИКАЦИЯ ============
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.user_register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', auth_views.PasswordChangeView.as_view(
        template_name='auth/password_change.html',
        success_url='/profile/'
    ), name='change_password'),

    # ============ СОТРУДНИКИ ============
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employees/create/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('employees/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('employees/<int:pk>/edit/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee_delete'),
    path('employees/<int:pk>/documents/', views.EmployeeDocumentsView.as_view(), name='employee_documents'),
    path('employees/<int:pk>/schedule/', views.EmployeeScheduleView.as_view(), name='employee_schedule'),
    path('employees/<int:pk>/attendance/', views.EmployeeAttendanceView.as_view(), name='employee_attendance'),
    path('employees/export/', views.export_employees, name='export_employees'),
    path('employees/import/', views.import_employees, name='import_employees'),
    path('employees/search/', views.employee_search, name='employee_search'),

    # ============ ТАБЕЛЬ УЧЕТА ============
    path('attendance/', views.AttendanceLogListView.as_view(), name='attendance_list'),
    path('attendance/log/', views.attendance_log, name='attendance_log'),
    path('attendance/today/', views.TodayAttendanceView.as_view(), name='attendance_today'),
    path('attendance/start/', views.attendance_start, name='attendance_start'),
    path('attendance/break/', views.attendance_break, name='attendance_break'),
    path('attendance/resume/', views.attendance_resume, name='attendance_resume'),
    path('attendance/end/', views.attendance_end, name='attendance_end'),
    path('attendance/monthly/', views.MonthlyReportView.as_view(), name='attendance_monthly'),
    path('attendance/calendar/', views.CalendarView.as_view(), name='attendance_calendar'),
    path('attendance/export/', views.export_attendance, name='export_attendance'),
    path('attendance/calendar/', views.TodayAttendanceView.as_view(), name='attendance_calendar'),

    # ============ ДОКУМЕНТЫ ============
    path('documents/', views.DocumentListView.as_view(), name='document_list'),
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('documents/<int:pk>/download/', views.download_document, name='document_download'),
    path('documents/<int:pk>/sign/', views.sign_document, name='document_sign'),
    path('documents/<int:pk>/send/', views.send_document, name='document_send'),
    path('documents/generate/', views.DocumentGenerateView.as_view(), name='document_generate'),
    path('documents/bulk/', views.bulk_document_generation, name='bulk_document_generation'),

    # Шаблоны документов
    path('documents/templates/', views.DocumentTemplateListView.as_view(), name='document_template_list'),
    path('documents/templates/create/', views.DocumentTemplateCreateView.as_view(), name='document_template_create'),
    path('documents/templates/<int:pk>/edit/', views.DocumentTemplateUpdateView.as_view(), name='document_template_edit'),
    path('documents/templates/<int:pk>/delete/', views.DocumentTemplateDeleteView.as_view(), name='document_template_delete'),

    # Личные документы сотрудников
    path('employee-documents/', views.EmployeeDocumentListView.as_view(), name='employee_document_list'),
    path('employee-documents/upload/', views.EmployeeDocumentUploadView.as_view(), name='employee_document_upload'),
    path('employee-documents/<int:pk>/', views.EmployeeDocumentDetailView.as_view(), name='employee_document_detail'),
    path('employee-documents/<int:pk>/edit/', views.EmployeeDocumentUpdateView.as_view(), name='employee_document_edit'),
    path('employee-documents/<int:pk>/delete/', views.EmployeeDocumentDeleteView.as_view(), name='employee_document_delete'),
    path('employee-documents/expiring/', views.ExpiringDocumentsView.as_view(), name='expiring_documents'),
    path('employees/<int:pk>/edit/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/test/', views.test_update, name='test_update'),

    # ============ НАПОМИНАНИЯ ============
    path('reminders/', views.ReminderListView.as_view(), name='reminder_list'),
    path('reminders/create/', views.ReminderCreateView.as_view(), name='reminder_create'),
    path('reminders/<int:pk>/', views.ReminderDetailView.as_view(), name='reminder_detail'),
    path('reminders/<int:pk>/complete/', views.reminder_complete, name='reminder_complete'),
    path('reminders/<int:pk>/delete/', views.ReminderDeleteView.as_view(), name='reminder_delete'),
    path('reminders/send/', views.send_reminders, name='send_reminders'),
    path('reminders/settings/', views.ReminderSettingsView.as_view(), name='reminder_settings'),

    # ============ ОТЧЕТЫ ============
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/monthly/', views.MonthlyReportView.as_view(), name='monthly_report'),
    path('reports/yearly/', views.YearlyReportView.as_view(), name='yearly_report'),
    path('reports/overtime/', views.OvertimeReportView.as_view(), name='overtime_report'),
    path('reports/department/', views.DepartmentReportView.as_view(), name='department_report'),
    path('reports/generate/', views.generate_report, name='generate_report'),
    path('reports/download/<int:pk>/', views.download_report, name='download_report'),

    # ============ ИНТЕГРАЦИЯ С БУХГАЛТЕРИЕЙ ============
    path('accounting/', views.AccountingIntegrationListView.as_view(), name='accounting_list'),
    path('accounting/sync/', views.sync_accounting, name='sync_accounting'),
    path('accounting/status/', views.accounting_status, name='accounting_status'),
    path('accounting/retry/<int:pk>/', views.retry_accounting, name='retry_accounting'),

    # ============ ОТЧЕТЫ ДЛЯ ГОСОРГАНОВ ============
    path('government-reports/', views.GovernmentReportListView.as_view(), name='government_report_list'),
    path('government-reports/create/', views.GovernmentReportCreateView.as_view(), name='government_report_create'),
    path('government-reports/<int:pk>/', views.GovernmentReportDetailView.as_view(), name='government_report_detail'),
    path('government-reports/<int:pk>/send/', views.send_government_report, name='send_government_report'),
    path('government-reports/generate/', views.generate_government_report, name='generate_government_report'),

    # ============ СТАТИСТИКА И АНАЛИТИКА ============
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
    path('statistics/employees/', views.EmployeeStatisticsView.as_view(), name='employee_statistics'),
    path('statistics/attendance/', views.AttendanceStatisticsView.as_view(), name='attendance_statistics'),
    path('statistics/documents/', views.DocumentStatisticsView.as_view(), name='document_statistics'),

    # ============ АУДИТ ============
    path('audit/', views.AuditLogListView.as_view(), name='audit_log'),
    path('audit/<int:pk>/', views.AuditLogDetailView.as_view(), name='audit_log_detail'),

    # ============ НАСТРОЙКИ ============
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('settings/general/', views.GeneralSettingsView.as_view(), name='general_settings'),
    path('settings/notifications/', views.NotificationSettingsView.as_view(), name='notification_settings'),
    path('settings/integrations/', views.IntegrationSettingsView.as_view(), name='integration_settings'),
    path('settings/backup/', views.BackupSettingsView.as_view(), name='backup_settings'),

    # Отчет по переработкам
    path('reports/overtime/', views.OvertimeReportView.as_view(), name='overtime_report'),

    # Отчет по отделам
    path('reports/department/', views.DepartmentReportView.as_view(), name='department_report')
]

# API маршруты
try:
    from .api import urls as api_urls
    urlpatterns += [
        path('api/v1/', include(api_urls)),
    ]
except ImportError:
    pass