# module_app/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

from .models import (
    EmployeeProfile, WorkSchedule, AttendanceLog,
    DocumentTemplate, GeneratedDocument, EmployeeDocument,
    Reminder, AccountingIntegration, GovernmentReport
)


# ============ ФОРМЫ АУТЕНТИФИКАЦИИ ============
class UserRegistrationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=True, label="Имя")
    last_name = forms.CharField(max_length=30, required=True, label="Фамилия")

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


# ============ ФОРМЫ ДЛЯ СОТРУДНИКОВ ============
class EmployeeProfileForm(forms.ModelForm):
    """Форма профиля сотрудника"""

    class Meta:
        model = EmployeeProfile
        fields = [
            'user', 'position', 'department', 'phone', 'address',
            'birth_date', 'hire_date', 'dismissal_date', 'employment_type',
            'salary', 'bank_account', 'tax_id', 'snils', 'profile_picture', 'is_active'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'dismissal_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_snils(self):
        """Валидация СНИЛС"""
        snils = self.cleaned_data.get('snils', '')
        if snils:
            snils_clean = re.sub(r'[\s\-]', '', snils)
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

            return f"{snils_clean[:3]}-{snils_clean[3:6]}-{snils_clean[6:9]} {snils_clean[9:]}"
        return snils

    def clean_tax_id(self):
        """Валидация ИНН"""
        inn = self.cleaned_data.get('tax_id', '')
        if inn:
            inn_clean = re.sub(r'\s', '', inn)
            if not re.match(r'^\d{10}$|^\d{12}$', inn_clean):
                raise ValidationError('ИНН должен содержать 10 или 12 цифр')
            return inn_clean
        return inn

    def clean_phone(self):
        """Валидация телефона"""
        phone = self.cleaned_data.get('phone', '')
        if phone:
            phone_clean = re.sub(r'[\s\-\(\)\+]', '', phone)
            if not re.match(r'^7\d{10}$|^8\d{10}$', phone_clean):
                raise ValidationError('Введите номер в формате: +7XXXXXXXXXX')
            return f"+7{phone_clean[-10:]}"
        return phone

    def clean(self):
        cleaned_data = super().clean()
        hire_date = cleaned_data.get('hire_date')
        dismissal_date = cleaned_data.get('dismissal_date')
        is_active = cleaned_data.get('is_active')

        if hire_date and dismissal_date and dismissal_date < hire_date:
            raise ValidationError('Дата увольнения не может быть раньше даты приема')

        if is_active and dismissal_date:
            raise ValidationError('У активного сотрудника не может быть даты увольнения')

        if not is_active and not dismissal_date:
            self.add_error('dismissal_date', 'Укажите дату увольнения')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


class WorkScheduleForm(forms.ModelForm):
    """Форма графика работы"""

    class Meta:
        model = WorkSchedule
        fields = ['employee', 'day', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise ValidationError('Время начала не может быть позже или равно времени окончания')

        return cleaned_data


class AttendanceLogForm(forms.ModelForm):
    """Форма для отметки рабочего времени"""

    class Meta:
        model = AttendanceLog
        fields = ['employee', 'date', 'time', 'event', 'hours']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get('employee')
        date = cleaned_data.get('date')

        if employee and date:
            if date > timezone.now().date():
                raise ValidationError('Дата не может быть в будущем')

            if not employee.is_active:
                raise ValidationError('Сотрудник уволен')

        return cleaned_data


# ============ ФОРМЫ ДЛЯ ДОКУМЕНТОВ ============
class DocumentTemplateForm(forms.ModelForm):
    """Форма шаблона документа"""

    class Meta:
        model = DocumentTemplate
        fields = ['name', 'template_type', 'content', 'variables', 'is_active']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 20, 'class': 'font-monospace'}),
            'variables': forms.Textarea(attrs={'rows': 5, 'placeholder': '{"full_name": "ФИО сотрудника"}'}),
        }

    def clean_variables(self):
        """Проверка переменных шаблона"""
        variables = self.cleaned_data.get('variables', {})
        content = self.cleaned_data.get('content', '')

        # Проверяем, что все переменные используются в шаблоне
        for var_name in variables.keys():
            if f'{{{{ {var_name} }}}}' not in content:
                pass  # Можно добавить предупреждение

        return variables


class GeneratedDocumentForm(forms.ModelForm):
    """Форма сгенерированного документа"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['template'].queryset = DocumentTemplate.objects.filter(is_active=True)

    class Meta:
        model = GeneratedDocument
        fields = ['employee', 'template', 'document_type', 'content', 'status', 'notes']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 15}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class EmployeeDocumentForm(forms.ModelForm):
    """Форма документа сотрудника"""

    class Meta:
        model = EmployeeDocument
        fields = ['employee', 'document_type', 'title', 'file', 'expiry_date', 'description', 'is_active']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_file(self):
        """Валидация загружаемого файла"""
        file = self.cleaned_data.get('file')
        if file:
            # Проверка размера файла (макс 10 МБ)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('Размер файла не должен превышать 10 МБ')

            # Проверка расширения
            ext = file.name.split('.')[-1].lower()
            allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx']
            if ext not in allowed_extensions:
                raise ValidationError(f'Недопустимый формат файла. Разрешены: {", ".join(allowed_extensions)}')
        return file

    def clean(self):
        cleaned_data = super().clean()
        expiry_date = cleaned_data.get('expiry_date')
        upload_date = cleaned_data.get('upload_date')

        if expiry_date and upload_date and expiry_date <= upload_date:
            raise ValidationError('Дата истечения срока должна быть позже даты загрузки')

        return cleaned_data


# ============ ФОРМЫ ДЛЯ НАПОМИНАНИЙ ============
class ReminderForm(forms.ModelForm):
    """Форма напоминания"""

    class Meta:
        model = Reminder
        fields = [
            'employee', 'reminder_type', 'title', 'description',
            'due_date', 'reminder_days_before', 'priority',
            'related_document', 'related_generated_doc'
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now().date():
            raise ValidationError('Дата напоминания не может быть в прошлом')
        return due_date


# ============ ФОРМЫ ДЛЯ ИНТЕГРАЦИИ ============
class AccountingIntegrationForm(forms.ModelForm):
    """Форма интеграции с бухгалтерией"""

    class Meta:
        model = AccountingIntegration
        fields = ['employee', 'operation_type', 'operation_date', 'data']
        widgets = {
            'operation_date': forms.DateInput(attrs={'type': 'date'}),
            'data': forms.Textarea(attrs={'rows': 5, 'placeholder': '{"key": "value"}'}),
        }


class GovernmentReportForm(forms.ModelForm):
    """Форма отчета для госорганов"""

    class Meta:
        model = GovernmentReport
        fields = ['report_type', 'report_period', 'report_file']
        widgets = {
            'report_period': forms.TextInput(attrs={'placeholder': '01.2025'}),
        }


# ============ ФОРМЫ ДЛЯ ПОИСКА И ФИЛЬТРАЦИИ ============
class EmployeeSearchForm(forms.Form):
    """Форма поиска сотрудников"""
    search = forms.CharField(required=False, label='Поиск',
                             widget=forms.TextInput(attrs={'placeholder': 'ФИО, должность, отдел, телефон'}))
    department = forms.ChoiceField(required=False, label='Отдел')
    position = forms.CharField(required=False, label='Должность')
    employment_type = forms.ChoiceField(required=False, label='Тип занятости',
                                        choices=[('', 'Все')] + EmployeeProfile.EMPLOYMENT_TYPES)
    is_active = forms.ChoiceField(required=False, label='Статус',
                                  choices=[('', 'Все'), ('true', 'Активные'), ('false', 'Уволенные')])
    hire_date_from = forms.DateField(required=False, label='Дата приема с',
                                     widget=forms.DateInput(attrs={'type': 'date'}))
    hire_date_to = forms.DateField(required=False, label='Дата приема по',
                                   widget=forms.DateInput(attrs={'type': 'date'}))
    salary_min = forms.DecimalField(required=False, label='Зарплата от', max_digits=10, decimal_places=2)
    salary_max = forms.DecimalField(required=False, label='Зарплата до', max_digits=10, decimal_places=2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Заполняем выбор отделов динамически
        departments = EmployeeProfile.objects.values_list('department', flat=True).distinct()
        self.fields['department'].choices = [('', 'Все')] + [(d, d) for d in departments if d]


class AttendanceFilterForm(forms.Form):
    """Форма фильтрации табеля"""
    employee = forms.ModelChoiceField(required=False, queryset=EmployeeProfile.objects.filter(is_active=True),
                                      label='Сотрудник')
    date_from = forms.DateField(required=False, label='Дата с',
                                widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, label='Дата по',
                              widget=forms.DateInput(attrs={'type': 'date'}))
    event = forms.ChoiceField(required=False, label='Тип события',
                              choices=[('', 'Все')] + AttendanceLog.EVENT_TYPES)


class DocumentFilterForm(forms.Form):
    """Форма фильтрации документов"""
    employee = forms.ModelChoiceField(required=False, queryset=EmployeeProfile.objects.all(),
                                      label='Сотрудник')
    document_type = forms.ChoiceField(required=False, label='Тип документа',
                                      choices=[('', 'Все')] + EmployeeDocument.DOCUMENT_TYPES)
    is_expiring = forms.BooleanField(required=False, label='Истекающие документы')
    is_expired = forms.BooleanField(required=False, label='Просроченные документы')
    upload_date_from = forms.DateField(required=False, label='Дата загрузки с',
                                       widget=forms.DateInput(attrs={'type': 'date'}))
    upload_date_to = forms.DateField(required=False, label='Дата загрузки по',
                                     widget=forms.DateInput(attrs={'type': 'date'}))


# ============ ВСПОМОГАТЕЛЬНЫЕ ФОРМЫ ============
class BulkEmployeeImportForm(forms.Form):
    """Форма массового импорта сотрудников"""
    file = forms.FileField(label='Excel файл',
                           help_text='Загрузите Excel файл с данными сотрудников')
    update_existing = forms.BooleanField(required=False, label='Обновлять существующих',
                                         help_text='Обновлять данные существующих сотрудников')


class ReportGenerationForm(forms.Form):
    """Форма генерации отчетов"""
    report_type = forms.ChoiceField(label='Тип отчета', choices=[
        ('monthly', 'Месячный отчет'),
        ('quarterly', 'Квартальный отчет'),
        ('annual', 'Годовой отчет'),
        ('pension', 'Отчет в ПФР'),
        ('tax', 'Отчет в ФНС'),
        ('social', 'Отчет в ФСС'),
    ])
    period = forms.CharField(label='Период', help_text='Например: 01.2025 или 2025')
    format = forms.ChoiceField(label='Формат', choices=[
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ])
    departments = forms.MultipleChoiceField(required=False, label='Отделы',
                                            widget=forms.CheckboxSelectMultiple)