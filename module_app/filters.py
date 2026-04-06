# module_app/filters.py
import django_filters
from django.db.models import Q
from .models import EmployeeProfile, AttendanceLog, EmployeeDocument, Reminder


class EmployeeFilter(django_filters.FilterSet):
    """Фильтр для сотрудников"""
    search = django_filters.CharFilter(method='filter_search', label='Поиск')
    department = django_filters.CharFilter(lookup_expr='icontains')
    position = django_filters.CharFilter(lookup_expr='icontains')
    hire_date_from = django_filters.DateFilter(field_name='hire_date', lookup_expr='gte')
    hire_date_to = django_filters.DateFilter(field_name='hire_date', lookup_expr='lte')
    age_min = django_filters.NumberFilter(field_name='age', lookup_expr='gte', method='filter_age')
    age_max = django_filters.NumberFilter(field_name='age', lookup_expr='lte', method='filter_age')
    salary_min = django_filters.NumberFilter(field_name='salary', lookup_expr='gte')
    salary_max = django_filters.NumberFilter(field_name='salary', lookup_expr='lte')
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = EmployeeProfile
        fields = ['department', 'position', 'employment_type', 'is_active']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value) |
            Q(position__icontains=value) |
            Q(department__icontains=value) |
            Q(phone__icontains=value) |
            Q(employee_code__icontains=value)
        )

    def filter_age(self, queryset, name, value):
        # Фильтрация по возрасту требует дополнительной логики
        from datetime import date
        today = date.today()
        if name == 'age_min':
            year = today.year - value
            return queryset.filter(birth_date__lte=date(year, today.month, today.day))
        elif name == 'age_max':
            year = today.year - value - 1
            return queryset.filter(birth_date__gte=date(year, today.month, today.day))
        return queryset


class AttendanceFilter(django_filters.FilterSet):
    """Фильтр для записей табеля"""
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    employee = django_filters.ModelChoiceFilter(queryset=EmployeeProfile.objects.all())
    event = django_filters.ChoiceFilter(choices=AttendanceLog.EVENT_TYPES)

    class Meta:
        model = AttendanceLog
        fields = ['employee', 'date', 'event']


class EmployeeDocumentFilter(django_filters.FilterSet):
    """Фильтр для документов сотрудников"""
    search = django_filters.CharFilter(method='filter_search', label='Поиск')
    employee = django_filters.ModelChoiceFilter(queryset=EmployeeProfile.objects.all())
    document_type = django_filters.ChoiceFilter(choices=EmployeeDocument.DOCUMENT_TYPES)
    is_expiring = django_filters.BooleanFilter(method='filter_expiring', label='Истекающие')
    is_expired = django_filters.BooleanFilter(method='filter_expired', label='Просроченные')
    upload_date_from = django_filters.DateFilter(field_name='upload_date', lookup_expr='gte')
    upload_date_to = django_filters.DateFilter(field_name='upload_date', lookup_expr='lte')
    expiry_date_from = django_filters.DateFilter(field_name='expiry_date', lookup_expr='gte')
    expiry_date_to = django_filters.DateFilter(field_name='expiry_date', lookup_expr='lte')

    class Meta:
        model = EmployeeDocument
        fields = ['employee', 'document_type', 'is_active']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value)
        )

    def filter_expiring(self, queryset, name, value):
        if value:
            from django.utils import timezone
            today = timezone.now().date()
            thirty_days = today + timezone.timedelta(days=30)
            return queryset.filter(expiry_date__gte=today, expiry_date__lte=thirty_days, is_active=True)
        return queryset

    def filter_expired(self, queryset, name, value):
        if value:
            from django.utils import timezone
            today = timezone.now().date()
            return queryset.filter(expiry_date__lt=today, is_active=True)
        return queryset


class ReminderFilter(django_filters.FilterSet):
    """Фильтр для напоминаний"""
    employee = django_filters.ModelChoiceFilter(queryset=EmployeeProfile.objects.all())
    reminder_type = django_filters.ChoiceFilter(choices=Reminder.REMINDER_TYPES)
    priority = django_filters.ChoiceFilter(choices=Reminder.PRIORITY)
    is_completed = django_filters.BooleanFilter()
    due_date_from = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_date_to = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')

    class Meta:
        model = Reminder
        fields = ['employee', 'reminder_type', 'priority', 'is_completed', 'is_sent']