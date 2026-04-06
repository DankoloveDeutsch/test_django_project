# module_app/services/document_service.py
"""
Сервис для работы с документами
"""

from django.db import transaction
from django.utils import timezone
from ..models import DocumentTemplate, GeneratedDocument, Reminder


class DocumentService:
    """Сервис для работы с документами"""

    @staticmethod
    def generate_document(template_id, employee_id, context):
        """Генерация документа из шаблона"""
        template = DocumentTemplate.objects.get(id=template_id)
        employee = EmployeeProfile.objects.get(id=employee_id)

        # Подстановка переменных
        content = template.render(context)

        # Создание документа
        document = GeneratedDocument.objects.create(
            employee=employee,
            template=template,
            document_type=template.template_type,
            content=content,
            status='generated'
        )

        return document

    @staticmethod
    def sign_document(document_id, user):
        """Подписание документа"""
        document = GeneratedDocument.objects.get(id=document_id)
        document.status = 'signed'
        document.signed_by = user
        document.signed_at = timezone.now()
        document.save()

        return document

    @staticmethod
    def create_template(name, template_type, content, variables):
        """Создание шаблона документа"""
        return DocumentTemplate.objects.create(
            name=name,
            template_type=template_type,
            content=content,
            variables=variables
        )

    @staticmethod
    def get_employee_documents(employee_id):
        """Получение документов сотрудника"""
        return GeneratedDocument.objects.filter(employee_id=employee_id).order_by('-document_date')

    @staticmethod
    def get_document_preview(template_id, context):
        """Предпросмотр документа"""
        template = DocumentTemplate.objects.get(id=template_id)
        return template.render(context)