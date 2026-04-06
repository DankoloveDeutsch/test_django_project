from django.contrib import admin
from .models import (
    ModuleRecord, EmployeeProfile, WorkSchedule, AttendanceLog,
    MonthlyReport, DocumentTemplate, GeneratedDocument, EmployeeDocument,
    Reminder, AccountingIntegration, GovernmentReport, AuditLog
)

# Регистрация ВСЕХ моделей (каждый класс только один раз)
admin.site.register(ModuleRecord)
admin.site.register(EmployeeProfile)
admin.site.register(WorkSchedule)
admin.site.register(AttendanceLog)
admin.site.register(MonthlyReport)
admin.site.register(DocumentTemplate)
admin.site.register(GeneratedDocument)
admin.site.register(EmployeeDocument)
admin.site.register(Reminder)
admin.site.register(AccountingIntegration)
admin.site.register(GovernmentReport)
admin.site.register(AuditLog)