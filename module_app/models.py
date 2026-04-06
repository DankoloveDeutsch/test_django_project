# module_app/models.py
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
import os


# ============ МОДЕЛЬ MODULE RECORD ============
class ModuleRecord(models.Model):
    """Финансовые записи модуля"""
    company_name = models.CharField(max_length=255, verbose_name="Название компании")
    date = models.DateField(verbose_name="Дата")
    revenue = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Выручка")
    expenses = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Расходы")
    profit = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name="Прибыль")

    class Meta:
        verbose_name = "Финансовая запись"
        verbose_name_plural = "Финансовые записи"
        ordering = ['-date']

    def save(self, *args, **kwargs):
        self.profit = self.revenue - self.expenses
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company_name} ({self.date})"


# ============ МОДЕЛЬ ПРОФИЛЯ СОТРУДНИКА ============
class EmployeeProfile(models.Model):
    """Личное дело сотрудника"""

    EMPLOYMENT_TYPES = [
        ('full_time', 'Полная занятость'),
        ('part_time', 'Частичная занятость'),
        ('contract', 'Договор подряда'),
        ('probation', 'Испытательный срок'),
    ]

    # Основная информация
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь",
                                related_name='employeeprofile')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg',
                                        verbose_name="Фото")
    position = models.CharField(max_length=100, blank=True, verbose_name="Должность")
    department = models.CharField(max_length=100, blank=True, verbose_name="Отдел")

    # Личные данные
    employee_code = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Табельный номер")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    work_phone = models.CharField(max_length=20, blank=True, verbose_name="Рабочий телефон")
    address = models.TextField(blank=True, verbose_name="Адрес")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    hire_date = models.DateField(null=True, blank=True, verbose_name="Дата приема")
    dismissal_date = models.DateField(null=True, blank=True, verbose_name="Дата увольнения")
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='full_time',
                                       verbose_name="Тип занятости")

    # Финансовая информация
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Оклад")
    bank_account = models.CharField(max_length=50, blank=True, verbose_name="Банковский счет")
    tax_id = models.CharField(max_length=20, blank=True, verbose_name="ИНН")
    snils = models.CharField(max_length=20, blank=True, verbose_name="СНИЛС")

    # Дополнительные контакты
    personal_email = models.EmailField(blank=True, verbose_name="Личный email")
    telegram = models.CharField(max_length=50, blank=True, verbose_name="Telegram")

    # Статус
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Профиль сотрудника"
        verbose_name_plural = "Профили сотрудников"
        ordering = ['-hire_date']
        indexes = [
            models.Index(fields=['employee_code'], name='idx_emp_code'),
            models.Index(fields=['snils'], name='idx_emp_snils'),
            models.Index(fields=['tax_id'], name='idx_emp_tax_id'),
            models.Index(fields=['is_active'], name='idx_emp_active'),
        ]

    def save(self, *args, **kwargs):
        if not self.employee_code and self.hire_date:
            year = self.hire_date.year
            count = EmployeeProfile.objects.filter(hire_date__year=year).count() + 1
            self.employee_code = f"{year}{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.position or 'Сотрудник'}"

    @property
    def full_name(self):
        """Полное имя сотрудника"""
        return self.user.get_full_name() or self.user.username

    @property
    def total_hours(self):
        """Общее количество часов за все время"""
        return round(self.attendance_logs.aggregate(models.Sum('hours'))['hours__sum'] or 0, 2)

    @property
    def age(self):
        """Возраст сотрудника"""
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                        (today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None


# ============ МОДЕЛЬ ГРАФИКА РАБОТЫ ============
class WorkSchedule(models.Model):
    """График работы сотрудника"""

    DAY_CHOICES = [
        ('mon', 'Понедельник'), ('tue', 'Вторник'), ('wed', 'Среда'),
        ('thu', 'Четверг'), ('fri', 'Пятница'), ('sat', 'Суббота'), ('sun', 'Воскресенье')
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='schedules',
                                 verbose_name="Сотрудник")
    day = models.CharField(max_length=3, choices=DAY_CHOICES, verbose_name="День недели")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")

    class Meta:
        verbose_name = "График работы"
        verbose_name_plural = "Графики работы"
        unique_together = ['employee', 'day']
        ordering = ['employee', 'day']

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_day_display()}"


# ============ МОДЕЛЬ ТАБЕЛЯ УЧЕТА ============
class AttendanceLog(models.Model):
    """Журнал учета рабочего времени"""

    EVENT_TYPES = [
        ('start', 'Начало работы'),
        ('break', 'Перерыв'),
        ('resume', 'Продолжение работы'),
        ('end', 'Окончание работы'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='attendance_logs',
                                 verbose_name="Сотрудник")
    date = models.DateField(verbose_name="Дата")
    time = models.TimeField(verbose_name="Время")
    event = models.CharField(max_length=10, choices=EVENT_TYPES, verbose_name="Событие")
    hours = models.FloatField(default=0, verbose_name="Часы")

    class Meta:
        verbose_name = "Запись табеля"
        verbose_name_plural = "Записи табеля"
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['date'], name='idx_att_date'),
            models.Index(fields=['employee', 'date'], name='idx_att_emp_date'),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} - {self.get_event_display()}"


# ============ МОДЕЛЬ МЕСЯЧНОГО ОТЧЕТА ============
class MonthlyReport(models.Model):
    """Сводный отчет за месяц"""

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='monthly_reports',
                                 verbose_name="Сотрудник")
    month = models.CharField(max_length=20, verbose_name="Месяц")
    total_hours = models.FloatField(default=0, verbose_name="Всего часов")
    overtime_hours = models.FloatField(default=0, verbose_name="Сверхурочные часы")

    class Meta:
        verbose_name = "Месячный отчет"
        verbose_name_plural = "Месячные отчеты"
        unique_together = ['employee', 'month']
        ordering = ['employee', '-month']

    def __str__(self):
        return f"{self.employee.full_name} - {self.month}"


# ============ МОДЕЛЬ ШАБЛОНА ДОКУМЕНТА ============
class DocumentTemplate(models.Model):
    """Шаблоны документов"""

    TEMPLATE_TYPES = [
        ('employment_order', 'Приказ о приеме'),
        ('dismissal_order', 'Приказ об увольнении'),
        ('vacation_order', 'Приказ о отпуске'),
        ('transfer_order', 'Приказ о переводе'),
        ('employment_contract', 'Трудовой договор'),
        ('vacation_notice', 'Уведомление об отпуске'),
        ('warning_notice', 'Предупреждение'),
        ('certificate', 'Справка'),
        ('other', 'Другое'),
    ]

    name = models.CharField(max_length=255, verbose_name="Название шаблона")
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES, verbose_name="Тип шаблона")
    content = models.TextField(verbose_name="Содержание шаблона")
    variables = models.JSONField(default=dict, help_text="Список переменных для подстановки", verbose_name="Переменные")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Шаблон документа"
        verbose_name_plural = "Шаблоны документов"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def render(self, context):
        """Подстановка переменных в шаблон"""
        rendered = self.content
        for key, value in context.items():
            rendered = rendered.replace(f'{{{{ {key} }}}}', str(value))
        return rendered


# ============ МОДЕЛЬ СГЕНЕРИРОВАННОГО ДОКУМЕНТА ============
class GeneratedDocument(models.Model):
    """Сформированные документы"""

    DOCUMENT_STATUS = [
        ('draft', 'Черновик'),
        ('generated', 'Сформирован'),
        ('signed', 'Подписан'),
        ('sent', 'Отправлен'),
        ('archived', 'Архивирован'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='generated_documents',
                                 verbose_name="Сотрудник")
    template = models.ForeignKey(DocumentTemplate, on_delete=models.SET_NULL, null=True, verbose_name="Шаблон")
    document_type = models.CharField(max_length=20, choices=DocumentTemplate.TEMPLATE_TYPES,
                                     verbose_name="Тип документа")
    document_number = models.CharField(max_length=50, unique=True, verbose_name="Номер документа")
    document_date = models.DateField(auto_now_add=True, verbose_name="Дата документа")
    content = models.TextField(verbose_name="Содержание")
    file = models.FileField(upload_to='generated_documents/%Y/%m/', blank=True, null=True, verbose_name="Файл")
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default='draft', verbose_name="Статус")
    signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='signed_documents', verbose_name="Подписан")
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата подписания")
    notes = models.TextField(blank=True, verbose_name="Примечания")

    class Meta:
        verbose_name = "Сгенерированный документ"
        verbose_name_plural = "Сгенерированные документы"
        ordering = ['-document_date']
        indexes = [
            models.Index(fields=['document_number'], name='idx_gen_doc_number'),
            models.Index(fields=['status'], name='idx_gen_doc_status'),
        ]

    def __str__(self):
        return f"{self.get_document_type_display()} №{self.document_number} - {self.employee.full_name}"

    def save(self, *args, **kwargs):
        if not self.document_number:
            year = datetime.now().year
            count = GeneratedDocument.objects.filter(document_type=self.document_type,
                                                     document_date__year=year).count() + 1
            self.document_number = f"{self.document_type[:2].upper()}-{year}-{count:04d}"
        super().save(*args, **kwargs)


# ============ МОДЕЛЬ ЛИЧНОГО ДОКУМЕНТА СОТРУДНИКА ============
class EmployeeDocument(models.Model):
    """Личные документы сотрудника"""

    DOCUMENT_TYPES = [
        ('passport', 'Паспорт'),
        ('snils', 'СНИЛС'),
        ('inn', 'ИНН'),
        ('employment_history', 'Трудовая книжка'),
        ('education', 'Диплом об образовании'),
        ('contract', 'Трудовой договор'),
        ('medical', 'Медицинская книжка'),
        ('certificate', 'Сертификат/Удостоверение'),
        ('military', 'Военный билет'),
        ('photo', 'Фотография'),
        ('other', 'Другое'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='personal_documents',
                                 verbose_name="Сотрудник")
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, verbose_name="Тип документа")
    title = models.CharField(max_length=255, verbose_name="Название документа")
    file = models.FileField(upload_to='employee_documents/%Y/%m/', verbose_name="Файл документа")
    upload_date = models.DateField(auto_now_add=True, verbose_name="Дата загрузки")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Срок действия")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Документ сотрудника"
        verbose_name_plural = "Документы сотрудников"
        ordering = ['employee', 'document_type', '-upload_date']
        indexes = [
            models.Index(fields=['document_type'], name='idx_doc_type'),
            models.Index(fields=['expiry_date'], name='idx_doc_expiry'),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_document_type_display()}"

    @property
    def is_expired(self):
        """Проверка, истек ли срок документа"""
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    @property
    def days_until_expiry(self):
        """Дней до истечения срока"""
        if self.expiry_date:
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None


# ============ МОДЕЛЬ НАПОМИНАНИЯ ============
class Reminder(models.Model):
    """Система напоминаний"""

    REMINDER_TYPES = [
        ('medical', 'Медосмотр'),
        ('certification', 'Аттестация'),
        ('contract_end', 'Окончание договора'),
        ('vacation', 'Отпуск'),
        ('probation_end', 'Окончание испытательного срока'),
        ('document_expiry', 'Истечение срока документа'),
        ('birthday', 'День рождения'),
        ('custom', 'Другое'),
    ]

    PRIORITY = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='reminders',
                                 verbose_name="Сотрудник")
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES, verbose_name="Тип напоминания")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    description = models.TextField(blank=True, verbose_name="Описание")
    due_date = models.DateField(verbose_name="Дата исполнения")
    reminder_days_before = models.IntegerField(default=7, help_text="Напомнить за N дней",
                                               verbose_name="Напомнить за дней")
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium', verbose_name="Приоритет")
    is_sent = models.BooleanField(default=False, verbose_name="Уведомление отправлено")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата отправки")
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата выполнения")
    related_document = models.ForeignKey(EmployeeDocument, on_delete=models.SET_NULL, null=True, blank=True,
                                         verbose_name="Связанный документ")
    related_generated_doc = models.ForeignKey(GeneratedDocument, on_delete=models.SET_NULL, null=True, blank=True,
                                              verbose_name="Связанный сгенерированный документ")

    class Meta:
        verbose_name = "Напоминание"
        verbose_name_plural = "Напоминания"
        ordering = ['due_date', '-priority']
        indexes = [
            models.Index(fields=['due_date'], name='idx_rem_due_date'),
            models.Index(fields=['is_sent', 'is_completed'], name='idx_rem_status'),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.title} ({self.due_date})"

    def should_notify(self):
        """Проверка, нужно ли отправить напоминание"""
        if self.is_sent or self.is_completed:
            return False
        days_until = (self.due_date - timezone.now().date()).days
        return days_until <= self.reminder_days_before and days_until >= 0


# ============ МОДЕЛЬ ИНТЕГРАЦИИ С БУХГАЛТЕРИЕЙ ============
class AccountingIntegration(models.Model):
    """Интеграция с бухгалтерской системой"""

    OPERATION_TYPES = [
        ('hire', 'Прием на работу'),
        ('dismissal', 'Увольнение'),
        ('vacation', 'Отпуск'),
        ('sick_leave', 'Больничный'),
        ('salary_change', 'Изменение зарплаты'),
        ('transfer', 'Перевод'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Ожидает отправки'),
        ('sent', 'Отправлен'),
        ('processed', 'Обработан'),
        ('error', 'Ошибка'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='accounting_operations',
                                 verbose_name="Сотрудник")
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES, verbose_name="Тип операции")
    operation_date = models.DateField(verbose_name="Дата операции")
    data = models.JSONField(help_text="Данные для передачи в бухгалтерию", verbose_name="Данные")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    external_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Внешний ID")
    error_message = models.TextField(blank=True, verbose_name="Сообщение об ошибке")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата обработки")

    class Meta:
        verbose_name = "Операция интеграции"
        verbose_name_plural = "Операции интеграции"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='idx_acc_status'),
            models.Index(fields=['operation_date'], name='idx_acc_date'),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_operation_type_display()} - {self.operation_date}"


# ============ МОДЕЛЬ ОТЧЕТА ДЛЯ ГОСОРГАНОВ ============
class GovernmentReport(models.Model):
    """Отчетность для государственных органов"""

    REPORT_TYPES = [
        ('pension_fund', 'ПФР'),
        ('tax_service', 'ФНС'),
        ('social_fund', 'ФСС'),
        ('statistics', 'Росстат'),
        ('employment_center', 'ЦЗН'),
    ]

    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, verbose_name="Тип отчета")
    report_period = models.CharField(max_length=20, help_text="Например: 01.2025", verbose_name="Период")
    report_file = models.FileField(upload_to='government_reports/%Y/%m/', verbose_name="Файл отчета")
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата генерации")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата отправки")
    status = models.CharField(max_length=20, default='generated', verbose_name="Статус")
    data = models.JSONField(default=dict, verbose_name="Данные отчета")

    class Meta:
        verbose_name = "Отчет для госорганов"
        verbose_name_plural = "Отчеты для госорганов"
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['report_type', 'report_period'], name='idx_gov_report'),
        ]

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.report_period}"


# ============ МОДЕЛЬ ЖУРНАЛА АУДИТА ============
class AuditLog(models.Model):
    """Журнал действий пользователей"""

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Пользователь")
    action = models.CharField(max_length=255, verbose_name="Действие")
    model_name = models.CharField(max_length=100, verbose_name="Модель")
    object_id = models.CharField(max_length=100, blank=True, verbose_name="ID объекта")
    object_repr = models.CharField(max_length=255, blank=True, verbose_name="Представление объекта")
    changes = models.JSONField(default=dict, verbose_name="Изменения")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP адрес")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Запись аудита"
        verbose_name_plural = "Записи аудита"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['model_name'], name='idx_audit_model'),
            models.Index(fields=['created_at'], name='idx_audit_date'),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"