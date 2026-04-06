# module_app/api/serializers/document_serializers.py
"""
Сериализаторы для документов
"""

from rest_framework import serializers
from ...models import DocumentTemplate, GeneratedDocument, EmployeeDocument
from .employee_serializers import EmployeeListSerializer


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для шаблонов документов"""
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)

    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'name', 'template_type', 'template_type_display',
            'content', 'variables', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DocumentTemplateDetailSerializer(DocumentTemplateSerializer):
    """Детальный сериализатор для шаблонов документов"""
    variables_list = serializers.SerializerMethodField()

    class Meta(DocumentTemplateSerializer.Meta):
        fields = DocumentTemplateSerializer.Meta.fields + ['variables_list']

    def get_variables_list(self, obj):
        """Возвращает список переменных в читаемом формате"""
        return [{'key': k, 'label': v} for k, v in obj.variables.items()]


class GeneratedDocumentSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для сгенерированных документов"""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    signed_by_name = serializers.CharField(source='signed_by.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedDocument
        fields = [
            'id', 'employee', 'employee_name', 'template', 'template_name',
            'document_type', 'document_type_display', 'document_number',
            'document_date', 'content', 'file', 'file_url', 'status',
            'status_display', 'signed_by', 'signed_by_name', 'signed_at', 'notes'
        ]
        read_only_fields = ['document_number', 'document_date']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class GeneratedDocumentDetailSerializer(GeneratedDocumentSerializer):
    """Детальный сериализатор для сгенерированных документов"""
    employee_detail = EmployeeListSerializer(source='employee', read_only=True)

    class Meta(GeneratedDocumentSerializer.Meta):
        fields = GeneratedDocumentSerializer.Meta.fields + ['employee_detail']


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для личных документов сотрудника"""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeDocument
        fields = [
            'id', 'employee', 'employee_name', 'document_type',
            'document_type_display', 'title', 'file', 'file_url',
            'upload_date', 'expiry_date', 'description', 'is_active',
            'is_expired', 'days_until_expiry'
        ]
        read_only_fields = ['upload_date']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class EmployeeDocumentDetailSerializer(EmployeeDocumentSerializer):
    """Детальный сериализатор для личных документов сотрудника"""
    employee_detail = EmployeeListSerializer(source='employee', read_only=True)

    class Meta(EmployeeDocumentSerializer.Meta):
        fields = EmployeeDocumentSerializer.Meta.fields + ['employee_detail']


class DocumentGenerationSerializer(serializers.Serializer):
    """Сериализатор для генерации документа"""
    template_id = serializers.IntegerField(required=True)
    employee_id = serializers.IntegerField(required=True)
    context = serializers.DictField(required=True)
    format = serializers.ChoiceField(choices=['html', 'pdf', 'docx'], default='html')

    def validate_template_id(self, value):
        from ...models import DocumentTemplate
        if not DocumentTemplate.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Шаблон не найден или неактивен")
        return value

    def validate_employee_id(self, value):
        from ...models import EmployeeProfile
        if not EmployeeProfile.objects.filter(id=value).exists():
            raise serializers.ValidationError("Сотрудник не найден")
        return value


class BulkDocumentGenerationSerializer(serializers.Serializer):
    """Сериализатор для массовой генерации документов"""
    template_id = serializers.IntegerField(required=True)
    employee_ids = serializers.ListField(child=serializers.IntegerField(), required=True)
    context_template = serializers.DictField(required=True)
    format = serializers.ChoiceField(choices=['html', 'pdf', 'docx'], default='html')

    def validate_template_id(self, value):
        from ...models import DocumentTemplate
        if not DocumentTemplate.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Шаблон не найден или неактивен")
        return value

    def validate_employee_ids(self, value):
        from ...models import EmployeeProfile
        if not value:
            raise serializers.ValidationError("Список сотрудников не может быть пустым")

        existing_ids = set(EmployeeProfile.objects.filter(id__in=value).values_list('id', flat=True))
        missing_ids = set(value) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(f"Сотрудники не найдены: {missing_ids}")
        return value