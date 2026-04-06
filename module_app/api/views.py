# module_app/api/views.py
"""
API представления для системы управления табельным учетом
"""

from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import (
    EmployeeProfile, AttendanceLog, MonthlyReport,
    DocumentTemplate, GeneratedDocument, EmployeeDocument,
    Reminder, AccountingIntegration, GovernmentReport
)

from .serializers import (
    EmployeeSerializer,
    EmployeeListSerializer,
    EmployeeDetailSerializer,
    AttendanceLogSerializer,
    AttendanceLogDetailSerializer,
    MonthlyReportSerializer,
    DocumentTemplateSerializer,
    DocumentTemplateDetailSerializer,
    GeneratedDocumentSerializer,
    GeneratedDocumentDetailSerializer,
    EmployeeDocumentSerializer,
    EmployeeDocumentDetailSerializer,
    ReminderSerializer,
    AccountingIntegrationSerializer,
    DashboardStatsSerializer,
    DocumentGenerationSerializer,
    BulkDocumentGenerationSerializer
)

from ..services.employee_service import EmployeeService
from ..services.document_service import DocumentService
from ..services.attendance_service import AttendanceService
from ..services.reminder_service import ReminderService
from ..services.report_service import ReportService
from ..services.accounting_service import AccountingService
from ..utils.decorators import admin_required, hr_manager_required


# ============ EMPLOYEE VIEWSET ============

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API для работы с сотрудниками
    """
    queryset = EmployeeProfile.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['department', 'employment_type', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'position', 'employee_code']
    ordering_fields = ['hire_date', 'salary', 'user__last_name']
    ordering = ['-hire_date']

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        elif self.action == 'retrieve':
            return EmployeeDetailSerializer
        return EmployeeSerializer

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Получение статистики по сотруднику"""
        employee = self.get_object()
        stats = EmployeeService.get_employee_stats(employee.id)
        return Response(stats)

    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Увольнение сотрудника"""
        employee = self.get_object()
        dismissal_date = request.data.get('dismissal_date', timezone.now().date())
        reason = request.data.get('reason', '')

        dismissed = EmployeeService.dismiss_employee(employee.id, dismissal_date, reason)
        return Response(EmployeeSerializer(dismissed).data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Поиск сотрудников"""
        query = request.query_params.get('q', '')
        department = request.query_params.get('department')
        is_active = request.query_params.get('is_active')

        filters = {}
        if department:
            filters['department'] = department
        if is_active is not None:
            filters['is_active'] = is_active.lower() == 'true'

        employees = EmployeeService.search_employees(query, filters)
        serializer = EmployeeListSerializer(employees, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def departments(self, request):
        """Получение списка отделов"""
        departments = EmployeeProfile.objects.values_list('department', flat=True).distinct()
        return Response([d for d in departments if d])


# ============ ATTENDANCE VIEWSET ============

class AttendanceViewSet(viewsets.ModelViewSet):
    """
    API для учета рабочего времени
    """
    queryset = AttendanceLog.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'date', 'event']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']
    ordering_fields = ['date', 'time']
    ordering = ['-date', '-time']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AttendanceLogDetailSerializer
        return AttendanceLogSerializer

    @action(detail=False, methods=['post'])
    def start(self, request):
        """Отметка начала работы"""
        employee_id = request.data.get('employee_id')
        if not employee_id and hasattr(request.user, 'employeeprofile'):
            employee_id = request.user.employeeprofile.id

        if not employee_id:
            return Response({'error': 'employee_id required'}, status=status.HTTP_400_BAD_REQUEST)

        if not AttendanceService.can_mark(employee_id, 'start'):
            return Response({'error': 'Невозможно отметить начало работы'}, status=status.HTTP_400_BAD_REQUEST)

        log = AttendanceService.log_attendance(employee_id, 'start')
        return Response(AttendanceLogSerializer(log).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def break_start(self, request):
        """Отметка начала перерыва"""
        employee_id = request.data.get('employee_id')
        if not employee_id and hasattr(request.user, 'employeeprofile'):
            employee_id = request.user.employeeprofile.id

        if not employee_id:
            return Response({'error': 'employee_id required'}, status=status.HTTP_400_BAD_REQUEST)

        if not AttendanceService.can_mark(employee_id, 'break'):
            return Response({'error': 'Невозможно отметить начало перерыва'}, status=status.HTTP_400_BAD_REQUEST)

        log = AttendanceService.log_attendance(employee_id, 'break')
        return Response(AttendanceLogSerializer(log).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def break_end(self, request):
        """Отметка окончания перерыва"""
        employee_id = request.data.get('employee_id')
        if not employee_id and hasattr(request.user, 'employeeprofile'):
            employee_id = request.user.employeeprofile.id

        if not employee_id:
            return Response({'error': 'employee_id required'}, status=status.HTTP_400_BAD_REQUEST)

        if not AttendanceService.can_mark(employee_id, 'resume'):
            return Response({'error': 'Невозможно отметить окончание перерыва'}, status=status.HTTP_400_BAD_REQUEST)

        log = AttendanceService.log_attendance(employee_id, 'resume')
        return Response(AttendanceLogSerializer(log).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def end(self, request):
        """Отметка окончания работы"""
        employee_id = request.data.get('employee_id')
        if not employee_id and hasattr(request.user, 'employeeprofile'):
            employee_id = request.user.employeeprofile.id

        if not employee_id:
            return Response({'error': 'employee_id required'}, status=status.HTTP_400_BAD_REQUEST)

        if not AttendanceService.can_mark(employee_id, 'end'):
            return Response({'error': 'Невозможно отметить окончание работы'}, status=status.HTTP_400_BAD_REQUEST)

        log = AttendanceService.log_attendance(employee_id, 'end')
        return Response(AttendanceLogSerializer(log).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Получение отметок за сегодня"""
        employee_id = request.query_params.get('employee_id')
        if not employee_id and hasattr(request.user, 'employeeprofile'):
            employee_id = request.user.employeeprofile.id

        if not employee_id:
            return Response({'error': 'employee_id required'}, status=status.HTTP_400_BAD_REQUEST)

        stats = AttendanceService.get_today_stats(employee_id)
        serializer = AttendanceLogSerializer(stats['logs'], many=True)

        return Response({
            'logs': serializer.data,
            'total_hours': stats['total_hours'],
            'break_hours': stats['break_hours'],
            'net_hours': stats['net_hours']
        })

    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Получение месячной статистики"""
        employee_id = request.query_params.get('employee_id')
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))

        if not employee_id:
            return Response({'error': 'employee_id required'}, status=status.HTTP_400_BAD_REQUEST)

        stats = AttendanceService.get_monthly_stats(employee_id, year, month)
        return Response(stats)

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Получение данных для календаря"""
        employee_id = request.query_params.get('employee_id')
        start = request.query_params.get('start')
        end = request.query_params.get('end')

        if not employee_id:
            return Response({'error': 'employee_id required'}, status=status.HTTP_400_BAD_REQUEST)

        queryset = AttendanceLog.objects.filter(employee_id=employee_id)

        if start:
            queryset = queryset.filter(date__gte=start)
        if end:
            queryset = queryset.filter(date__lte=end)

        events = []
        for log in queryset:
            events.append({
                'id': log.id,
                'title': log.get_event_display(),
                'start': f"{log.date}T{log.time}",
                'end': f"{log.date}T{log.time}",
                'extendedProps': {
                    'hours': log.hours,
                    'event': log.event
                }
            })

        return Response(events)


# ============ DOCUMENT VIEWSET ============

class DocumentTemplateViewSet(viewsets.ModelViewSet):
    """
    API для шаблонов документов
    """
    queryset = DocumentTemplate.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DocumentTemplateDetailSerializer
        return DocumentTemplateSerializer

    @action(detail=True, methods=['get'])
    def variables(self, request, pk=None):
        """Получение списка переменных шаблона"""
        template = self.get_object()
        return Response(template.variables)

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """Предпросмотр документа"""
        template = self.get_object()
        context = request.data.get('context', {})
        rendered = DocumentService.get_document_preview(template.id, context)
        return Response({'html': rendered})


class GeneratedDocumentViewSet(viewsets.ModelViewSet):
    """
    API для сгенерированных документов
    """
    queryset = GeneratedDocument.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'document_type', 'status']
    search_fields = ['document_number', 'employee__user__first_name', 'employee__user__last_name']
    ordering_fields = ['document_date']
    ordering = ['-document_date']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GeneratedDocumentDetailSerializer
        return GeneratedDocumentSerializer

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Генерация документа"""
        serializer = DocumentGenerationSerializer(data=request.data)
        if serializer.is_valid():
            document = DocumentService.generate_document(
                template_id=serializer.validated_data['template_id'],
                employee_id=serializer.validated_data['employee_id'],
                context=serializer.validated_data['context'],
                format=serializer.validated_data.get('format', 'html')
            )
            return Response(GeneratedDocumentSerializer(document).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """Подписание документа"""
        document = self.get_object()
        signed = DocumentService.sign_document(document.id, request.user)
        return Response(GeneratedDocumentSerializer(signed).data)

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """Массовая генерация документов"""
        template_id = request.data.get('template_id')
        employee_ids = request.data.get('employee_ids', [])
        context_template = request.data.get('context_template', {})

        documents = DocumentService.bulk_generate(template_id, employee_ids, context_template)
        serializer = GeneratedDocumentSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    """
    API для личных документов сотрудников
    """
    queryset = EmployeeDocument.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'document_type', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['upload_date', 'expiry_date']
    ordering = ['-upload_date']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EmployeeDocumentDetailSerializer
        return EmployeeDocumentSerializer

    @action(detail=False, methods=['get'])
    def expiring(self, request):
        """Получение документов с истекающим сроком"""
        days = int(request.query_params.get('days', 30))
        today = timezone.now().date()
        end_date = today + timedelta(days=days)

        documents = EmployeeDocument.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=end_date,
            is_active=True
        )
        serializer = EmployeeDocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Получение просроченных документов"""
        today = timezone.now().date()
        documents = EmployeeDocument.objects.filter(
            expiry_date__lt=today,
            is_active=True
        )
        serializer = EmployeeDocumentSerializer(documents, many=True)
        return Response(serializer.data)


# ============ REMINDER VIEWSET ============

class ReminderViewSet(viewsets.ModelViewSet):
    """
    API для напоминаний
    """
    queryset = Reminder.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'reminder_type', 'priority', 'is_sent', 'is_completed']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date']
    ordering = ['due_date']

    serializer_class = ReminderSerializer

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Получение активных напоминаний"""
        reminders = ReminderService.get_active_reminders()
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def due_soon(self, request):
        """Получение напоминаний, которые скоро истекают"""
        days = int(request.query_params.get('days', 7))
        reminders = ReminderService.get_reminders_due_soon(days)
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Отметка напоминания как выполненного"""
        reminder = self.get_object()
        completed = ReminderService.complete_reminder(reminder.id)
        return Response(self.get_serializer(completed).data)

    @action(detail=False, methods=['post'])
    def send(self, request):
        """Отправка всех ожидающих напоминаний"""
        sent_count = ReminderService.send_pending_reminders()
        return Response({'sent': sent_count})


# ============ REPORT VIEWSET ============

class ReportViewSet(viewsets.GenericViewSet):
    """
    API для отчетов
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Месячный отчет"""
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        department = request.query_params.get('department')

        report = ReportService.get_monthly_attendance_report(year, month, department)
        return Response(report)

    @action(detail=False, methods=['get'])
    def yearly(self, request):
        """Годовой отчет"""
        year = int(request.query_params.get('year', timezone.now().year))
        department = request.query_params.get('department')

        report = ReportService.get_yearly_attendance_report(year, department)
        return Response(report)

    @action(detail=False, methods=['get'])
    def overtime(self, request):
        """Отчет по переработкам"""
        year = int(request.query_params.get('year', timezone.now().year))
        month = request.query_params.get('month')
        department = request.query_params.get('department')

        if month:
            month = int(month)

        report = ReportService.get_overtime_report(year, month, department)
        return Response(report)

    @action(detail=False, methods=['get'])
    def department(self, request):
        """Отчет по отделам"""
        year = int(request.query_params.get('year', timezone.now().year))
        quarter = request.query_params.get('quarter')

        if quarter and quarter != 'all':
            quarter = int(quarter)
        else:
            quarter = None

        report = ReportService.get_department_report(year, quarter)
        return Response(report)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика системы"""
        employee_stats = {
            'total_employees': EmployeeProfile.objects.count(),
            'active_employees': EmployeeProfile.objects.filter(is_active=True).count(),
            'dismissed_employees': EmployeeProfile.objects.filter(is_active=False).count(),
            'employees_on_probation': EmployeeProfile.objects.filter(employment_type='probation').count(),
            'average_age': EmployeeProfile.objects.filter(birth_date__isnull=False).aggregate(
                avg_age=Avg('age')
            )['avg_age'] or 0,
            'average_salary': EmployeeProfile.objects.filter(salary__isnull=False).aggregate(
                avg_salary=Avg('salary')
            )['avg_salary'] or 0,
            'departments_count': EmployeeProfile.objects.values('department').distinct().count()
        }

        today = timezone.now().date()
        month_start = today.replace(day=1)

        attendance_stats = {
            'total_hours_this_month': AttendanceLog.objects.filter(
                date__gte=month_start
            ).aggregate(total=Sum('hours'))['total'] or 0,
            'average_hours_per_day': AttendanceLog.objects.filter(
                date__gte=month_start
            ).values('date').annotate(daily_sum=Sum('hours')).aggregate(avg=Avg('daily_sum'))['avg'] or 0,
            'total_overtime_this_month': 0,  # Рассчитывается отдельно
            'attendance_rate': 0,
            'most_active_employees': AttendanceLog.objects.values('employee').annotate(
                total=Sum('hours')
            ).order_by('-total')[:10].values('employee__user__first_name', 'employee__user__last_name', 'total'),
            'department_stats': []
        }

        document_stats = {
            'total_documents': GeneratedDocument.objects.count(),
            'expired_documents': EmployeeDocument.objects.filter(
                expiry_date__lt=today, is_active=True
            ).count(),
            'expiring_soon_documents': EmployeeDocument.objects.filter(
                expiry_date__gte=today,
                expiry_date__lte=today + timedelta(days=30),
                is_active=True
            ).count(),
            'documents_by_type': dict(GeneratedDocument.objects.values('document_type').annotate(
                count=Count('id')
            ).values_list('document_type', 'count')),
            'documents_by_status': dict(GeneratedDocument.objects.values('status').annotate(
                count=Count('id')
            ).values_list('status', 'count')),
            'total_documents_size': '0 KB'
        }

        return Response({
            'employees': employee_stats,
            'attendance': attendance_stats,
            'documents': document_stats
        })

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Статистика для дашборда"""
        today = timezone.now().date()
        month_start = today.replace(day=1)

        stats = {
            'total_employees': EmployeeProfile.objects.count(),
            'active_employees': EmployeeProfile.objects.filter(is_active=True).count(),
            'active_reminders': Reminder.objects.filter(is_completed=False).count(),
            'expired_documents': EmployeeDocument.objects.filter(
                expiry_date__lt=today, is_active=True
            ).count(),
            'total_hours_this_month': AttendanceLog.objects.filter(
                date__gte=month_start
            ).aggregate(total=Sum('hours'))['total'] or 0,
            'attendance_rate': 0
        }

        return Response(stats)


# ============ ACCOUNTING VIEWSET ============

class AccountingViewSet(viewsets.ModelViewSet):
    """
    API для интеграции с бухгалтерией
    """
    queryset = AccountingIntegration.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['operation_type', 'status']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    serializer_class = AccountingIntegrationSerializer

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """Синхронизация с 1С"""
        result = AccountingService.sync_pending_operations()
        return Response(result)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Статус подключения к 1С"""
        status = AccountingService.get_connection_status()
        stats = AccountingService.get_operation_statistics()
        return Response({
            'connection': status,
            'statistics': stats
        })

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Повторная отправка операции"""
        operation = self.get_object()
        operation.status = 'pending'
        operation.save()

        result = AccountingService.sync_pending_operations()
        return Response(result)


# ============ AUTH VIEWS ============

class LoginView(generics.GenericAPIView):
    """
    API для входа в систему
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from django.contrib.auth import authenticate, login
        from rest_framework.authtoken.models import Token

        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'full_name': user.get_full_name() or user.username
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(generics.GenericAPIView):
    """
    API для выхода из системы
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        from django.contrib.auth import logout
        logout(request)
        return Response({'message': 'Logged out successfully'})


class RegisterView(generics.CreateAPIView):
    """
    API для регистрации пользователя
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from django.contrib.auth.models import User

        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Создание профиля сотрудника
        EmployeeProfile.objects.create(user=user)

        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API для профиля пользователя
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = getattr(user, 'employeeprofile', None)

        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name() or user.username,
            'profile': {
                'position': profile.position if profile else None,
                'department': profile.department if profile else None,
                'phone': profile.phone if profile else None,
                'profile_picture': profile.profile_picture.url if profile and profile.profile_picture else None
            } if profile else None
        })

    def put(self, request):
        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save()

        profile = getattr(user, 'employeeprofile', None)
        if profile:
            profile.position = request.data.get('position', profile.position)
            profile.department = request.data.get('department', profile.department)
            profile.phone = request.data.get('phone', profile.phone)
            profile.save()

        return self.get(request)


# ============ DOCUMENT VIEWSET ============

class DocumentViewSet(viewsets.ModelViewSet):
    """
    API для работы с документами
    """
    queryset = GeneratedDocument.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'document_type', 'status']
    search_fields = ['document_number', 'employee__user__first_name', 'employee__user__last_name']
    ordering_fields = ['document_date']
    ordering = ['-document_date']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GeneratedDocumentDetailSerializer
        return GeneratedDocumentSerializer

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Генерация документа"""
        serializer = DocumentGenerationSerializer(data=request.data)
        if serializer.is_valid():
            from ..services.document_service import DocumentService
            document = DocumentService.generate_document(
                template_id=serializer.validated_data['template_id'],
                employee_id=serializer.validated_data['employee_id'],
                context=serializer.validated_data['context'],
                format=serializer.validated_data.get('format', 'html')
            )
            return Response(GeneratedDocumentSerializer(document).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """Подписание документа"""
        document = self.get_object()
        from ..services.document_service import DocumentService
        signed = DocumentService.sign_document(document.id, request.user)
        return Response(GeneratedDocumentSerializer(signed).data)

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """Массовая генерация документов"""
        template_id = request.data.get('template_id')
        employee_ids = request.data.get('employee_ids', [])
        context_template = request.data.get('context_template', {})

        from ..services.document_service import DocumentService
        documents = DocumentService.bulk_generate(template_id, employee_ids, context_template)
        serializer = GeneratedDocumentSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    """
    API для шаблонов документов
    """
    queryset = DocumentTemplate.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['template_type', 'is_active']
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DocumentTemplateDetailSerializer
        return DocumentTemplateSerializer

    @action(detail=True, methods=['get'])
    def variables(self, request, pk=None):
        """Получение списка переменных шаблона"""
        template = self.get_object()
        return Response(template.variables)

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """Предпросмотр документа"""
        template = self.get_object()
        context = request.data.get('context', {})
        from ..services.document_service import DocumentService
        rendered = DocumentService.get_document_preview(template.id, context)
        return Response({'html': rendered})


class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    """
    API для личных документов сотрудников
    """
    queryset = EmployeeDocument.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'document_type', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['upload_date', 'expiry_date']
    ordering = ['-upload_date']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EmployeeDocumentDetailSerializer
        return EmployeeDocumentSerializer

    @action(detail=False, methods=['get'])
    def expiring(self, request):
        """Получение документов с истекающим сроком"""
        days = int(request.query_params.get('days', 30))
        today = timezone.now().date()
        end_date = today + timezone.timedelta(days=days)

        documents = EmployeeDocument.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=end_date,
            is_active=True
        )
        serializer = EmployeeDocumentSerializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Получение просроченных документов"""
        today = timezone.now().date()
        documents = EmployeeDocument.objects.filter(
            expiry_date__lt=today,
            is_active=True
        )
        serializer = EmployeeDocumentSerializer(documents, many=True)
        return Response(serializer.data)


# ============ REMINDER VIEWSET ============

class ReminderViewSet(viewsets.ModelViewSet):
    """
    API для напоминаний
    """
    queryset = Reminder.objects.all()
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'reminder_type', 'priority', 'is_sent', 'is_completed']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date']
    ordering = ['due_date']

    serializer_class = ReminderSerializer

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Получение активных напоминаний"""
        from ..services.reminder_service import ReminderService
        reminders = ReminderService.get_active_reminders()
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def due_soon(self, request):
        """Получение напоминаний, которые скоро истекают"""
        days = int(request.query_params.get('days', 7))
        from ..services.reminder_service import ReminderService
        reminders = ReminderService.get_reminders_due_soon(days)
        serializer = self.get_serializer(reminders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Отметка напоминания как выполненного"""
        reminder = self.get_object()
        from ..services.reminder_service import ReminderService
        completed = ReminderService.complete_reminder(reminder.id)
        return Response(self.get_serializer(completed).data)

    @action(detail=False, methods=['post'])
    def send(self, request):
        """Отправка всех ожидающих напоминаний"""
        from ..services.reminder_service import ReminderService
        sent_count = ReminderService.send_pending_reminders()
        return Response({'sent': sent_count})


# ============ REPORT VIEWSET ============

class ReportViewSet(viewsets.GenericViewSet):
    """
    API для отчетов
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Месячный отчет"""
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        department = request.query_params.get('department')

        from ..services.report_service import ReportService
        report = ReportService.get_monthly_attendance_report(year, month, department)
        return Response(report)

    @action(detail=False, methods=['get'])
    def yearly(self, request):
        """Годовой отчет"""
        year = int(request.query_params.get('year', timezone.now().year))
        department = request.query_params.get('department')

        from ..services.report_service import ReportService
        report = ReportService.get_yearly_attendance_report(year, department)
        return Response(report)

    @action(detail=False, methods=['get'])
    def overtime(self, request):
        """Отчет по переработкам"""
        year = int(request.query_params.get('year', timezone.now().year))
        month = request.query_params.get('month')
        department = request.query_params.get('department')

        if month:
            month = int(month)

        from ..services.report_service import ReportService
        report = ReportService.get_overtime_report(year, month, department)
        return Response(report)

    @action(detail=False, methods=['get'])
    def department(self, request):
        """Отчет по отделам"""
        year = int(request.query_params.get('year', timezone.now().year))
        quarter = request.query_params.get('quarter')

        if quarter and quarter != 'all':
            quarter = int(quarter)
        else:
            quarter = None

        from ..services.report_service import ReportService
        report = ReportService.get_department_report(year, quarter)
        return Response(report)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Статистика для дашборда"""
        today = timezone.now().date()
        month_start = today.replace(day=1)

        stats = {
            'total_employees': EmployeeProfile.objects.count(),
            'active_employees': EmployeeProfile.objects.filter(is_active=True).count(),
            'active_reminders': Reminder.objects.filter(is_completed=False).count(),
            'expired_documents': EmployeeDocument.objects.filter(
                expiry_date__lt=today, is_active=True
            ).count(),
            'total_hours_this_month': AttendanceLog.objects.filter(
                date__gte=month_start
            ).aggregate(total=Sum('hours'))['total'] or 0,
            'attendance_rate': 0
        }

        return Response(stats)