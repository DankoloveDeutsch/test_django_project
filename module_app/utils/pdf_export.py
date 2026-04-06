# module_app/utils/pdf_export.py
"""
Экспорт данных в PDF
"""

import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
import os


def export_to_pdf(data, title, headers=None):
    """
    Экспорт данных в PDF

    Args:
        data: список словарей с данными
        title: заголовок отчета
        headers: список заголовков (опционально)

    Returns:
        bytes: PDF контент
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', alignment=TA_CENTER, fontSize=16, leading=20, spaceAfter=20))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, fontSize=10))

    story = []

    # Заголовок
    story.append(Paragraph(title, styles['CenterTitle']))
    story.append(Spacer(1, 0.5 * cm))

    # Дата
    from datetime import datetime
    story.append(Paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}", styles['Right']))
    story.append(Spacer(1, 0.5 * cm))

    if data:
        # Определяем заголовки
        if not headers:
            headers = list(data[0].keys())

        # Создаем таблицу
        table_data = [headers]
        for row in data:
            table_data.append([str(row.get(h, '')) for h in headers])

        # Ширина колонок
        col_widths = [4 * cm] * len(headers)

        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))

        story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def export_employee_card_pdf(employee):
    """
    Экспорт карточки сотрудника в PDF

    Args:
        employee: объект EmployeeProfile

    Returns:
        bytes: PDF контент
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', alignment=TA_CENTER, fontSize=16, leading=20))
    styles.add(ParagraphStyle(name='SectionHeader', alignment=TA_LEFT, fontSize=12, leading=14, spaceAfter=10))

    story = []

    # Заголовок
    story.append(Paragraph(f"ЛИЧНАЯ КАРТОЧКА СОТРУДНИКА", styles['CenterTitle']))
    story.append(Spacer(1, 0.5 * cm))

    # Общая информация
    story.append(Paragraph("1. ОБЩАЯ ИНФОРМАЦИЯ", styles['SectionHeader']))

    data = [
        ['Табельный номер:', employee.employee_code or '—'],
        ['ФИО:', employee.full_name],
        ['Должность:', employee.position or '—'],
        ['Отдел:', employee.department or '—'],
        ['Дата рождения:', employee.birth_date.strftime('%d.%m.%Y') if employee.birth_date else '—'],
        ['Возраст:', str(employee.age) if employee.age else '—'],
        ['Телефон:', employee.phone or '—'],
        ['Email:', employee.user.email],
        ['Адрес:', employee.address or '—'],
    ]

    table = Table(data, colWidths=[4 * cm, 10 * cm])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))

    # Трудоустройство
    story.append(Paragraph("2. ТРУДОУСТРОЙСТВО", styles['SectionHeader']))

    employment_data = [
        ['Дата приема:', employee.hire_date.strftime('%d.%m.%Y') if employee.hire_date else '—'],
        ['Дата увольнения:', employee.dismissal_date.strftime('%d.%m.%Y') if employee.dismissal_date else '—'],
        ['Тип занятости:', dict(EmployeeProfile.EMPLOYMENT_TYPES).get(employee.employment_type, '—')],
        ['Оклад:', f"{employee.salary:,.2f} руб." if employee.salary else '—'],
        ['Банковский счет:', employee.bank_account or '—'],
    ]

    table = Table(employment_data, colWidths=[4 * cm, 10 * cm])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))

    # Документы
    story.append(Paragraph("3. ДОКУМЕНТЫ", styles['SectionHeader']))

    docs = employee.personal_documents.all()
    if docs.exists():
        doc_data = [['Тип', 'Название', 'Срок действия']]
        for doc in docs:
            doc_data.append([
                doc.get_document_type_display(),
                doc.title,
                doc.expiry_date.strftime('%d.%m.%Y') if doc.expiry_date else '—'
            ])

        table = Table(doc_data, colWidths=[3 * cm, 7 * cm, 4 * cm])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("Нет загруженных документов", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()