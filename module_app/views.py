# module_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.db.models import Sum, Q, Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
import csv
import json
from datetime import datetime, timedelta

from .models import (
    ModuleRecord, EmployeeProfile, WorkSchedule, AttendanceLog,
    MonthlyReport, DocumentTemplate, GeneratedDocument, EmployeeDocument,
    Reminder, AccountingIntegration, GovernmentReport, AuditLog
)
from .forms import (
    UserRegistrationForm, EmployeeProfileForm, WorkScheduleForm,
    AttendanceLogForm, DocumentTemplateForm, GeneratedDocumentForm,
    EmployeeDocumentForm, ReminderForm
)
from .utils.notification import send_reminder_notification
from .utils.document_generator import generate_document_pdf
from .utils.excel_export import export_to_excel


# ============ АУТЕНТИФИКАЦИЯ ============

def user_login(request):
    """Вход в систему"""
    if request.user.is_authenticated:
        return redirect('module_app:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_full_name() or user.username}!')

            AuditLog.objects.create(
                user=user,
                action='login',
                model_name='User',
                object_repr=user.username,
                ip_address=request.META.get('REMOTE_ADDR')
            )

            next_url = request.GET.get('next', 'module_app:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')

    return render(request, 'module_app/auth/login.html')


def user_logout(request):
    """Выход из системы"""
    if request.user.is_authenticated:
        AuditLog.objects.create(
            user=request.user,
            action='logout',
            model_name='User',
            object_repr=request.user.username,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        logout(request)
        messages.info(request, 'Вы вышли из системы')

    return redirect('module_app:login')


def user_register(request):
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect('module_app:dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешно завершена!')
            return redirect('module_app:profile')
    else:
        form = UserRegistrationForm()

    return render(request, 'module_app/auth/register.html', {'form': form})


@login_required
def profile(request):
    """Профиль пользователя"""
    try:
        profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        profile = None

    context = {
        'profile': profile,
        'user': request.user
    }
    return render(request, 'module_app/auth/profile.html', context)


@login_required
def edit_profile(request):
    """Редактирование профиля"""
    try:
        profile = request.user.employeeprofile
    except EmployeeProfile.DoesNotExist:
        profile = EmployeeProfile(user=request.user)

    if request.method == 'POST':
        form = EmployeeProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('module_app:profile')
    else:
        form = EmployeeProfileForm(instance=profile)

    return render(request, 'module_app/auth/edit_profile.html', {'form': form})


# ============ ДАШБОРД ============

class DashboardView(LoginRequiredMixin, TemplateView):
    """Главная панель управления"""
    template_name = 'module_app/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_employees'] = EmployeeProfile.objects.count()
        context['active_employees'] = EmployeeProfile.objects.filter(is_active=True).count()
        context['active_reminders'] = Reminder.objects.filter(
            is_completed=False,
            due_date__gte=timezone.now().date()
        ).count()
        context['expired_documents'] = EmployeeDocument.objects.filter(
            expiry_date__lt=timezone.now().date(),
            is_active=True
        ).count()

        context['recent_reminders'] = Reminder.objects.filter(
            is_completed=False
        ).order_by('due_date')[:5]

        context['audit_logs'] = AuditLog.objects.all().order_by('-created_at')[:10]

        last_30_days = []
        hours_data = []
        for i in range(30, 0, -1):
            date = timezone.now().date() - timedelta(days=i)
            total_hours = AttendanceLog.objects.filter(date=date).aggregate(Sum('hours'))['hours__sum'] or 0
            last_30_days.append(date.strftime('%d.%m'))
            hours_data.append(total_hours)

        context['chart_labels'] = json.dumps(last_30_days)
        context['chart_data'] = json.dumps(hours_data)

        return context


def home(request):
    """Главная страница"""
    return redirect('module_app:dashboard')


# ============ СОТРУДНИКИ ============

class EmployeeListView(LoginRequiredMixin, ListView):
    """Список сотрудников"""
    model = EmployeeProfile
    template_name = 'module_app/employees/list.html'
    context_object_name = 'employees'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(position__icontains=search) |
                Q(department__icontains=search) |
                Q(employee_code__icontains=search) |
                Q(phone__icontains=search)
            )

        department = self.request.GET.get('department')
        if department:
            queryset = queryset.filter(department=department)

        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        hire_date_from = self.request.GET.get('hire_date_from')
        if hire_date_from:
            queryset = queryset.filter(hire_date__gte=hire_date_from)

        hire_date_to = self.request.GET.get('hire_date_to')
        if hire_date_to:
            queryset = queryset.filter(hire_date__lte=hire_date_to)

        return queryset.order_by('-hire_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = EmployeeProfile.objects.values_list('department', flat=True).distinct()
        return context


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    """Карточка сотрудника"""
    model = EmployeeProfile
    template_name = 'module_app/employees/detail.html'
    context_object_name = 'employee'


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    """Создание сотрудника"""
    model = EmployeeProfile
    form_class = EmployeeProfileForm
    template_name = 'module_app/employees/create.html'
    success_url = reverse_lazy('module_app:employee_list')

    def form_valid(self, form):
        messages.success(self.request, 'Сотрудник успешно добавлен')
        return super().form_valid(form)


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование сотрудника"""
    model = EmployeeProfile
    form_class = EmployeeProfileForm
    template_name = 'module_app/employees/edit.html'

    def get_success_url(self):
        return reverse('module_app:employee_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        employee = form.save(commit=False)
        user = employee.user
        user.first_name = self.request.POST.get('first_name', user.first_name)
        user.last_name = self.request.POST.get('last_name', user.last_name)
        user.email = self.request.POST.get('email', user.email)
        user.save()
        employee.save()
        messages.success(self.request, 'Данные сотрудника обновлены')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при сохранении данных')
        return super().form_invalid(form)


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    """Увольнение сотрудника"""
    model = EmployeeProfile
    template_name = 'module_app/employees/delete.html'
    success_url = reverse_lazy('module_app:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        return context

    def post(self, request, *args, **kwargs):
        employee = self.get_object()
        dismissal_date = request.POST.get('dismissal_date')
        dismissal_reason = request.POST.get('dismissal_reason')

        employee.is_active = False
        employee.dismissal_date = dismissal_date
        employee.save()

        GeneratedDocument.objects.create(
            employee=employee,
            document_type='dismissal_order',
            content=f'Приказ об увольнении {employee.full_name}\nДата увольнения: {dismissal_date}\nПричина: {dismissal_reason}',
            status='generated'
        )

        AccountingIntegration.objects.create(
            employee=employee,
            operation_type='dismissal',
            operation_date=dismissal_date,
            data={'reason': dismissal_reason}
        )

        messages.success(request, f'Сотрудник {employee.full_name} уволен')
        return redirect(self.success_url)


def export_employees(request):
    """Экспорт сотрудников в Excel"""
    employees = EmployeeProfile.objects.all()
    data = []
    for emp in employees:
        data.append({
            'Табельный номер': emp.employee_code,
            'ФИО': emp.full_name,
            'Должность': emp.position,
            'Отдел': emp.department,
            'Телефон': emp.phone,
            'Дата приема': emp.hire_date,
            'Дата увольнения': emp.dismissal_date,
            'Статус': 'Активен' if emp.is_active else 'Уволен'
        })

    return export_to_excel(data, 'employees')


def employee_search(request):
    """Поиск сотрудников (AJAX)"""
    query = request.GET.get('q', '')
    employees = EmployeeProfile.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(position__icontains=query)
    )[:20]

    results = [{'id': e.id, 'name': e.full_name, 'position': e.position} for e in employees]
    return JsonResponse({'results': results})


@login_required
def employee_update(request, pk):
    employee = get_object_or_404(EmployeeProfile, pk=pk)

    print("\n" + "=" * 60)
    print(f"ФУНКЦИЯ ВЫЗВАНА!")
    print(f"ID сотрудника: {pk}")
    print(f"Имя: {employee.user.first_name}")
    print(f"Фамилия: {employee.user.last_name}")
    #print(f"Отчество: {employee.user.middle_name}")
    print(f"Email: {employee.user.email}")
    print(f"Должность: {employee.position}")
    print(f"Отдел: {employee.department}")
    print("=" * 60)

    if request.method == 'POST':
        print("\n📝 POST ДАННЫЕ ПОЛУЧЕНЫ:")
        for key, value in request.POST.items():
            print(f"   {key} = {value}")

        # Сохраняем
        user = employee.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        #user.middle_name = request.POST.get('middle_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        employee.position = request.POST.get('position', '')
        employee.department = request.POST.get('department', '')
        employee.phone = request.POST.get('phone', '')
        employee.address = request.POST.get('address', '')


        employee.middle_name = request.POST.get('middle_name', '')
        employee.bank_account = request.POST.get('bank_account', '')
        employee.tax_id = request.POST.get('tax_id', '')
        employee.snils = request.POST.get('snils', '')

        # Дата рождения
        birth_date_str = request.POST.get('birth_date', '')
        employee.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date() if birth_date_str else None

        # Дата приёма
        hire_date_str = request.POST.get('hire_date', '')
        employee.hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date() if hire_date_str else None

        # Дата увольнения
        dismissal_date_str = request.POST.get('dismissal_date', '')
        employee.dismissal_date = datetime.strptime(dismissal_date_str,
                                                             '%Y-%m-%d').date() if dismissal_date_str else None

        salary_str = request.POST.get('salary')
        if salary_str:
            # замена запятой на точку для преобразования в float
            salary_str = salary_str.replace(',', '.')
            try:
                employee.salary = float(salary_str)
            except ValueError:
                employee.salary = None
        else:
            employee.salary = None

        if 'profile_picture' in request.FILES:
            employee.profile_picture = request.FILES['profile_picture']


        employee.save()

        messages.success(request, 'Данные сохранены!')
        return redirect('module_app:employee_detail', pk=employee.id)

    return render(request, 'module_app/employees/edit.html', {'object': employee})

# ============ УЧЕТ РАБОЧЕГО ВРЕМЕНИ ============

class AttendanceLogListView(LoginRequiredMixin, ListView):
    """Список записей табеля"""
    model = AttendanceLog
    template_name = 'module_app/attendance/list.html'
    context_object_name = 'logs'
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        employee = self.request.GET.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)

        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        event = self.request.GET.get('event')
        if event:
            queryset = queryset.filter(event=event)

        return queryset.order_by('-date', '-time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employees'] = EmployeeProfile.objects.filter(is_active=True)
        context['events'] = AttendanceLog.EVENT_TYPES
        return context


def attendance_log(request):
    """Страница отметки времени"""
    return render(request, 'attendance/log.html')


def attendance_start(request):
    """Начало работы (AJAX)"""
    if request.method == 'POST':
        try:
            profile = request.user.employeeprofile
            today = timezone.now().date()
            now = timezone.now().time()

            if AttendanceLog.objects.filter(employee=profile, date=today, event='start').exists():
                return JsonResponse({'success': False, 'message': 'Рабочий день уже начат'})

            AttendanceLog.objects.create(
                employee=profile,
                date=today,
                time=now,
                event='start'
            )
            return JsonResponse({'success': True, 'message': 'Рабочий день начат'})
        except EmployeeProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Профиль сотрудника не найден'})

    return JsonResponse({'success': False, 'message': 'Метод не поддерживается'})


def attendance_break(request):
    """Начало перерыва (AJAX)"""
    if request.method == 'POST':
        try:
            profile = request.user.employeeprofile
            today = timezone.now().date()
            now = timezone.now().time()

            last_log = AttendanceLog.objects.filter(employee=profile, date=today).order_by('-time').first()
            if not last_log or last_log.event not in ['start', 'resume']:
                return JsonResponse({'success': False, 'message': 'Нельзя начать перерыв'})

            if AttendanceLog.objects.filter(employee=profile, date=today, event='break').exists():
                return JsonResponse({'success': False, 'message': 'Перерыв уже начат'})

            AttendanceLog.objects.create(
                employee=profile,
                date=today,
                time=now,
                event='break'
            )
            return JsonResponse({'success': True, 'message': 'Перерыв начат'})
        except EmployeeProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Профиль сотрудника не найден'})

    return JsonResponse({'success': False, 'message': 'Метод не поддерживается'})


def attendance_resume(request):
    """Окончание перерыва (AJAX)"""
    if request.method == 'POST':
        try:
            profile = request.user.employeeprofile
            today = timezone.now().date()
            now = timezone.now().time()

            last_log = AttendanceLog.objects.filter(employee=profile, date=today).order_by('-time').first()
            if not last_log or last_log.event != 'break':
                return JsonResponse({'success': False, 'message': 'Нельзя продолжить работу'})

            AttendanceLog.objects.create(
                employee=profile,
                date=today,
                time=now,
                event='resume'
            )
            return JsonResponse({'success': True, 'message': 'Работа продолжена'})
        except EmployeeProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Профиль сотрудника не найден'})

    return JsonResponse({'success': False, 'message': 'Метод не поддерживается'})


def attendance_end(request):
    """Окончание работы (AJAX)"""
    if request.method == 'POST':
        try:
            profile = request.user.employeeprofile
            today = timezone.now().date()
            now = timezone.now().time()

            start_log = AttendanceLog.objects.filter(employee=profile, date=today, event='start').first()
            if not start_log:
                return JsonResponse({'success': False, 'message': 'Рабочий день не был начат'})

            if AttendanceLog.objects.filter(employee=profile, date=today, event='end').exists():
                return JsonResponse({'success': False, 'message': 'Рабочий день уже завершен'})

            start_time = datetime.combine(today, start_log.time)
            end_time = datetime.combine(today, now)
            hours = (end_time - start_time).total_seconds() / 3600

            breaks = AttendanceLog.objects.filter(employee=profile, date=today, event='break')
            for break_log in breaks:
                resume_log = AttendanceLog.objects.filter(
                    employee=profile, date=today, event='resume', time__gt=break_log.time
                ).first()
                if resume_log:
                    break_start = datetime.combine(today, break_log.time)
                    break_end = datetime.combine(today, resume_log.time)
                    hours -= (break_end - break_start).total_seconds() / 3600

            AttendanceLog.objects.create(
                employee=profile,
                date=today,
                time=now,
                event='end',
                hours=round(hours, 2)
            )
            return JsonResponse({'success': True, 'message': f'Рабочий день завершен. Отработано: {round(hours, 2)} ч.'})
        except EmployeeProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Профиль сотрудника не найден'})

    return JsonResponse({'success': False, 'message': 'Метод не поддерживается'})


class TodayAttendanceView(LoginRequiredMixin, TemplateView):
    """Отметки за сегодня"""
    template_name = 'module_app/attendance/today.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        return context


class MonthlyReportView(LoginRequiredMixin, TemplateView):
    """Месячный отчет"""
    template_name = 'module_app/reports/monthly.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем параметры из GET запроса
        year_str = self.request.GET.get('year', '')
        month_str = self.request.GET.get('month', '')
        department = self.request.GET.get('department', '')

        # Устанавливаем год
        if year_str and year_str.isdigit():
            year = int(year_str)
        else:
            year = timezone.now().year

        # Устанавливаем месяц (ИСПРАВЛЕНО - нет int() от пустой строки)
        if month_str and month_str.isdigit():
            month = int(month_str)
        else:
            month = timezone.now().month

        # Фильтр по отделам
        employees = EmployeeProfile.objects.filter(is_active=True)
        if department:
            employees = employees.filter(department=department)

        # Данные по сотрудникам
        employees_data = []
        total_hours = 0
        total_overtime = 0

        for emp in employees:
            logs = AttendanceLog.objects.filter(
                employee=emp,
                date__year=year,
                date__month=month
            )
            total = logs.aggregate(total=Sum('hours'))['total'] or 0
            norm = 160  # Норма часов в месяц
            overtime = max(0, total - norm)
            percentage = (total / norm * 100) if norm > 0 else 0

            employees_data.append({
                'id': emp.id,
                'full_name': emp.full_name,
                'department': emp.department,
                'total_hours': total,
                'norm_hours': norm,
                'overtime_hours': overtime,
                'percentage': min(100, percentage)
            })
            total_hours += total
            total_overtime += overtime

        context['employees_data'] = employees_data
        context['year'] = year
        context['month'] = month
        context['month_name'] = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                                 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][month]
        context['years'] = range(2020, timezone.now().year + 1)
        context['months'] = [(i, ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                                  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][i]) for i in range(1, 13)]
        context['departments'] = EmployeeProfile.objects.values_list('department', flat=True).distinct()

        context['summary'] = {
            'total_employees': len(employees_data),
            'total_hours': total_hours,
            'total_overtime': total_overtime,
            'avg_hours': total_hours / len(employees_data) if employees_data else 0,
            'avg_overtime': total_overtime / len(employees_data) if employees_data else 0
        }

        # Данные для графика
        context['chart_labels'] = json.dumps([d['full_name'][:15] for d in employees_data[:10]])
        context['chart_data'] = json.dumps([d['total_hours'] for d in employees_data[:10]])

        return context


def export_attendance(request):
    """Экспорт табеля"""
    from django.http import HttpResponse
    return HttpResponse("Экспорт табеля")


# ============ НАПОМИНАНИЯ ============

class ReminderListView(LoginRequiredMixin, ListView):
    """Список напоминаний"""
    model = Reminder
    template_name = 'module_app/reminders/list.html'
    context_object_name = 'reminders'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_completed=False)
        elif status == 'completed':
            queryset = queryset.filter(is_completed=True)
        return queryset.order_by('due_date', '-priority')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_reminders'] = Reminder.objects.filter(is_completed=False)
        context['today'] = timezone.now().date()
        return context


class ReminderCreateView(LoginRequiredMixin, CreateView):
    """Создание напоминания"""
    model = Reminder
    form_class = ReminderForm
    template_name = 'module_app/reminders/create.html'
    success_url = reverse_lazy('module_app:reminder_list')

    def form_valid(self, form):
        messages.success(self.request, 'Напоминание создано')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employees'] = EmployeeProfile.objects.filter(is_active=True)
        return context


class ReminderDetailView(LoginRequiredMixin, DetailView):
    """Детали напоминания"""
    model = Reminder
    template_name = 'module_app/reminders/detail.html'
    context_object_name = 'reminder'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        return context


@login_required
def reminder_complete(request, pk):
    """Отметка напоминания как выполненного"""
    reminder = get_object_or_404(Reminder, pk=pk)
    reminder.is_completed = True
    reminder.completed_at = timezone.now()
    reminder.save()
    messages.success(request, 'Напоминание отмечено как выполненное')
    return redirect('module_app:reminder_detail', pk=pk)


@login_required
def send_reminders(request):
    """Отправка активных напоминаний"""
    reminders = Reminder.objects.filter(is_sent=False, is_completed=False)
    sent_count = 0
    for reminder in reminders:
        if reminder.should_notify():
            send_reminder_notification(reminder)
            reminder.is_sent = True
            reminder.sent_at = timezone.now()
            reminder.save()
            sent_count += 1
    messages.success(request, f'Отправлено {sent_count} напоминаний')
    return redirect('module_app:reminder_list')


# ============ ОТЧЕТЫ ============

class ReportsView(LoginRequiredMixin, TemplateView):
    """Главная страница отчетов"""
    template_name = 'module_app/reports/index.html'


class MonthlyReportView(LoginRequiredMixin, TemplateView):
    """Месячный отчет"""
    template_name = 'module_app/reports/monthly.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        department = self.request.GET.get('department')

        employees = EmployeeProfile.objects.filter(is_active=True)
        if department:
            employees = employees.filter(department=department)

        employees_data = []
        total_hours = 0
        total_overtime = 0

        for emp in employees:
            logs = AttendanceLog.objects.filter(
                employee=emp,
                date__year=year,
                date__month=month
            )
            total = logs.aggregate(total=Sum('hours'))['total'] or 0
            norm = 160
            overtime = max(0, total - norm)
            percentage = (total / norm * 100) if norm > 0 else 0

            employees_data.append({
                'id': emp.id,
                'full_name': emp.full_name,
                'department': emp.department,
                'total_hours': total,
                'norm_hours': norm,
                'overtime_hours': overtime,
                'percentage': min(100, percentage)
            })
            total_hours += total
            total_overtime += overtime

        context['employees_data'] = employees_data
        context['year'] = year
        context['month'] = month
        context['month_name'] = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                                 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][month]
        context['years'] = range(2020, timezone.now().year + 1)
        context['months'] = [(i, ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                                  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][i]) for i in range(1, 13)]
        context['departments'] = EmployeeProfile.objects.values_list('department', flat=True).distinct()

        context['summary'] = {
            'total_employees': len(employees_data),
            'total_hours': total_hours,
            'total_overtime': total_overtime,
            'avg_hours': total_hours / len(employees_data) if employees_data else 0,
            'avg_overtime': total_overtime / len(employees_data) if employees_data else 0
        }

        context['chart_labels'] = json.dumps([d['full_name'][:15] for d in employees_data[:10]])
        context['chart_data'] = json.dumps([d['total_hours'] for d in employees_data[:10]])

        return context


class YearlyReportView(LoginRequiredMixin, TemplateView):
    """Годовой отчет"""
    template_name = 'module_app/reports/yearly.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = int(self.request.GET.get('year', timezone.now().year))
        department = self.request.GET.get('department')

        from .services.report_service import ReportService
        report = ReportService.get_yearly_attendance_report(year, department)

        context['monthly_data'] = report['monthly_data']
        context['summary'] = report['summary']
        context['year'] = year
        context['years'] = range(2020, timezone.now().year + 1)
        context['departments'] = EmployeeProfile.objects.values_list('department', flat=True).distinct()

        context['month_labels'] = json.dumps([m['name'] for m in report['monthly_data']])
        context['hours_data'] = json.dumps([m['total_hours'] for m in report['monthly_data']])
        context['norm_data'] = json.dumps([m['norm_hours'] for m in report['monthly_data']])

        return context


class OvertimeReportView(LoginRequiredMixin, TemplateView):
    """Отчет по переработкам"""
    template_name = 'module_app/reports/overtime.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = int(self.request.GET.get('year', timezone.now().year))
        month = self.request.GET.get('month')
        department = self.request.GET.get('department')

        if month:
            month = int(month)

        from .services.report_service import ReportService
        report = ReportService.get_overtime_report(year, month, department)

        context['overtime_data'] = report['data']
        context['summary'] = report['summary']
        context['year'] = year
        context['month'] = month
        context['employees'] = EmployeeProfile.objects.filter(is_active=True)
        context['date_from'] = self.request.GET.get('date_from', f"{year}-01-01")
        context['date_to'] = self.request.GET.get('date_to', f"{year}-12-31")
        context['period'] = self.request.GET.get('period', 'year')

        trend_data = []
        trend_labels = []
        for m in range(1, 13):
            monthly_report = ReportService.get_overtime_report(year, m, department)
            trend_data.append(monthly_report['summary']['total_overtime'])
            trend_labels.append(['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                                 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'][m - 1])

        context['trend_labels'] = json.dumps(trend_labels)
        context['trend_data'] = json.dumps(trend_data)

        return context


class DepartmentReportView(LoginRequiredMixin, TemplateView):
    """Отчет по отделам"""
    template_name = 'module_app/reports/department.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        year = int(self.request.GET.get('year', timezone.now().year))
        quarter = self.request.GET.get('quarter', 'all')

        if quarter != 'all':
            quarter = int(quarter)
        else:
            quarter = None

        from .services.report_service import ReportService
        report = ReportService.get_department_report(year, quarter)

        context['departments_data'] = report['data']
        context['summary'] = report['summary']
        context['year'] = year
        context['quarter'] = quarter if quarter else 'all'
        context['years'] = range(2020, timezone.now().year + 1)

        dept_names = [d['name'] for d in report['data']]
        dept_hours = [d['total_hours'] for d in report['data']]
        dept_overtime = [d['overtime_hours'] for d in report['data']]

        context['dept_names'] = json.dumps(dept_names)
        context['dept_hours'] = json.dumps(dept_hours)
        context['dept_overtime'] = json.dumps(dept_overtime)

        return context


class GovernmentReportListView(LoginRequiredMixin, ListView):
    """Список отчетов для госорганов"""
    model = GovernmentReport
    template_name = 'module_app/reports/government_list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        report_type = self.request.GET.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        return queryset.order_by('-generated_at')


class GovernmentReportDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр отчета для госорганов"""
    model = GovernmentReport
    template_name = 'module_app/reports/government_detail.html'
    context_object_name = 'report'


# ============ ДОКУМЕНТЫ ============

class DocumentListView(LoginRequiredMixin, ListView):
    """Список документов"""
    model = GeneratedDocument
    template_name = 'module_app/documents/list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(document_number__icontains=search) |
                Q(employee__user__first_name__icontains=search) |
                Q(employee__user__last_name__icontains=search)
            )
        doc_type = self.request.GET.get('document_type')
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(document_date__gte=date_from)
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(document_date__lte=date_to)
        return queryset.select_related('employee', 'template').order_by('-document_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_types'] = GeneratedDocument.DOCUMENT_STATUS
        return context


class DocumentDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр документа"""
    model = GeneratedDocument
    template_name = 'module_app/documents/detail.html'
    context_object_name = 'document'


class DocumentGenerateView(LoginRequiredMixin, TemplateView):
    """Генерация документа"""
    template_name = 'module_app/documents/generate.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = DocumentTemplate.objects.filter(is_active=True)
        context['employees'] = EmployeeProfile.objects.filter(is_active=True)
        return context


class DocumentTemplateListView(LoginRequiredMixin, ListView):
    """Список шаблонов документов"""
    model = DocumentTemplate
    template_name = 'module_app/documents/templates/list.html'
    context_object_name = 'templates'
    paginate_by = 20


# ============ НАСТРОЙКИ ============

class SettingsView(LoginRequiredMixin, TemplateView):
    """Главная страница настроек"""
    template_name = 'module_app/settings/index.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class GeneralSettingsView(LoginRequiredMixin, TemplateView):
    """Общие настройки"""
    template_name = 'module_app/settings/general.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class NotificationSettingsView(LoginRequiredMixin, TemplateView):
    """Настройки уведомлений"""
    template_name = 'module_app/settings/notifications.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class IntegrationSettingsView(LoginRequiredMixin, TemplateView):
    """Настройки интеграций"""
    template_name = 'module_app/settings/integrations.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class BackupSettingsView(LoginRequiredMixin, TemplateView):
    """Настройки резервного копирования"""
    template_name = 'module_app/settings/backup.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


# ============ АУДИТ ============

class AuditLogListView(LoginRequiredMixin, ListView):
    """Журнал аудита"""
    model = AuditLog
    template_name = 'module_app/audit/list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.GET.get('user')
        if user:
            queryset = queryset.filter(user__username__icontains=user)
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action=action)
        model = self.request.GET.get('model')
        if model:
            queryset = queryset.filter(model_name=model)
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        return queryset.order_by('-created_at')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class AuditLogDetailView(LoginRequiredMixin, DetailView):
    """Детали записи аудита"""
    model = AuditLog
    template_name = 'module_app/audit/detail.html'
    context_object_name = 'log'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


# ============ ОШИБКИ ============

def error_400(request, exception):
    """Ошибка 400"""
    return render(request, 'module_app/400.html', status=400)


def error_403(request, exception):
    """Ошибка 403"""
    return render(request, 'module_app/403.html', status=403)


def error_404(request, exception):
    """Ошибка 404"""
    return render(request, 'module_app/404.html', status=404)


def error_500(request):
    """Ошибка 500"""
    return render(request, 'module_app/500.html', status=500)


# ============ ДОПОЛНИТЕЛЬНЫЕ VIEWS ДЛЯ СОТРУДНИКОВ ============

class EmployeeDocumentsView(LoginRequiredMixin, DetailView):
    """Просмотр документов сотрудника"""
    model = EmployeeProfile
    template_name = 'module_app/employees/documents.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.object.personal_documents.all()
        context['total_documents'] = context['documents'].count()
        context['expiring_soon'] = context['documents'].filter(
            expiry_date__gte=timezone.now().date(),
            expiry_date__lte=timezone.now().date() + timezone.timedelta(days=30)
        ).count()
        context['expired'] = context['documents'].filter(
            expiry_date__lt=timezone.now().date()
        ).count()
        return context


class EmployeeScheduleView(LoginRequiredMixin, UpdateView):
    """Редактирование графика работы сотрудника"""
    model = EmployeeProfile
    template_name = 'module_app/employees/schedule.html'
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['days'] = [
            ('mon', 'Понедельник'),
            ('tue', 'Вторник'),
            ('wed', 'Среда'),
            ('thu', 'Четверг'),
            ('fri', 'Пятница'),
            ('sat', 'Суббота'),
            ('sun', 'Воскресенье')
        ]
        # Добавляем employee в контекст
        context['employee'] = self.get_object()  # ← ЭТА СТРОКА ДОЛЖНА БЫТЬ

        schedule = {}
        for day, name in context['days']:
            sched = self.object.schedules.filter(day=day).first()
            if sched:
                schedule[day] = {
                    'start': sched.start_time.strftime('%H:%M'),
                    'end': sched.end_time.strftime('%H:%M'),
                    'is_off': False
                }
            else:
                schedule[day] = {'is_off': True}
        context['schedule'] = schedule
        return context

    def post(self, request, *args, **kwargs):
        employee = self.get_object()
        employee.schedules.all().delete()

        for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
            is_off = request.POST.get(f'off_{day}') == 'on'
            if not is_off:
                start_time = request.POST.get(f'start_{day}')
                end_time = request.POST.get(f'end_{day}')
                if start_time and end_time:
                    WorkSchedule.objects.create(
                        employee=employee,
                        day=day,
                        start_time=start_time,
                        end_time=end_time
                    )

        messages.success(request, 'График работы сохранен')
        return redirect('module_app:employee_detail', pk=employee.id)


class EmployeeAttendanceView(LoginRequiredMixin, TemplateView):
    """Просмотр табеля сотрудника"""
    template_name = 'module_app/employees/attendance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = get_object_or_404(EmployeeProfile, pk=self.kwargs['pk'])
        context['employee'] = employee

        year = int(self.request.GET.get('year', timezone.now().year))
        month = int(self.request.GET.get('month', timezone.now().month))
        context['year'] = year
        context['month'] = month
        context['month_name'] = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                                 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][month]

        context['available_months'] = []
        for y in range(2023, timezone.now().year + 1):
            for m in range(1, 13):
                if AttendanceLog.objects.filter(employee=employee, date__year=y, date__month=m).exists():
                    context['available_months'].append({
                        'value': f"{y}-{m:02d}",
                        'name': f"{['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][m]} {y}"
                    })

        import calendar
        cal = calendar.monthcalendar(year, month)

        context['calendar'] = []
        for week in cal:
            for day in week:
                if day != 0:
                    date_obj = datetime(year, month, day).date()
                    logs = AttendanceLog.objects.filter(employee=employee, date=date_obj)

                    start_log = logs.filter(event='start').first()
                    end_log = logs.filter(event='end').first()
                    break_logs = logs.filter(event='break')

                    break_hours = 0
                    for br in break_logs:
                        resume = logs.filter(event='resume', time__gt=br.time).first()
                        if resume:
                            break_start = datetime.combine(date_obj, br.time)
                            break_end = datetime.combine(date_obj, resume.time)
                            break_hours += (break_end - break_start).total_seconds() / 3600

                    total_hours = 0
                    if start_log and end_log:
                        start_time = datetime.combine(date_obj, start_log.time)
                        end_time = datetime.combine(date_obj, end_log.time)
                        total_hours = (end_time - start_time).total_seconds() / 3600 - break_hours

                    context['calendar'].append({
                        'date': date_obj,
                        'weekday': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][date_obj.weekday()],
                        'start_time': start_log.time.strftime('%H:%M') if start_log else None,
                        'end_time': end_log.time.strftime('%H:%M') if end_log else None,
                        'break_hours': round(break_hours, 1) if break_hours else None,
                        'hours': round(total_hours, 1) if total_hours else 0,
                        'is_weekend': date_obj.weekday() >= 5,
                        'is_absent': not start_log and not end_log
                    })

        month_logs = AttendanceLog.objects.filter(employee=employee, date__year=year, date__month=month)
        total_hours = month_logs.filter(event='end').aggregate(Sum('hours'))['hours__sum'] or 0
        context['monthly_stats'] = {
            'total_hours': total_hours,
            'overtime_hours': max(0, total_hours - 160),
            'norm_hours': 160
        }

        return context


# ============ ИМПОРТ/ЭКСПОРТ ============

@login_required
def import_employees(request):
    """Импорт сотрудников из Excel"""
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            from .utils.excel_export import import_employees_from_excel
            file = request.FILES['file']
            result = import_employees_from_excel(file)
            messages.success(request, f'Импорт завершен. Добавлено: {result["added"]}, Обновлено: {result["updated"]}')
            if result['errors']:
                messages.warning(request, f'Ошибок: {len(result["errors"])}')
        except Exception as e:
            messages.error(request, f'Ошибка импорта: {str(e)}')
    return redirect('module_app:employee_list')


# ============ ИНТЕГРАЦИЯ С БУХГАЛТЕРИЕЙ ============

class AccountingIntegrationListView(LoginRequiredMixin, ListView):
    """Список операций интеграции"""
    model = AccountingIntegration
    template_name = 'module_app/accounting/list.html'
    context_object_name = 'operations'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        operation_type = self.request.GET.get('operation_type')
        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(operation_date__gte=date_from)
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(operation_date__lte=date_to)
        return queryset.select_related('employee').order_by('-created_at')


def accounting_status(request):
    """Статус интеграции с 1С"""
    from .utils.accounting_api import get_1c_connection_status

    context = {
        'connection_status': get_1c_connection_status(),
        'stats': AccountingIntegration.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            processed=Count('id', filter=Q(status='processed')),
            error=Count('id', filter=Q(status='error'))
        )
    }
    return render(request, 'module_app/accounting/status.html', context)


def retry_accounting(request, pk):
    """Повторная отправка операции в 1С"""
    operation = get_object_or_404(AccountingIntegration, pk=pk)
    operation.status = 'pending'
    operation.save()

    from .utils.accounting_api import sync_to_1c
    result = sync_to_1c(operation)

    if result['success']:
        messages.success(request, f'Операция отправлена. Внешний ID: {result.get("external_id")}')
    else:
        messages.error(request, f'Ошибка: {result.get("error")}')

    return redirect('module_app:accounting_list')


def sync_accounting(request):
    """Синхронизация с бухгалтерской системой"""
    if request.method == 'POST':
        from .utils.accounting_api import sync_to_1c
        sync_type = request.POST.get('sync_type', 'all')

        if sync_type == 'employees':
            employees = EmployeeProfile.objects.filter(is_active=True)
            for emp in employees:
                operation = AccountingIntegration.objects.create(
                    employee=emp,
                    operation_type='hire' if emp.is_active else 'dismissal',
                    operation_date=emp.hire_date or timezone.now().date(),
                    data={'action': 'sync'},
                    status='pending'
                )
                sync_to_1c(operation)
        elif sync_type == 'attendance':
            date_from = request.POST.get('date_from')
            date_to = request.POST.get('date_to')
            employees = EmployeeProfile.objects.filter(is_active=True)
            if request.POST.get('employees'):
                employees = employees.filter(id__in=request.POST.getlist('employees'))

            for emp in employees:
                operation = AccountingIntegration.objects.create(
                    employee=emp,
                    operation_type='vacation',
                    operation_date=timezone.now().date(),
                    data={'date_from': date_from, 'date_to': date_to, 'sync_type': 'attendance'},
                    status='pending'
                )
                sync_to_1c(operation)
        else:
            for emp in EmployeeProfile.objects.filter(is_active=True):
                operation = AccountingIntegration.objects.create(
                    employee=emp,
                    operation_type='hire',
                    operation_date=emp.hire_date or timezone.now().date(),
                    data={'action': 'full_sync'},
                    status='pending'
                )
                sync_to_1c(operation)

        messages.success(request, 'Синхронизация запущена')
        return redirect('module_app:accounting_list')

    return render(request, 'module_app/accounting/sync.html', {
        'employees': EmployeeProfile.objects.filter(is_active=True),
        'default_date_from': (timezone.now().date() - timezone.timedelta(days=30)).isoformat(),
        'default_date_to': timezone.now().date().isoformat()
    })


# ============ ЛИЧНЫЕ ДОКУМЕНТЫ СОТРУДНИКОВ ============

class EmployeeDocumentListView(LoginRequiredMixin, ListView):
    """Список личных документов сотрудников"""
    model = EmployeeDocument
    template_name = 'module_app/documents/personal/list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        document_type = self.request.GET.get('document_type')
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        employee = self.request.GET.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True, expiry_date__gte=timezone.now().date())
        elif status == 'expiring':
            queryset = queryset.filter(
                expiry_date__gte=timezone.now().date(),
                expiry_date__lte=timezone.now().date() + timezone.timedelta(days=30),
                is_active=True
            )
        elif status == 'expired':
            queryset = queryset.filter(expiry_date__lt=timezone.now().date(), is_active=True)
        return queryset.select_related('employee').order_by('-upload_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_types'] = EmployeeDocument.DOCUMENT_TYPES
        context['employees'] = EmployeeProfile.objects.filter(is_active=True)
        return context


class EmployeeDocumentUploadView(LoginRequiredMixin, CreateView):
    """Загрузка личного документа сотрудника"""
    model = EmployeeDocument
    form_class = EmployeeDocumentForm
    template_name = 'module_app/documents/personal/upload.html'
    success_url = reverse_lazy('module_app:employee_document_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employees'] = EmployeeProfile.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Документ успешно загружен')
        return super().form_valid(form)


class EmployeeDocumentDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр личного документа сотрудника"""
    model = EmployeeDocument
    template_name = 'module_app/documents/personal/detail.html'
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reminders'] = Reminder.objects.filter(related_document=self.object)
        return context


class EmployeeDocumentDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление личного документа сотрудника"""
    model = EmployeeDocument
    template_name = 'module_app/documents/personal/confirm_delete.html'
    success_url = reverse_lazy('module_app:employee_document_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Документ удален')
        return super().delete(request, *args, **kwargs)


class ExpiringDocumentsView(LoginRequiredMixin, ListView):
    """Документы с истекающим сроком"""
    model = EmployeeDocument
    template_name = 'module_app/documents/personal/expiring.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        today = timezone.now().date()
        return EmployeeDocument.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=today + timezone.timedelta(days=30),
            is_active=True
        ).select_related('employee').order_by('expiry_date')


class ScheduleCalendarView(LoginRequiredMixin, TemplateView):
    """Календарь графиков работы"""
    template_name = 'module_app/attendance/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employees'] = EmployeeProfile.objects.filter(is_active=True)
        return context


class CalendarView(LoginRequiredMixin, TemplateView):
    """Календарь посещаемости"""
    template_name = 'module_app/attendance/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employees'] = EmployeeProfile.objects.filter(is_active=True)
        return context


def download_document(request, pk):
    """Скачивание документа"""
    document = get_object_or_404(GeneratedDocument, pk=pk)
    if document.file:
        return redirect(document.file.url)
    messages.error(request, 'Файл не найден')
    return redirect('module_app:document_detail', pk=pk)


def sign_document(request, pk):
    """Подписание документа"""
    document = get_object_or_404(GeneratedDocument, pk=pk)
    document.status = 'signed'
    document.signed_by = request.user
    document.signed_at = timezone.now()
    document.save()
    messages.success(request, 'Документ подписан')
    return redirect('module_app:document_detail', pk=pk)


def send_document(request, pk):
    """Отправка документа"""
    document = get_object_or_404(GeneratedDocument, pk=pk)
    document.status = 'sent'
    document.save()
    messages.success(request, 'Документ отправлен')
    return redirect('module_app:document_detail', pk=pk)


def bulk_document_generation(request):
    """Массовая генерация документов"""
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        employee_ids = request.POST.getlist('employee_ids')

        if template_id and employee_ids:
            from .services.document_service import DocumentService
            documents = DocumentService.bulk_generate(template_id, employee_ids, {})
            messages.success(request, f'Сгенерировано {len(documents)} документов')
            return redirect('module_app:document_list')

    return redirect('module_app:document_generate')

class DocumentTemplateCreateView(LoginRequiredMixin, CreateView):
    """Создание шаблона документа"""
    model = DocumentTemplate
    form_class = DocumentTemplateForm
    template_name = 'module_app/documents/templates/form.html'
    success_url = reverse_lazy('module_app:document_template_list')

    def form_valid(self, form):
        messages.success(self.request, 'Шаблон создан')
        return super().form_valid(form)


class DocumentTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование шаблона документа"""
    model = DocumentTemplate
    form_class = DocumentTemplateForm
    template_name = 'module_app/documents/templates/form.html'
    success_url = reverse_lazy('module_app:document_template_list')

    def form_valid(self, form):
        messages.success(self.request, 'Шаблон обновлен')
        return super().form_valid(form)


class DocumentTemplateDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление шаблона документа"""
    model = DocumentTemplate
    template_name = 'module_app/documents/templates/confirm_delete.html'
    success_url = reverse_lazy('module_app:document_template_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Шаблон удален')
        return super().delete(request, *args, **kwargs)


class EmployeeDocumentUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование личного документа сотрудника"""
    model = EmployeeDocument
    form_class = EmployeeDocumentForm
    template_name = 'module_app/documents/personal/edit.html'

    def get_success_url(self):
        return reverse('module_app:employee_document_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Документ обновлен')
        return super().form_valid(form)


class EmployeeDocumentDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр личного документа сотрудника"""
    model = EmployeeDocument
    template_name = 'module_app/documents/personal/detail.html'
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reminders'] = Reminder.objects.filter(related_document=self.object)
        return context


class EmployeeDocumentDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление личного документа сотрудника"""
    model = EmployeeDocument
    template_name = 'module_app/documents/personal/confirm_delete.html'
    success_url = reverse_lazy('module_app:employee_document_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Документ удален')
        return super().delete(request, *args, **kwargs)


class ExpiringDocumentsView(LoginRequiredMixin, ListView):
    """Документы с истекающим сроком"""
    model = EmployeeDocument
    template_name = 'module_app/documents/personal/expiring.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        today = timezone.now().date()
        return EmployeeDocument.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=today + timezone.timedelta(days=30),
            is_active=True
        ).select_related('employee').order_by('expiry_date')


class ReminderDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление напоминания"""
    model = Reminder
    template_name = 'module_app/reminders/confirm_delete.html'
    success_url = reverse_lazy('module_app:reminder_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Напоминание удалено')
        return super().delete(request, *args, **kwargs)


class ReminderSettingsView(LoginRequiredMixin, TemplateView):
    """Настройки напоминаний"""
    template_name = 'module_app/reminders/settings.html'


def generate_report(request):
    """Генерация отчета"""
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        year = request.POST.get('year')
        month = request.POST.get('month')

        from .utils.report_generator import generate_monthly_report_pdf

        messages.success(request, f'Отчет {report_type} сформирован')
        return redirect('module_app:reports')

    return redirect('module_app:reports')


def download_report(request, pk):
    """Скачивание отчета"""
    report = get_object_or_404(GovernmentReport, pk=pk)
    if report.report_file:
        return redirect(report.report_file.url)
    messages.error(request, 'Файл не найден')
    return redirect('module_app:government_report_list')


def send_government_report(request, pk):
    """Отправка отчета в госорган"""
    report = get_object_or_404(GovernmentReport, pk=pk)
    report.status = 'sent'
    report.sent_at = timezone.now()
    report.save()
    messages.success(request, f'Отчет "{report.get_report_type_display()}" отправлен')
    return redirect('module_app:government_report_list')


def generate_government_report(request):
    """Генерация отчета для госорганов"""
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        period = request.POST.get('period')

        from .utils.report_generator import generate_government_report_pdf

        data = []
        report_file = generate_government_report_pdf(report_type, period, data)

        report = GovernmentReport.objects.create(
            report_type=report_type,
            report_period=period,
            status='generated'
        )

        messages.success(request, 'Отчет сформирован')
        return redirect('module_app:government_report_detail', pk=report.id)

    return redirect('module_app:government_report_list')


class GovernmentReportCreateView(LoginRequiredMixin, CreateView):
    """Создание отчета для госорганов"""
    model = GovernmentReport
    template_name = 'module_app/reports/government_form.html'
    fields = ['report_type', 'report_period', 'report_file']
    success_url = reverse_lazy('module_app:government_report_list')

    def form_valid(self, form):
        messages.success(self.request, 'Отчет создан')
        return super().form_valid(form)


class GovernmentReportDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр отчета для госорганов"""
    model = GovernmentReport
    template_name = 'module_app/reports/government_detail.html'
    context_object_name = 'report'


class GovernmentReportListView(LoginRequiredMixin, ListView):
    """Список отчетов для госорганов"""
    model = GovernmentReport
    template_name = 'module_app/reports/government_list.html'
    context_object_name = 'reports'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        report_type = self.request.GET.get('report_type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        return queryset.order_by('-generated_at')


class StatisticsView(LoginRequiredMixin, TemplateView):
    """Статистика системы"""
    template_name = 'module_app/statistics/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from .services.report_service import ReportService

        context['employee_stats'] = ReportService.get_employee_statistics()
        context['attendance_stats'] = ReportService.get_attendance_statistics()
        context['document_stats'] = ReportService.get_document_statistics()
        context['reminder_stats'] = ReportService.get_reminder_statistics()

        return context


class EmployeeStatisticsView(LoginRequiredMixin, TemplateView):
    """Статистика по сотрудникам"""
    template_name = 'module_app/statistics/employees.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        departments = EmployeeProfile.objects.values('department').annotate(
            count=Count('id'),
            active=Count('id', filter=Q(is_active=True)),
            avg_salary=Avg('salary')
        ).order_by('-count')

        context['departments'] = departments
        context['total_employees'] = EmployeeProfile.objects.count()
        context['active_employees'] = EmployeeProfile.objects.filter(is_active=True).count()
        context['avg_age'] = EmployeeProfile.objects.filter(birth_date__isnull=False).aggregate(
            avg_age=Avg('age')
        )['avg_age'] or 0
        context['avg_salary'] = EmployeeProfile.objects.filter(salary__isnull=False).aggregate(
            avg_salary=Avg('salary')
        )['avg_salary'] or 0

        return context


class AttendanceStatisticsView(LoginRequiredMixin, TemplateView):
    """Статистика посещаемости"""
    template_name = 'module_app/statistics/attendance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().date()
        month_start = today.replace(day=1)

        context['total_hours_this_month'] = AttendanceLog.objects.filter(
            date__gte=month_start
        ).aggregate(total=Sum('hours'))['total'] or 0

        context['total_employees'] = EmployeeProfile.objects.filter(is_active=True).count()

        top_employees = AttendanceLog.objects.values('employee').annotate(
            total=Sum('hours')
        ).order_by('-total')[:10]

        context['top_employees'] = []
        for item in top_employees:
            emp = EmployeeProfile.objects.get(id=item['employee'])
            context['top_employees'].append({
                'name': emp.full_name,
                'hours': item['total']
            })

        return context


class DocumentStatisticsView(LoginRequiredMixin, TemplateView):
    """Статистика по документам"""
    template_name = 'module_app/statistics/documents.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().date()

        context['total_documents'] = GeneratedDocument.objects.count()
        context['expired_documents'] = EmployeeDocument.objects.filter(
            expiry_date__lt=today, is_active=True
        ).count()
        context['expiring_soon'] = EmployeeDocument.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=today + timezone.timedelta(days=30),
            is_active=True
        ).count()

        context['by_type'] = GeneratedDocument.objects.values('document_type').annotate(
            count=Count('id')
        )

        context['by_status'] = GeneratedDocument.objects.values('status').annotate(
            count=Count('id')
        )

        return context


def test_update(request, pk):
    emp = get_object_or_404(EmployeeProfile, pk=pk)

    if request.method == 'POST':
        print("=== ТЕСТОВОЕ СОХРАНЕНИЕ ===")
        print(request.POST)

        emp.position = request.POST.get('position', emp.position)
        emp.save()

        messages.success(request, f'Сохранено! Должность: {emp.position}')
        return redirect('module_app:employee_detail', pk=emp.id)

    return render(request, 'module_app/employees/test.html', {'emp': emp})