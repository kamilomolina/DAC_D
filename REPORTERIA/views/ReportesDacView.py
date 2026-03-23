from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connections
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime, timedelta
from CONTABLE.views.ContableView import dictfetchall
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import sessionmaker
import time
import pymysql
import requests
from requests.exceptions import HTTPError
import hashlib
import subprocess
import jwt
from urllib.parse import quote_plus
import json
from django.core.mail import send_mail
from django.urls import reverse
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import locale
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, Frame, PageBreak, KeepTogether
import io
from io import BytesIO
from django.core.mail import get_connection, EmailMultiAlternatives
from collections import defaultdict

TOKEN = '2e078366ee3366544e4132ebb24eb2948270bbce69aa8ff22a30a2422cc12a7e'
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


def capitalizar_frase(frase):
    stopwords = {'de', 'la', 'y', 'en', 'del', 'al', 'un', 'una', 'unos', 'unas', 'los', 'las'}  # Palabras que van en minúscula
    palabras = frase.lower().split()
    resultado = []
    
    for i, palabra in enumerate(palabras):
        if palabra in stopwords and i != 0:  # Deja las palabras en minúscula excepto si es la primera
            resultado.append(palabra)
        else:
            resultado.append(palabra.capitalize())  # Capitaliza la palabra
    
    return ' '.join(resultado)


class GenerarReportePDF(APIView):

    def get(self, request, id_gasto, *args, **kwargs):

        # Obtener encabezado y detalles mediante stored procedures
        encabezado = self.obtener_encabezado(id_gasto)
        detalles = self.obtener_detalles(id_gasto)

        return self.generar_pdf(encabezado, detalles)


    def obtener_encabezado(self, id_gasto):
        # Ejecutar el stored procedure para obtener el encabezado
        with connections['universal'].cursor() as cursor:
            cursor.callproc('VAIC_PDF_GASTOS_HEADER', [id_gasto])
            encabezado_result = cursor.fetchone()

        # Mapa del resultado del procedimiento
        encabezado = {
            'empresa_nombre': encabezado_result[0],
            'tipo_solicitud': encabezado_result[1],
            'fecha_pago': encabezado_result[2],
            'tipo_docto': encabezado_result[3],
            'logo_url': "http://3.230.160.184:81/media/carbajal.jpg",
            'moneda': encabezado_result[4],
            'concepto': encabezado_result[5],
            'fecha_documento': encabezado_result[6],
            'usuario': encabezado_result[7]
        }
        return encabezado


    def obtener_detalles(self, id_gasto):
        # Ejecutar el stored procedure para obtener los detalles
        detalles = []
        with connections['universal'].cursor() as cursor:
            cursor.callproc('VAIC_PDF_GASTOS_DETAILS', [id_gasto])
            detalles_result = cursor.fetchall()

        # Convertir los resultados en un diccionario
        for detalle in detalles_result:
            detalles.append({
                'cuenta_contable': detalle[0],
                'descripcion_cuenta': detalle[1],
                'valor_u': detalle[2],
                'sub_total': detalle[3],
                'isv': detalle[4],
                'ajuste': detalle[5],
                'total': detalle[6],
                'concepto_detalle': detalle[7],
                'id_empresa': detalle[8],  # Se agrega el ID de la empresa
                'nombre_empresa': detalle[9]  # Se agrega el nombre de la empresa
            })

        return detalles


    def draw_footer(self, canvas, doc, encabezado, style_normal):
        """
        Función para dibujar la firma en el pie de la última página.
        """
        canvas.saveState()

        # Posicionar la firma siempre en la parte inferior de la página
        width, height = letter
        firma_data = [
            [
                Paragraph("____________________________", style_normal),
                "",
                Paragraph("Usuario: {}".format(encabezado['usuario']), style_normal)
            ],
            [
                Paragraph("Autorizado por", style_normal),
                "",
                Paragraph("Fecha: {}".format(encabezado['fecha_documento']), style_normal)
            ]
        ]
        
        firma_table = Table(firma_data, colWidths=[4.0 * inch, 0.5 * inch, 3.0 * inch])
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Firma alineada a la izquierda
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Usuario y fecha alineados a la derecha
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))

        # Dibujar la tabla en la posición final de la página
        firma_table.wrapOn(canvas, width, height)
        firma_table.drawOn(canvas, 0.7 * inch, 0.75 * inch)

        canvas.restoreState()


    def draw_footer_last_page(self, canvas, doc, encabezado, style_normal):
        if doc.page == doc.page_count:  # Asegurarse de que es la última página
            self.draw_footer(canvas, doc, encabezado, style_normal)


    def generar_pdf(self, encabezado, detalles):
        # Lista para agregar elementos (contenido del PDF)
        elements = []

        # Estilos de texto
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(name='Title', fontSize=14, alignment=1)  # Empresa más grande
        style_subtitle = ParagraphStyle(name='Subtitle', fontSize=12, alignment=1)  # Título de la solicitud más pequeño
        style_normal = ParagraphStyle(name='Normal', fontSize=8, leading=12)

        # Crear una tabla para el logo y el encabezado de la empresa
        logo = Image(encabezado['logo_url'], 1 * inch, 1 * inch)  # Ajuste de tamaño del logo
        data_encabezado = [
            [logo, Paragraph("<b>{}</b>".format(encabezado['tipo_solicitud']), style_title)]
        ]

        table_encabezado = Table(data_encabezado, colWidths=[1.5 * inch, 6.7 * inch])  # Ajuste de los anchos de columna
        table_encabezado.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Centrar el texto de la empresa
            ('VALIGN', (0, 0), (1, 0), 'TOP')  # Alinear el logo con la parte superior
        ]))

        elements.append(table_encabezado)

        # Encabezado en formato de tabla para los detalles del documento
        data_encabezado_info = [
            [
                Paragraph("<b>Fecha de Doc:</b> {}".format(encabezado['fecha_documento']), style_normal),
                Paragraph("<b>Fecha de Pago:</b> {}".format(encabezado['fecha_pago']), style_normal),
                Paragraph("<b>Tipo Docto:</b> {}".format(encabezado['tipo_docto']), style_normal),
                Paragraph("<b>Moneda:</b> {}".format(encabezado['moneda']), style_normal),
            ]
        ]

        table_encabezado_info = Table(data_encabezado_info, colWidths=[2.0 * inch, 2.0 * inch, 2.0 * inch, 2.2 * inch])
        table_encabezado_info.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Alinear a la izquierda
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # Reducir el tamaño del texto
        ]))

        elements.append(table_encabezado_info)

        # Añadir una línea divisoria antes del encabezado de la tabla de detalles
        elements.append(Spacer(1, 6))
        elements.append(Table([['']], colWidths=[8.2 * inch]))

        # Inicializar los totales generales
        total_valor_u_general = 0
        total_sub_total_general = 0
        total_isv_general = 0
        total_total_general = 0

        # Inicializar id_empresa_anterior antes del bucle
        id_empresa_anterior = None  # Inicialmente no hay empresa anterior

        # Variable para guardar la empresa actual (opcional)
        empresa_actual = None
        empty_text = None

        # Inicializar la lista data para los detalles
        data = []

        # Preparar la tabla de detalles agrupados por empresa
        # Bucle por empresas (dentro del bucle principal de detalles)
        # Preparar la tabla de detalles agrupados por empresa
        for detalle in detalles:
            # Cuando cambie de empresa, mostrar el nombre de la nueva empresa
            if id_empresa_anterior != detalle['id_empresa']:
                # Si ya hay detalles en 'data', crear la tabla antes de cambiar de empresa
                if data:
                    table = Table(data, colWidths=[2.3 * inch, 1.0 * inch, 1.0 * inch, 3.9 * inch])
                    table.setStyle(TableStyle([
                        ('ALIGN', (1, 0), (-2, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black)
                    ]))
                    elements.append(table)
                    data = []

                # Nueva empresa
                elements.append(Spacer(1, 5))
                elements.append(Paragraph(
                    "<b>{}</b>".format(detalle['nombre_empresa']),
                    ParagraphStyle(name='Normal', fontSize=8, leading=6, wordWrap='CJK', splitLongWords=True)
                ))
                elements.append(Spacer(1, 5))

                # Encabezado para los detalles simplificados
                data_encabezado = [[
                    Paragraph('<b>Cuenta Contable</b>', ParagraphStyle(name='Centered', alignment=1, fontSize=8)),
                    Paragraph('<b>Valor Unitario</b>', ParagraphStyle(name='Centered', alignment=1, fontSize=8)),
                    Paragraph('<b>Total</b>', ParagraphStyle(name='Centered', alignment=1, fontSize=8)),
                    Paragraph('<b>Concepto</b>', ParagraphStyle(name='Centered', alignment=1, fontSize=8))
                ]]

                # Crear tabla de encabezado
                table_encabezado = Table(data_encabezado, colWidths=[2.3 * inch, 1.0 * inch, 1.0 * inch, 3.9 * inch])
                table_encabezado.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ]))
                elements.append(table_encabezado)

                id_empresa_anterior = detalle['id_empresa']

            # Añadir detalles
            cuenta_detalle = "{}<br/><i>{}</i>".format(detalle['cuenta_contable'], detalle['descripcion_cuenta'])
            data.append([
                Paragraph(cuenta_detalle, style_normal),
                locale.format_string("%.2f", detalle['valor_u'], grouping=True),
                locale.format_string("%.2f", detalle['total'], grouping=True),
                Paragraph(detalle['concepto_detalle'], style_normal),
            ])

            total_valor_u_general += detalle['valor_u']
            total_total_general += detalle['total']

        # Última empresa
        if data:
            table = Table(data, colWidths=[2.3 * inch, 1.0 * inch, 1.0 * inch, 3.9 * inch])
            table.setStyle(TableStyle([
                ('ALIGN', (1, 0), (-2, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black)
            ]))
            elements.append(table)

        # Totales generales simplificados
        elements.append(Spacer(1, 12))
        totales_data = [[
            Paragraph("<b>TOTALES</b>", style_normal),
            locale.format_string("%.2f", total_valor_u_general, grouping=True),
            locale.format_string("%.2f", total_total_general, grouping=True),
            Paragraph('', style_normal)
        ]]

        totales_table = Table(totales_data, colWidths=[2.3 * inch, 1.0 * inch, 1.0 * inch, 3.9 * inch])
        totales_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black)
        ]))
        elements.append(KeepTogether([Spacer(1, 12), totales_table]))


        # Fase 1: calcular el número total de páginas
        elements_for_counting_pages = elements.copy()  # Hacer una copia de los elementos
        dummy_response = io.BytesIO()  # Usar un buffer en memoria

        # Crear un SimpleDocTemplate temporal solo para contar las páginas
        doc_for_counting_pages = SimpleDocTemplate(dummy_response, pagesize=letter, topMargin=0.2 * inch, bottomMargin=0.2 * inch)
        doc_for_counting_pages.build(elements_for_counting_pages)

        # Obtener la cantidad de páginas
        num_pages = doc_for_counting_pages.page  # Esto te debería dar el número de páginas.


        # --- Fase 2: Generar el PDF con el pie de página ---
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="reporte_pago.pdf"'

        # Crear el documento final para la respuesta
        doc = SimpleDocTemplate(response, pagesize=letter, topMargin=0.2 * inch, bottomMargin=0.2 * inch)
        doc.title = "Reporte de Solicitud de Gasto"


        def onFirstPage(canvas, doc):
            print('Primera página, página: {}'.format(num_pages))
            print('Primera página, página: {}'.format(doc.page))
            if num_pages <= doc.page:
                self.draw_footer(canvas, doc, encabezado, style_normal)

        def onLaterPages(canvas, doc):
            print('Página: {}'.format(num_pages))
            print('Página: {}'.format(doc.page))
            self.draw_footer(canvas, doc, encabezado, style_normal)

        # Generar el documento con el pie de página
        doc.build(elements, onFirstPage=onFirstPage, onLaterPages=onLaterPages)


        # Retornar la respuesta HTTP con el PDF
        return response










class GenerarReporteIngresosPDF(APIView):

    def get(self, request, id_gasto, *args, **kwargs):

        # Obtener encabezado y detalles mediante stored procedures
        encabezado = self.obtener_encabezado(id_gasto)
        detalles = self.obtener_detalles(id_gasto)

        return self.generar_pdf(encabezado, detalles)


    def obtener_encabezado(self, id_gasto):
        # Ejecutar el stored procedure para obtener el encabezado
        with connections['universal'].cursor() as cursor:
            cursor.callproc('VAIC_PDF_INGRESOS_HEADER', [id_gasto])
            encabezado_result = cursor.fetchone()

        # Mapa del resultado del procedimiento
        encabezado = {
            'empresa_nombre': encabezado_result[0],
            'tipo_solicitud': encabezado_result[1],
            'fecha_pago': encabezado_result[2],
            'tipo_docto': encabezado_result[3],
            'logo_url': "http://3.230.160.184:81/media/carbajal.jpg",
            'moneda': encabezado_result[4],
            'concepto': encabezado_result[5],
            'fecha_documento': encabezado_result[6],
            'usuario': encabezado_result[7]
        }
        return encabezado


    def obtener_detalles(self, id_gasto):
        # Ejecutar el stored procedure para obtener los detalles
        detalles = []
        with connections['universal'].cursor() as cursor:
            cursor.callproc('VAIC_PDF_INGRESOS_DETAILS', [id_gasto])
            detalles_result = cursor.fetchall()

        # Convertir los resultados en un diccionario
        for detalle in detalles_result:
            detalles.append({
                'cuenta_contable': detalle[0],
                'descripcion_cuenta': detalle[1],
                'valor_u': detalle[2],
                'sub_total': detalle[3],
                'isv': detalle[4],
                'ajuste': detalle[5],
                'total': detalle[6],
                'concepto_detalle': detalle[7],
                'id_empresa': detalle[8],  # Se agrega el ID de la empresa
                'nombre_empresa': detalle[9]  # Se agrega el nombre de la empresa
            })

        return detalles


    def draw_footer(self, canvas, doc, encabezado, style_normal):
        """
        Función para dibujar la firma en el pie de la última página.
        """
        canvas.saveState()

        # Posicionar la firma siempre en la parte inferior de la página
        width, height = letter
        firma_data = [
            [
                Paragraph("____________________________", style_normal),
                "",
                Paragraph("Usuario: {}".format(encabezado['usuario']), style_normal)
            ],
            [
                Paragraph("Autorizado por", style_normal),
                "",
                Paragraph("Fecha: {}".format(encabezado['fecha_documento']), style_normal)
            ]
        ]
        
        firma_table = Table(firma_data, colWidths=[4.0 * inch, 0.5 * inch, 3.0 * inch])
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Firma alineada a la izquierda
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Usuario y fecha alineados a la derecha
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))

        # Dibujar la tabla en la posición final de la página
        firma_table.wrapOn(canvas, width, height)
        firma_table.drawOn(canvas, 0.7 * inch, 1.5 * inch)

        canvas.restoreState()


    def draw_footer_last_page(self, canvas, doc, encabezado, style_normal):
        if doc.page == doc.page_count:  # Asegurarse de que es la última página
            self.draw_footer(canvas, doc, encabezado, style_normal)


    def generar_pdf(self, encabezado, detalles):
        # Lista para agregar elementos (contenido del PDF)
        elements = []

        # Estilos de texto
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(name='Title', fontSize=16, alignment=1)  # Empresa más grande
        style_subtitle = ParagraphStyle(name='Subtitle', fontSize=14, alignment=1)  # Título de la solicitud más pequeño
        style_normal = ParagraphStyle(name='Normal', fontSize=8, leading=12)

        # Crear una tabla para el logo y el encabezado de la empresa
        logo = Image(encabezado['logo_url'], 1 * inch, 1 * inch)  # Ajuste de tamaño del logo
        data_encabezado = [
            [logo, Paragraph("<b>{}</b>".format(encabezado['tipo_solicitud']), style_title)]
        ]

        table_encabezado = Table(data_encabezado, colWidths=[1.5 * inch, 6.5 * inch])  # Ajuste de los anchos de columna
        table_encabezado.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Centrar el texto de la empresa
            ('VALIGN', (0, 0), (1, 0), 'TOP')  # Alinear el logo con la parte superior
        ]))

        elements.append(table_encabezado)

        # Encabezado en formato de tabla para los detalles del documento
        data_encabezado_info = [
            [
                Paragraph("<b>Fecha de Doc:</b> {}".format(encabezado['fecha_documento']), style_normal),
                Paragraph("<b>Fecha de Pago:</b> {}".format(encabezado['fecha_pago']), style_normal),
                Paragraph("<b>Tipo Docto:</b> {}".format(encabezado['tipo_docto']), style_normal),
                Paragraph("<b>Moneda:</b> {}".format(encabezado['moneda']), style_normal),
            ]
        ]

        table_encabezado_info = Table(data_encabezado_info, colWidths=[2.0 * inch, 2.0 * inch, 2.0 * inch, 2.0 * inch])
        table_encabezado_info.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Alinear a la izquierda
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # Reducir el tamaño del texto
        ]))

        elements.append(table_encabezado_info)

        # Añadir una línea divisoria antes del encabezado de la tabla de detalles
        elements.append(Spacer(1, 6))
        elements.append(Table([['']], colWidths=[8 * inch]))

        # Inicializar los totales generales
        total_valor_u_general = 0
        total_sub_total_general = 0
        total_isv_general = 0
        total_total_general = 0

        # Inicializar id_empresa_anterior antes del bucle
        id_empresa_anterior = None  # Inicialmente no hay empresa anterior

        # Variable para guardar la empresa actual (opcional)
        empresa_actual = None
        empty_text = None

        # Inicializar la lista data para los detalles
        data = []

        # Preparar la tabla de detalles agrupados por empresa
        # Bucle por empresas (dentro del bucle principal de detalles)
        for detalle in detalles:
            # Cuando cambie de empresa, mostrar el nombre de la nueva empresa
            if id_empresa_anterior != detalle['id_empresa']:
                # Si ya hay detalles en 'data', crear una tabla con los detalles anteriores antes de cambiar de empresa
                if data:
                    table = Table(data, colWidths=[3 * inch, 0.6 * inch, 1.0 * inch, 2.7 * inch])
                    table.setStyle(TableStyle([
                        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # Alinear texto a la derecha para números
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),    # Alinear texto a la izquierda para la columna de cuenta contable
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),   # Alinear todo el contenido verticalmente arriba
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black)
                    ]))
                    elements.append(table)

                    # Vaciar `data` para los detalles de la nueva empresa
                    data = []

                # Insertar el nombre de la nueva empresa
                elements.append(Spacer(1, 15))
                elements.append(Paragraph("<b>{}</b>".format(detalle['nombre_empresa']), style_normal))
                elements.append(Spacer(1, 15))

                # Encabezado para los detalles de la nueva empresa
                data_encabezado = [
                    [
                        Paragraph('<b>Cuenta Contable</b>', ParagraphStyle(name='Centered', alignment=1, fontSize=8)),  # CENTER alignment
                        Paragraph('<b>Valor Unitario</b>', ParagraphStyle(name='Centered', alignment=1, fontSize=8)),
                        Paragraph('<b>Total</b>', ParagraphStyle(name='Centered', alignment=1, fontSize=8)),
                        Paragraph('<b>Concepto</b>', ParagraphStyle(name='Centered', alignment=1, fontSize=8)),
                    ]
                ]


                # Añadir el encabezado a los elementos
                table_encabezado = Table(data_encabezado, colWidths=[3 * inch, 0.6 * inch, 1.0 * inch, 2.7 * inch])
                table_encabezado.setStyle(TableStyle([
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Alinear encabezados al centro
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Línea debajo del encabezado
                ]))
                elements.append(table_encabezado)

                # Actualizar el ID de la empresa actual
                id_empresa_anterior = detalle['id_empresa']

            # Añadir los detalles de la empresa actual
            cuenta_detalle = "{}<br/><i>{}</i>".format(detalle['cuenta_contable'], detalle['descripcion_cuenta'])

            data.append([
                Paragraph(cuenta_detalle, ParagraphStyle(name='Normal', fontSize=6, wordWrap='CJK', splitLongWords=True)),  # Reducir fuente y ajustar texto
                locale.format_string("%.2f", detalle['valor_u'], grouping=True),
                locale.format_string("%.2f", detalle['total'], grouping=True),
                Paragraph(detalle['concepto_detalle'], ParagraphStyle(name='Normal', fontSize=6, wordWrap='CJK', splitLongWords=True))  # Reducir fuente y ajustar texto
            ])


            # Sumar los totales
            total_valor_u_general += detalle['valor_u']
            total_total_general += detalle['total']

        # Si quedan detalles sin agregar (para la última empresa), añadirlos a la tabla
        if data:
            table = Table(data, colWidths=[3 * inch, 0.6 * inch, 1.0 * inch, 2.7 * inch])
            table.setStyle(TableStyle([
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # Alinear texto a la derecha para números
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),    # Alinear texto a la izquierda para la columna de cuenta contable
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),   # Alinear todo el contenido verticalmente arriba
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black)
            ]))
            elements.append(table)
            

        # Añadir los totales generales al final
        elements.append(Spacer(1, 20))

        # Tabla de totales generales, con los mismos colWidths que la tabla de detalles
        totales_data = [
            [
                Paragraph("<b>TOTALES</b>", style_normal),
                locale.format_string("%.2f", total_valor_u_general, grouping=True),
                locale.format_string("%.2f", total_total_general, grouping=True),
                Paragraph('<b></b>', style_normal)
            ]
        ]

        # Crear la tabla de totales con los mismos colWidths
        totales_table = Table(totales_data, colWidths=[3 * inch, 0.6 * inch, 1.0 * inch, 2.7 * inch])
        totales_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # Alinear texto a la derecha para los números
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black)
        ]))

        # Añadir la tabla de totales al documento
        elements.append(totales_table)

        # Fase 1: calcular el número total de páginas
        elements_for_counting_pages = elements.copy()  # Hacer una copia de los elementos
        dummy_response = io.BytesIO()  # Usar un buffer en memoria

        # Crear un SimpleDocTemplate temporal solo para contar las páginas
        doc_for_counting_pages = SimpleDocTemplate(dummy_response, pagesize=letter, topMargin=0.2 * inch, bottomMargin=0.2 * inch)
        doc_for_counting_pages.build(elements_for_counting_pages)

        # Obtener la cantidad de páginas
        num_pages = doc_for_counting_pages.page  # Esto te debería dar el número de páginas.


        # --- Fase 2: Generar el PDF con el pie de página ---
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="reporte_solicitud_ingreso.pdf"'

        # Crear el documento final para la respuesta
        doc = SimpleDocTemplate(response, pagesize=letter, topMargin=0.2 * inch, bottomMargin=0.2 * inch)
        doc.title = "Reporte de Solicitud de Ingreso"

        def onFirstPage(canvas, doc):
            print('Primera página, página: {}'.format(num_pages))
            print('Primera página, página: {}'.format(doc.page))
            if num_pages <= doc.page:
                self.draw_footer(canvas, doc, encabezado, style_normal)

        def onLaterPages(canvas, doc):
            print('Página: {}'.format(num_pages))
            print('Página: {}'.format(doc.page))
            self.draw_footer(canvas, doc, encabezado, style_normal)

        # Generar el documento con el pie de página
        doc.build(elements, onFirstPage=onFirstPage, onLaterPages=onLaterPages)


        # Retornar la respuesta HTTP con el PDF
        return response









class GenerarPartidaContablePDF(APIView):
    def get(self, request, pk_partida, *args, **kwargs):
        encabezado = self.obtener_encabezado(pk_partida)
        detalles = self.obtener_detalles(pk_partida)
        return self.generar_pdf(encabezado, detalles)

    def obtener_encabezado(self, pk_partida):
        with connections['universal'].cursor() as cursor:
            cursor.callproc('CONTA_GET_ENCABEZADO_PARTIDA', [pk_partida])
            column_names = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()

        if not row:
            return {}

        row_dict = dict(zip(column_names, row))

        encabezado = {
            'npartida': row_dict.get('Npartida'),
            'sinopsis': row_dict.get('Sinopsis'),
            'fecha': row_dict.get('FechaPartida'),
            'balance': row_dict.get('Balance'),
            'creado_por': row_dict.get('creado_por'),
            'sucursal': row_dict.get('NombreSucursal'),
            'logo_url': "http://3.230.160.184:81/media/carbajal.jpg"
        }
        return encabezado


    def obtener_detalles(self, pk_partida):
        detalles = []
        with connections['universal'].cursor() as cursor:
            cursor.callproc('CONTA_GET_DETALLE_PARTIDA', [pk_partida])
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

        for row in rows:
            row_dict = dict(zip(column_names, row))
            detalles.append({
                'codigo': row_dict.get('CodigoCuenta'),
                'concepto': row_dict.get('ConceptoCuenta'),
                'sinopsis': row_dict.get('Sinopsis'),
                'debe': row_dict.get('Debe'),
                'haber': row_dict.get('Haber'),
            })

        return detalles


    def generar_pdf(self, encabezado, detalles):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="partida_contable.pdf"'

        doc = SimpleDocTemplate(response, pagesize=letter,
                                topMargin=0.4 * inch, bottomMargin=0.4 * inch)

        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(name='Title', fontSize=14, alignment=1, textColor=colors.HexColor('#006400'))
        style_header = ParagraphStyle(name='Header', fontSize=10, alignment=0, textColor=colors.black)
        style_normal = ParagraphStyle(name='Normal', fontSize=9)
        style_right_bold = ParagraphStyle(name='RightBold', parent=styles['Normal'], alignment=2, fontSize=9, fontName='Helvetica-Bold')


        elements = []

        # Logo y título
        logo = Image(encabezado['logo_url'], width=1 * inch, height=1 * inch)
        title_data = [
            [logo],
        ]
        table_title = Table(title_data, colWidths=[1.2 * inch])
        elements.append(table_title)

        elements.append(Spacer(1, 8))

        # Encabezado de partida
        encabezado_data = [
            ['N° Partida:', encabezado['npartida'], 'Fecha:', str(encabezado['fecha'])],
            ['Sinopsis:', encabezado['sinopsis'], '', ''],
            ['Balance:', f"L {locale.format_string('%.2f', encabezado['balance'], grouping=True)}", 'Usuario:', encabezado['creado_por']],
            ['Sucursal:', encabezado['sucursal'], '', ''],
        ]
        table_info = Table(encabezado_data, colWidths=[1.2 * inch, 3.0 * inch, 1.2 * inch, 2.6 * inch])
        table_info.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(table_info)
        elements.append(Spacer(1, 8))
        
        # Tabla de detalles
        data = [[
            Paragraph('<b>Código</b>', style_normal),
            Paragraph('<b>Concepto</b>', style_normal),
            Paragraph('<b>Debe</b>', style_normal),
            Paragraph('<b>Haber</b>', style_normal),
        ]]

        total_debe = 0
        total_haber = 0

        for detalle in detalles:
            data.append([
                detalle['codigo'],
                detalle['concepto'],
                locale.format_string('%.2f', detalle['debe'], grouping=True),
                locale.format_string('%.2f', detalle['haber'], grouping=True),
            ])
            total_debe += detalle['debe'] or 0
            total_haber += detalle['haber'] or 0

        data.append([
            Paragraph('<b>TOTALES</b>', style_normal),
            '',
            Paragraph('<b>{}</b>'.format(locale.format_string('%.2f', total_debe, grouping=True)), style_right_bold),
            Paragraph('<b>{}</b>'.format(locale.format_string('%.2f', total_haber, grouping=True)), style_right_bold),
        ])

        table_detalles = Table(data, colWidths=[1.4 * inch, 3.8 * inch, 1.2 * inch, 1.2 * inch])
        table_detalles.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0f0ff')),
            ('ALIGN', (2, 1), (-1, -2), 'RIGHT'),  # Datos normales
            ('ALIGN', (2, -1), (-1, -1), 'RIGHT'),  # Totales
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        elements.append(table_detalles)
        elements.append(Spacer(1, 10))

        # Tabla de firma con espacio, línea y texto centrado
        firma_data = [
            ['', '', ''],
            ['_________________________', '', '_________________________'],
            ['Realizada Por', '', 'Aprobado Por']
        ]

        table_firma = Table(firma_data, colWidths=[3.0 * inch, 1 * inch, 3.0 * inch], rowHeights=[20, 12, 14])
        table_firma.setStyle(TableStyle([
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),  # Línea centrada
            ('ALIGN', (0, 2), (-1, 2), 'CENTER'),  # Texto centrado
            ('FONTSIZE', (0, 2), (-1, 2), 9),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 0),
            ('TOPPADDING', (0, 2), (-1, 2), 0),
        ]))

        # Insertar espacio flexible antes de las firmas
        elements.append(Spacer(1, 50))  # puedes ir ajustando esto según el contenido
        elements.append(KeepTogether([table_firma]))

        doc.build(elements)
        return response
    







class GenerarVoucherPDF(APIView):
    def dictfetchall(cursor):
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get(self, request, id_planilla, *args, **kwargs):
        # Obtener encabezado de la empresa y detalles simulados
        encabezado_empresa = self.obtener_encabezado_empresa(id_planilla)
        empleados = self.obtener_empleados(id_planilla)
        detalles = self.obtener_detalles(id_planilla)

        # Generar el PDF
        return self.generar_pdf(request, encabezado_empresa, empleados, detalles, id_planilla)


    def obtener_encabezado_empresa(self, id_planilla):
        # Información simulada del encabezado de la empresa
        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_HEADER_EMPRESA_PLANILLA', [id_planilla])
            encabezado_result = cursor.fetchone()
            print(encabezado_result)
        
        if encabezado_result is None:
            raise ValueError("No se encontraron resultados para la planilla con ID {}".format(id_planilla))
        
        encabezado = {
            'empresa_nombre': encabezado_result[0],
            'logo_url': "http://3.230.160.184:81/media/carbajal.png"
        }
        return encabezado

    def obtener_empleados(self, id_planilla):
        empleados = []
        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_GET_DETALLES_PLANILLAS_v20251010', [id_planilla, 1])
            rows = dictfetchall(cursor)  # Usa fetchall para múltiples filas
            print('')
            print('EMPLEADOS {}'.format(rows))

            if not rows:
                # Manejar el caso donde no hay resultados
                print("No se encontraron resultados para el id_planilla:", id_planilla)
                return empleados

            # Procesa cada fila de resultados
            for e in rows:
                empleados.append({
                    'codigo_planilla': str(e.get('id_planilla', '')),
                    'id_empleado': e.get('id_empleado', 0),
                    'nombre_completo': e.get('nombre_completo', ''),
                    'salario_base': float(e.get('salario_base', 0)),
                    'codigo_empleado': e.get('codigo_empleado', ''),
                    'dias_trabajados': e.get('dias_trabajados', 0),
                    'tipo_planilla': e.get('tipo_planilla', ''),
                    'fecha_planilla': e.get('fecha_planilla', ''),
                })

        return empleados


    def obtener_detalles(self, id_planilla):
        detalles = []
        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_GET_DETALLES_PLANILLAS_v20251010', [id_planilla, 1])
            rows = dictfetchall(cursor)  # Usa fetchall para múltiples filas
            print('')
            print('DETALLES SALARIOS {}'.format(rows))

            if not rows:
                # Manejar el caso donde no hay resultados
                print("No se encontraron detalles para el id_planilla:", id_planilla)
                return detalles

            # Procesa cada fila de resultados
            for d in rows:
                detalles.append({
                    'id_empleado': d.get('id_empleado', 0),
                    'concepto': 'Salario',
                    'valor': float(d.get('salario_calculado', 0)),
                    'tipo': 'beneficio',
                })
        # Confirmar la transacción para la primera llamada
        connections['universal'].commit()

        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_GET_DETALLES_PLANILLAS_v20251010', [id_planilla, 2])
            rows = dictfetchall(cursor)  # Usa fetchall para múltiples filas
            print('')
            print('DETALLES DEDUCCIONES COMISIONES {}'.format(rows))

            if not rows:
                # Manejar el caso donde no hay resultados
                print("No se encontraron detalles para el id_planilla:", id_planilla)
                return detalles

            # Procesa cada fila de resultados
            for d in rows:
                detalles.append({
                    'id_empleado': d.get('id_empleado', 0),
                    'concepto': capitalizar_frase(d.get('descripcion_tipo', '')),
                    'valor': float(d.get('monto', 0)),
                    'tipo': d.get('tipo_detalle', ''),
                    'codigo_cuenta': d.get('codigo_cuenta', ''),
                    'nombre_cuenta': d.get('nombre_cuenta', ''),
                })
        # Confirmar la transacción para la segunda llamada (si modifica datos)
        connections['universal'].commit()
        
        return detalles


    def generar_pdf(self, request, encabezado_empresa, empleados, detalles, id_planilla):
        id = request.session.get('user_id', '')
    
        if id == '':
            return HttpResponseRedirect(reverse('login'))
        else:
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="voucher_planilla.pdf"'

            # Tamaño de la página: Media carta (8.5 x 5.5 pulgadas)
            page_width = 8.5 * inch
            page_height = 5.5 * inch
            doc = SimpleDocTemplate(
                response,
                pagesize=(page_width, page_height),
                topMargin=0,
                bottomMargin=0,
                leftMargin=0,
                rightMargin=0,
            )
            doc.title = "Reporte de Comprobantes de Pagos"

            fecha_hora_actual = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")
            elements = []  # Elementos del PDF

            # Estilos
            styles = getSampleStyleSheet()
            style_title = ParagraphStyle(name="Title", fontSize=10, alignment=1)
            style_normal_center = ParagraphStyle(name="Title", fontSize=7, alignment=1)
            style_normal_right = ParagraphStyle(name="Title", fontSize=7, alignment=2)
            style_normal = ParagraphStyle(name="Normal", fontSize=7, leading=10)

            # Crear una página por cada empleado
            for empleado in empleados:

                # Encabezado de la empresa
                logo = Image(encabezado_empresa['logo_url'], 2 * inch, 0.5 * inch)  # Ajuste de tamaño del logo

                # Ajustar la separación entre líneas
                style_title_compacto = ParagraphStyle(name='TitleCompact', fontSize=10, alignment=1, spaceAfter=0, leading=12)

                data_encabezado = [
                    [
                        logo,
                        Paragraph("<b>{}</b><br/><br/><b>Comprobante de Pago</b>".format(encabezado_empresa['empresa_nombre']), style_title_compacto)
                    ]
                ]

                table_encabezado = Table(data_encabezado, colWidths=[2 * inch, 6 * inch])  # Ajuste de los anchos de columna
                table_encabezado.setStyle(TableStyle([
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # Centrar el texto del nombre y comprobante
                    ('VALIGN', (0, 0), (1, 0), 'TOP'),    # Alinear el logo y el texto con la parte superior
                    ('LEFTPADDING', (0, 0), (0, 0), 0),   # Sin padding a la izquierda
                    ('RIGHTPADDING', (1, 0), (1, 0), 0),  # Sin padding a la derecha
                    ('TOPPADDING', (0, 0), (-1, -1), 0),  # Sin padding superior
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0)  # Sin padding inferior
                ]))

                elements.append(table_encabezado)
                elements.append(Spacer(1, 10))

                data_encabezado_info = [
                    [
                        Paragraph("<b>Código Planilla:</b> {}".format(empleado['codigo_planilla']), style_normal),
                        Paragraph("<b>Fecha Planilla:</b> {}".format(empleado['fecha_planilla']), style_normal),
                        Paragraph("<b>Tipo Planilla:</b> {}".format(empleado['tipo_planilla']), style_normal),
                        Paragraph("<b>Salario Base:</b> {}".format(locale.format_string("%.2f", empleado['salario_base'], grouping=True)), style_normal),
                    ],
                    [
                        Paragraph("<b>Empleado:</b> {}".format(empleado['nombre_completo']), style_normal),
                        Paragraph("<b>Codigo Empleado:</b> {}".format(empleado['codigo_empleado']), style_normal),
                        Paragraph("<b>Dias Trabajados:</b> {}".format(empleado['dias_trabajados']), style_normal),
                    ],
                ]

                table_encabezado_info = Table(data_encabezado_info, colWidths=[2.0 * inch, 2.0 * inch, 2.0 * inch, 2.0 * inch])
                table_encabezado_info.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Alinear a la izquierda
                    ('FONTSIZE', (0, 0), (-1, -1), 8),  # Reducir el tamaño del texto
                ]))

                elements.append(table_encabezado_info)

                # Tabla de beneficios
                data_beneficios = [['Beneficios', 'Valor']]
                total_beneficios = 0
                for detalle in detalles:
                    if detalle['id_empleado'] == empleado['id_empleado'] and detalle['tipo'] == "beneficio":
                        data_beneficios.append([detalle['concepto'], "L " + "{}".format(locale.format_string("%.2f", detalle['valor'], grouping=True))])
                        total_beneficios += detalle['valor']

                # Añadir fila para total de beneficios
                data_beneficios.append(['Total Beneficios', "L " + "{}".format(locale.format_string("%.2f", total_beneficios, grouping=True))])

                table_beneficios = Table(data_beneficios, colWidths=[3.0 * inch, 2.5 * inch])
                table_beneficios.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('BACKGROUND', (-2, -1), (-1, -1), colors.lightgrey),  # Resaltar fila del total
                ]))
                elements.append(table_beneficios)

                # Tabla de deducciones
                data_deducciones = [['Deducciones', 'Valor']]
                total_deducciones = 0
                for detalle in detalles:
                    if detalle['id_empleado'] == empleado['id_empleado'] and detalle['tipo'] == "deduccion":
                        data_deducciones.append([detalle['concepto'], "L " + "{}".format(locale.format_string("%.2f", detalle['valor'], grouping=True))])
                        total_deducciones += detalle['valor']

                # Calcular el total neto
                total_neto = total_beneficios - total_deducciones

                # Añadir fila para total de deducciones
                data_deducciones.append(['Total Deducciones', "L " + "{}".format(locale.format_string("%.2f", total_deducciones, grouping=True))])

                # Añadir fila para total neto a pagar
                data_deducciones.append(['Total Neto a Pagar', "L " + "{}".format(locale.format_string("%.2f", total_neto, grouping=True))])

                table_deducciones = Table(data_deducciones, colWidths=[3.0 * inch, 2.5 * inch])
                table_deducciones.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('BACKGROUND', (-2, -2), (-1, -2), colors.lightgrey),  # Resaltar Total Deducciones
                    ('BACKGROUND', (-2, -1), (-1, -1), colors.lightgrey),  # Resaltar Total Neto
                ]))
                elements.append(table_deducciones)
                elements.append(Spacer(1, 10))

                # Firma final
                firma_data = [
                    [
                        Paragraph("Fecha Impreso: {}".format(fecha_hora_actual), style_normal),  # Reemplaza 'NOW' por la fecha real
                        "",
                        Paragraph("____________________________", style_normal),
                    ],
                    [
                        Paragraph("Usuario: {} | Página {} de {}".format(request.session.get('userName', ''), empleados.index(empleado) + 1, len(empleados)), style_normal),
                        "",
                        Paragraph("Firma del Empleado", style_normal),
                    ]
                ]

                firma_table = Table(firma_data, colWidths=[4.0 * inch, 2.0 * inch, 2.0 * inch])
                firma_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Firma alineada a la izquierda
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Usuario y fecha alineados a la derecha
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                ]))

                # Agregar la tabla al flujo de elementos
                elements.append(firma_table)

                # Nueva página para el siguiente empleado
                elements.append(PageBreak())

            # Construir el PDF
            doc.build(elements)
            return response
