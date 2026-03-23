import base64
import csv
import hashlib
import json
import logging
import os
import pandas as pd
import pyodbc
import pymssql
import pymysql
import requests
import subprocess
import tempfile
import time
import xlrd
import jwt
from decimal import Decimal
import gzip
from io import BytesIO
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, numbers
from openpyxl.utils import get_column_letter
from datetime import date, datetime, timedelta
import decimal
from django.db.utils import OperationalError
from django.views.decorators.http import require_POST
from calendar import monthrange
from urllib.parse import quote_plus
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import connections, transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from CWS.views.LoginView import EXPIRATION_MINUTES, SECRET_KEY


def dictfetchall(cursor):
    """Devuelve todas las filas de un cursor como una lista de diccionarios, convirtiendo bits a 0/1."""
    columns = [col[0] for col in cursor.description]
    return [
        dict(
            zip(
                columns,
                [
                    ord(val) if isinstance(val, bytes) and len(val) == 1 else val
                    for val in row
                ],
            )
        )
        for row in cursor.fetchall()
    ]


def _callproc_fetchall(conn, proc_name, params):
    with conn.cursor() as cursor:
        cursor.callproc(proc_name, params)
        rows = cursor.fetchall()  # primer result set (si hay)
        # Consumir cualquier result set restante
        while cursor.nextset():
            try:
                # Si el siguiente result set tiene filas, lás consúmelas para vaciar el buffer
                cursor.fetchall()
            except Exception:
                pass
        return rows


def drain_cursor(cursor):
    """Drena todos los posibles result sets de un cursor después de un callproc."""
    try:
        if cursor.description:
            _ = cursor.fetchall()
    except Exception:
        pass
    try:
        while cursor.nextset():
            pass
    except Exception:
        pass


def chunks(lista, tamano):
    for i in range(0, len(lista), tamano):
        yield lista[i : i + tamano]


def _execute_sp(connection_name, sp_name, params=None, image_fields=None):
    """
    Ejecuta un stored procedure y devuelve lista de dicts.
    - Convierte BIT (bytes) a int
    - Convierte campos de imagen a base64 si se especifican
    """
    data = []
    params = params or []
    image_fields = image_fields or []

    try:
        conn = connections[connection_name]

        with conn.cursor() as cursor:
            cursor.callproc(sp_name, params)

            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            for row in rows:
                row_dict = {}

                for col, val in zip(column_names, row):

                    # Conversión BIT (MySQL devuelve bytes)
                    if isinstance(val, (bytes, bytearray)):
                        if col in image_fields:
                            # Campo imagen
                            row_dict[col] = base64.b64encode(val).decode("utf-8")
                        else:
                            # Campo BIT
                            row_dict[col] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[col] = val if val is not None else ""

                data.append(row_dict)

    except Exception as e:
        print("ERROR {}: {}".format(sp_name, e))
        return []

    return data


def conta_get_partidas_hermanas():
    hermanas_list = []

    try:
        udcConn = connections["universal"]
        with udcConn.cursor() as cursor:
            cursor.callproc("CONTA_GET_PARTIDAS_HERMANAS", [1])
            column_names = [desc[0] for desc in cursor.description]
            hermanas_list = [
                dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
            ]

    except Exception as e:
        hermanas_list = []

    return hermanas_list


def getModulos():
    modulos_list = []
    try:
        with connections["global_nube"].cursor() as cursor:
            cursor.execute("CALL GS_LIST_MODULOS()")
            modulos = cursor.fetchall()
            modulos_list = [
                {"id": modulo[3], "modulo": modulo[1]} for modulo in modulos
            ]

    except Exception as e:
        modulos_list = ""
    return modulos_list


def getUsers():
    usersList = []
    try:
        with connections["global_nube"].cursor() as cursor:
            cursor.execute("CALL GS_GET_ALL_USUARIOS()")
            users = cursor.fetchall()
            usersList = [{"PkUsuario": user[0], "Nombre": user[1]} for user in users]

    except Exception as e:
        usersList = ""
    return usersList


def obtener_empresas():
    empresas_list = []
    try:
        with connections["global_nube"].cursor() as cursor:
            cursor.execute("CALL TH_GET_EMPRESAS()")
            empresas = cursor.fetchall()
            empresas_list = [
                {"id": empresa[1], "nombre": empresa[0]} for empresa in empresas
            ]

    except Exception as e:
        empresas_list = ""
    return empresas_list


def obtener_empresas_usuario(request):
    usuario_id = request.session.get("user_id", 0)
    admin_it = (
        1
        if (
            request.session.get("bancarioAdminIT", 0) == 1
            or request.session.get("contabilidadAdminIT", 0) == 1
        )
        else 0
    )
    return _execute_sp(
        connection_name="global_nube",
        sp_name="GS_GET_EMPRESAS_USUARIO",
        params=[usuario_id, admin_it],
    )


def obtener_sucursales_usuario(request, empresa):
    usuario_id = request.session.get("user_id", 0)
    admin_it = (
        1
        if (
            request.session.get("bancarioAdminIT", 0) == 1
            or request.session.get("contabilidadAdminIT", 0) == 1
        )
        else 0
    )
    return _execute_sp(
        connection_name="global_nube",
        sp_name="GS_GET_SUCURSALES_USUARIO",
        params=[empresa, usuario_id, admin_it],
    )


def get_bancos():
    return _execute_sp(
        connection_name="bankConn",
        sp_name="BNK_GET_BANCOS",
        image_fields=["ImagenBanco"],
    )


def get_estados_movimientos():
    return _execute_sp(connection_name="bankConn", sp_name="BK_GET_CAT_ESTADOS")


def get_sucursales_x_empresa(empresa):
    return _execute_sp(
        connection_name="global_nube",
        sp_name="GS_GET_SUCURSALES_X_EMPRESA",
        params=[empresa],
    )


def get_clientes():
    return _execute_sp(connection_name="super", sp_name="BK_GET_CLIENTES")


def get_procedencias(empresa=0):
    return _execute_sp(
        connection_name="bankConn", sp_name="BK_GET_PROCEDENCIAS", params=[empresa]
    )


def get_destinos(empresa=0):
    return _execute_sp(
        connection_name="bankConn", sp_name="BK_GET_DESTINOS", params=[empresa]
    )


def get_procedencias_usuario(empresa=0, usuario=0, adminIT=0):
    return _execute_sp(
        connection_name="bankConn",
        sp_name="BK_GET_PROCEDENCIAS_USUARIO",
        params=[empresa, usuario, adminIT],
    )


def get_destinos_usuario(empresa=0, usuario=0, adminIT=0):
    return _execute_sp(
        connection_name="bankConn",
        sp_name="BK_GET_DESTINOS_USUARIO",
        params=[empresa, usuario, adminIT],
    )


def get_tipos_documentos():
    return _execute_sp(connection_name="bankConn", sp_name="BK_GET_TIPOS_DOCUMENTOS")


def get_acreedores():
    return _execute_sp(connection_name="bankConn", sp_name="BK_GET_ACREEDORES")


def get_proveedores():
    return _execute_sp(connection_name="bankConn", sp_name="BK_GET_PROVEEDORES")


def get_sucursales(empresa=0):
    return _execute_sp(
        connection_name="global_nube",
        sp_name="GS_GET_SUCURSALES_X_EMPRESA",
        params=[empresa],
    )


def get_tarjetas_credito(empresa=0):
    return _execute_sp(
        connection_name="bankConn", sp_name="BK_GET_TARJETAS_CREDITO", params=[empresa]
    )


def calcular_tasa_seguridad(request):

    try:
        fk_tipo_calculo = int(request.POST.get("fkTipoCalculo", 0))
        valor_movimiento = Decimal(request.POST.get("valorMovimiento", "0"))
        moneda = request.POST.get("moneda", "")
        valor_en_lps = Decimal(request.POST.get("valorEnLps", "0"))
        fecha = request.POST.get("fecha")

        if valor_movimiento <= 0:
            return JsonResponse({"success": True, "tasa_seguridad": 0})

        with connections["contable"].cursor() as cursor:

            # ===== Obtener Tasa Cambio =====
            cursor.execute("SELECT fn_getasacambio(%s)", [fecha])
            tasa_cambio = Decimal(cursor.fetchone()[0] or 0)

            # ===== Obtener Tasa Compra =====
            cursor.execute("SELECT fn_getasacompra(%s)", [fecha])
            tasa_compra = Decimal(cursor.fetchone()[0] or 0)

        tasa_seguridad = Decimal("0")

        # ===========================
        # ===== DÓLARES ============
        # ===========================

        if moneda == "Dolares":

            if fk_tipo_calculo == 1:
                tasa_seguridad = (
                    valor_movimiento * tasa_cambio * valor_en_lps
                ) / tasa_cambio

            elif fk_tipo_calculo == 2:
                valor_ts = valor_movimiento * tasa_cambio
                bloques = math.floor(valor_ts / 1000)
                if valor_ts % 1000 > 0:
                    bloques += 1
                tasa_seguridad = (bloques * valor_en_lps) / tasa_cambio

            elif fk_tipo_calculo == 3:
                valor_lps = valor_movimiento * tasa_compra
                bloques = math.floor(valor_lps / 1000)
                if valor_lps % 1000 > 0:
                    bloques += 1
                tasa_seguridad = (bloques * valor_en_lps) / tasa_compra

            elif fk_tipo_calculo == 4:
                valor_lps = valor_movimiento * tasa_compra
                bloques = math.floor(valor_lps / 1000)
                if valor_lps % 1000 > 0:
                    bloques += 1
                tasa_seguridad = (bloques * valor_en_lps) / tasa_cambio

        # ===========================
        # ===== LEMPIRAS ===========
        # ===========================

        elif moneda == "Lempiras":

            if fk_tipo_calculo == 1:
                tasa_seguridad = valor_movimiento * valor_en_lps

            elif fk_tipo_calculo == 2:
                bloques = math.floor(valor_movimiento / 1000)
                if valor_movimiento % 1000 > 0:
                    bloques += 1
                tasa_seguridad = bloques * valor_en_lps

            elif fk_tipo_calculo in [3, 4]:
                tasa_seguridad = valor_movimiento * valor_en_lps

        return JsonResponse(
            {
                "success": True,
                "tasa_seguridad": round(tasa_seguridad, 2),
                "tasa_cambio": tasa_cambio,
                "tasa_compra": tasa_compra,
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def calcular_tasa_seguridad_multi(request):

    if request.method != "POST":
        return JsonResponse({"success": False, "msg": "Método no permitido"})

    try:
        fkTipoCalculo = int(request.POST.get("fkTipoCalculo", 0) or 0)
        moneda = (request.POST.get("moneda", "") or "").strip()
        fecha = (request.POST.get("fecha", "") or "").strip()

        valorEnLps = request.POST.get("valorEnLps", "0") or "0"
        valorEnLps = Decimal(str(valorEnLps).replace(",", ""))

        items_raw = request.POST.get("items", "[]") or "[]"
        items = json.loads(items_raw)

        if fkTipoCalculo <= 0 or not fecha or moneda not in ["Lempiras", "Dolares"]:
            return JsonResponse({"success": False, "msg": "Parámetros inválidos"})

        # ===== tasas del día (1 sola vez) =====
        with connections["contable"].cursor() as cursor:
            cursor.execute("select fn_getasacambio(%s)", [fecha])
            row = cursor.fetchone()
            tasa_cambio = Decimal(str(row[0] or 0)) if row else Decimal("0")

            cursor.execute("select fn_getasacompra(%s)", [fecha])
            row = cursor.fetchone()
            tasa_compra = Decimal(str(row[0] or 0)) if row else Decimal("0")

        def _ceil_div_1000(valor):
            # retorna ceil(valor/1000) usando enteros (VB hacía CLng y Mod)
            v = int(valor)
            q = v // 1000
            r = v % 1000
            if r > 0:
                q += 1
            return Decimal(q)

        def _get_tasa_seg(
            fkTipoCalculo, valorMovimiento, tasaCambio, tasaCompra, moneda, valorEnLps
        ):
            # replica VB (GetTasaSeg) completo
            if fkTipoCalculo == 1 and moneda == "Dolares":
                # (ValorMovimiento * _TasaCambio * _ValorEnLps) / _TasaCambio
                # se simplifica a ValorMovimiento * _ValorEnLps, pero lo dejamos equivalente:
                if tasaCambio == 0:
                    return Decimal("0")
                return (valorMovimiento * tasaCambio * valorEnLps) / tasaCambio

            elif fkTipoCalculo == 2 and moneda == "Dolares":
                # por cada mil o fracción (sobre Lps usando tasaCambio, y luego / tasaCambio)
                if tasaCambio == 0:
                    return Decimal("0")
                valor_ts = valorMovimiento * tasaCambio
                valorp = _ceil_div_1000(valor_ts)
                return (valorp * valorEnLps) / tasaCambio

            elif fkTipoCalculo == 3 and moneda == "Dolares":
                # 0.10 por cada L1000 o fracción dividido por TasaCompra
                if tasaCompra == 0:
                    return Decimal("0")
                valor_lps = valorMovimiento * tasaCompra
                valorp = _ceil_div_1000(valor_lps)
                return (valorp * valorEnLps) / tasaCompra

            elif fkTipoCalculo == 4 and moneda == "Dolares":
                # 2 por cada L1000 o fracción dividido por TasaCambio (VB usa valor_lps con tasaCompra)
                if tasaCambio == 0:
                    return Decimal("0")
                valor_lps = (
                    valorMovimiento * tasa_compra
                )  # igual que VB (ValorMovimiento * _TasaCompra)
                valorp = _ceil_div_1000(valor_lps)
                return (valorp * valorEnLps) / tasaCambio

            elif fkTipoCalculo == 1 and moneda == "Lempiras":
                return valorMovimiento * valorEnLps

            elif fkTipoCalculo == 2 and moneda == "Lempiras":
                valorp = _ceil_div_1000(valorMovimiento)
                return valorp * valorEnLps

            elif fkTipoCalculo == 3 and moneda == "Lempiras":
                return valorMovimiento * valorEnLps

            elif fkTipoCalculo == 4 and moneda == "Lempiras":
                return valorMovimiento * valorEnLps

            return Decimal("0")

        data_out = []

        for it in items:
            entidad_id = int(it.get("entidad_id", 0) or 0)
            total = Decimal(str(it.get("total", 0) or 0))

            entidad_txt = (it.get("entidad_txt", "") or "").strip()
            cod = (it.get("cod", "") or "").strip()
            es_acreedor = int(it.get("es_acreedor", 0) or 0)

            if entidad_id <= 0 or total <= 0:
                continue

            # 👇 Aquí tu regla: el total viene en Lps por proveedor
            # Entonces valorMovimiento para cálculo = total (Lps)
            # Si la cuenta está en dólares, igual nosotros calculamos con la moneda que manda la cuenta.
            tasa_seg = _get_tasa_seg(
                fkTipoCalculo=fkTipoCalculo,
                valorMovimiento=total,
                tasaCambio=tasa_cambio,
                tasaCompra=tasa_compra,
                moneda=moneda,
                valorEnLps=2,
            )

            # 2 decimales
            tasa_seg = tasa_seg.quantize(Decimal("0.01"))

            data_out.append(
                {
                    "entidad_id": entidad_id,
                    "entidad_txt": entidad_txt,
                    "cod": cod,
                    "es_acreedor": es_acreedor,
                    "total": float(total),
                    "tasa_seguridad": float(tasa_seg),
                }
            )

        return JsonResponse({"success": True, "data": data_out})

    except Exception as e:
        return JsonResponse({"success": False, "msg": str(e)})


def getDate1():
    return datetime.now().replace(day=1).strftime("%Y-%m-%d")


def getYesterday():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def getActualDate():
    return datetime.now().strftime("%Y-%m-%d")
