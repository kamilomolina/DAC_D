from django.http import HttpResponse, HttpResponseRedirect
from django.db import connections
from django.http import JsonResponse
from django.conf import settings
import requests
import datetime
import pandas as pd
import time
import hashlib
import os
import subprocess
import traceback
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from django.views.decorators.csrf import csrf_exempt
import json
import base64
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, HttpResponseRedirect
import xlrd
from datetime import date, datetime, timedelta
from django.http import JsonResponse, Http404
from django.urls import reverse
import csv
import tempfile
import pyodbc
import pymssql
from django.db import transaction
import calendar
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .utilsContable import getUsers


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


def getEmpresas():
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


def getFormatos():
    formatosList = []
    try:
        with connections["universal"].cursor() as cursor:
            cursor.execute("CALL VAIC_LIST_FORMATOS()")
            formatos = cursor.fetchall()
            formatosList = [
                {"id_formato": formato[0], "formato": formato[1]}
                for formato in formatos
            ]

    except Exception as e:
        formatosList = ""
    return formatosList


def getCuentasAnaliticas():
    cuentasList = []
    try:
        with connections["universal"].cursor() as cursor:
            cursor.execute("CALL VAIC_LIST_CUENTAS_ANALITICAS()")
            cuentas = cursor.fetchall()
            cuentasList = [
                {"id_cuenta_analitica": cuenta[0], "descripcion_cuenta": cuenta[3]}
                for cuenta in cuentas
            ]

    except Exception as e:
        cuentasList = ""
    return cuentasList


def getDepartametos():
    deptosList = []
    try:
        with connections["universal"].cursor() as cursor:
            cursor.execute("CALL VAIC_GetAll_Departamentos()")
            deptos = cursor.fetchall()
            deptosList = [
                {
                    "id_departamento": depto[0],
                    "nombre_departamento": depto[1],
                    "nombre_sucursal": depto[2],
                }
                for depto in deptos
            ]

    except Exception as e:
        deptosList = ""
    return deptosList


def getCentrosGestion():
    centrosData = []
    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_LIST_CENTROS_NOT_CERRADOS_X_PERIODO", [0, 0])
            column_names = [desc[0] for desc in cursor.description]
            centrosData = [
                dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
            ]

    except Exception as e:
        centrosData = []

    return centrosData


""" TEMPLATES """


def ctrl_centros(request):
    user_id = request.session.get("user_id", "")

    acceso13049 = int(request.session.get("13049", 0))
    acceso13050 = int(request.session.get("13050", 0))
    autorizaRechazaVAIC = int(request.session.get("13052", 0))
    adminIT = int(request.session.get("ctrlGestionAdminIT", 0))

    print(dict(request.session))

    if user_id == "":

        return HttpResponseRedirect(reverse("login"))

    elif acceso13049 == 1 or acceso13050 == 1 or adminIT == 1:

        fecha_actual = datetime.now()
        varMonth = fecha_actual.strftime("%m")
        varAnio = fecha_actual.strftime("%Y")

        # Accesos personalizados para centros
        permisos_control_gestion = {
            "acceso_crear_centros": "13055",
            "cierre_mensualVAIC": "13051",
        }

        # Construir accesos a partir de la sesión
        accesos_context = {
            nombre: request.session.get(codigo, 0)
            for nombre, codigo in permisos_control_gestion.items()
        }

        # Agregar también si es admin IT contable
        accesos_context["adminIT"] = request.session.get("ctrlGestionAdminIT", 0)

        context = {
            "empresasData": getEmpresas(),
            "usersData": getUsers(),
            "formatoData": getFormatos(),
            "cuentasData": getCuentasAnaliticas(),
            "deptosData": getDepartametos(),
            "varMonth": varMonth,
            "varAnio": varAnio,
        }
        context.update(accesos_context)

        return render(request, "control_gestion/centros.html", context)

    else:

        return HttpResponseRedirect(reverse("panel_contabilidad"))


def ctrl_gestion_centro(request, centro_id, mes, anio):
    user_id = request.session.get("user_id", 0)
    userName = request.session.get("userName", "")

    acceso13049 = int(request.session.get("13049", 0))
    acceso13050 = int(request.session.get("13050", 0))
    autorizaRechazaVAIC = int(request.session.get("13052", 0))
    gestionAjustesPresupuestoCuentas = int(request.session.get("13084", 0))
    adminIT = int(request.session.get("ctrlGestionAdminIT", 0))

    formato = 1
    aplica_programacion_rutas = 0

    if user_id == "":

        return HttpResponseRedirect(reverse("login"))

    elif acceso13049 == 1 or acceso13050 == 1 or adminIT == 1:

        # Accesos personalizados para centros
        permisos_control_gestion = {
            "acceso_crear_centros": "13055",
            "cierre_mensualVAIC": "13051",
        }

        # Construir accesos a partir de la sesión
        accesos_context = {
            nombre: request.session.get(codigo, 0)
            for nombre, codigo in permisos_control_gestion.items()
        }

        # Agregar también si es admin IT contable
        accesos_context["adminIT"] = request.session.get("ctrlGestionAdminIT", 0)

        if adminIT == 1:
            varAcceso = 13050
        else:
            varAcceso = acceso13050

        if acceso13050 == 1:
            varAcceso = 13050

        date1 = date.today().replace(day=1).strftime("%Y-%m-%d")
        today = date.today().strftime("%Y-%m-%d")

        mesA = timezone.now().month
        anioA = timezone.now().year

        # Mes y año anteriores
        mesP = (timezone.now().replace(day=1) - timezone.timedelta(days=1)).month
        anioP = (timezone.now().replace(day=1) - timezone.timedelta(days=1)).year

        # Default
        varFormato = 1
        aplica_programacion_rutas = 0

        centroData = []
        try:
            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_GET_DATA_X_CENTRO_ACCESO",
                    [centro_id, mes, anio, userName, varAcceso],
                )
                column_names = [desc[0] for desc in cursor.description]
                centroData = [dict(zip(column_names, row)) for row in cursor.fetchall()]

            if centroData:
                varFormato = centroData[0]["id_formato"]
                aplica_programacion_rutas = centroData[0]["aplica_programacion_rutas"]
        except Exception as e:
            centroData = []

        centrosData = ejecutar_sp(
            "VAIC_GET_ALL_CENTROS_COSTOS_NOT_X", "universal", [centro_id, mes, anio]
        )
        cuentasData = ejecutar_sp(
            "VAIC_LIST_ALL_CUENTAS_CONTABLES",
            "universal",
            ["Gasto", centro_id, mes, anio],
        )

        vendedoresData = []

        if varFormato == 2:
            vendedoresData = ejecutar_sp(
                "VAIC_LIST_ALL_VENDEDORES", "mastercontrol_EC2", [mesP, anioP]
            )
            allVendedoresData = ejecutar_sp(
                "VAIC_LIST_ALL_VENDEDORES", "mastercontrol_EC2", [mesP, anioP]
            )
        else:
            vendedoresData = ejecutar_sp(
                "VAIC_LIST_ALL_VENDEDORES",
                "universal",
                [mes, anio, aplica_programacion_rutas],
            )
            allVendedoresData = ejecutar_sp("VAIC_LIST_ALL_VENDEDORES_ALL", "universal")

        # Options vendedores en HTML
        optionsHTML = '<option value="">Seleccione un Vendedor</option>'
        for v in vendedoresData:
            if aplica_programacion_rutas == 1:
                optionsHTML += f'<option value="{v["nombre_vendedor"]}" data-costo="{v["costo"]}" data-venta="{v["volumen"]}" data-utilidad="{v["utilidad"]}" data-margen="{v["margen"]}">{v["nombre_vendedor"]}</option>'
            else:
                optionsHTML += f'<option value="{v["nombre_vendedor"]}" data-costo="0.00" data-venta="0.00" data-utilidad="0.00" data-margen="0.00">{v["nombre_vendedor"]}</option>'

        # Servicios centro
        serviciosData = ejecutar_sp(
            "VAIC_LIST_SERVICIOS_CENTRO", "universal", [1, centro_id]
        )
        serviciosHTML = '<option value="">Seleccione un Servicio</option>'
        for s in serviciosData:
            serviciosHTML += (
                f'<option value="{s["id_servicio"]}">{s["servicio"]}</option>'
            )

        context = {
            "date1": date1,
            "date": today,
            "id": centro_id,
            "centro_id": centro_id,
            "varMonth": mes,
            "varAnio": anio,
            "mesA": mesA,
            "anioA": anioA,
            "centroData": centroData,
            "centrosData": centrosData,
            "cuentasData": cuentasData,
            "vendedoresData": vendedoresData,
            "optionsHTML": optionsHTML,
            "serviciosData": serviciosData,
            "serviciosHTML": serviciosHTML,
            "allVendedoresData": allVendedoresData,
            "aplica_programacion_rutas": aplica_programacion_rutas,
            "userName": userName,
            "adminIT": adminIT,
            "autorizaRechazaVAIC": autorizaRechazaVAIC,
        }
        context.update(accesos_context)

        return render(request, "control_gestion/gestion_centro.html", context)

    else:

        return HttpResponseRedirect(reverse("panel_contabilidad"))


def ctrl_crear_solicitud_gasto(request):
    user_id = request.session.get("user_id", "")

    crearSolicitudGasto = int(request.session.get("13081", 0))
    adminIT = int(request.session.get("ctrlGestionAdminIT", 0))

    empresa = 3

    if user_id == "":

        return HttpResponseRedirect(reverse("login"))

    elif crearSolicitudGasto == 1 or adminIT == 1:

        fecha_actual = datetime.now()
        date1 = date.today().replace(day=1).strftime("%Y-%m-%d")
        today = date.today().strftime("%Y-%m-%d")
        varMonth = fecha_actual.strftime("%m")
        varAnio = fecha_actual.strftime("%Y")

        # Accesos personalizados para centros
        permisos_control_gestion = {
            "acceso_crear_centros": "13055",
            "cierre_mensualVAIC": "13051",
            "crearSolicitudGasto": "13081",
        }

        # Construir accesos a partir de la sesión
        accesos_context = {
            nombre: request.session.get(codigo, 0)
            for nombre, codigo in permisos_control_gestion.items()
        }

        # Agregar también si es admin IT contable
        accesos_context["adminIT"] = request.session.get("ctrlGestionAdminIT", 0)

        centrosData = getCentrosGestion()

        optionsCentros = '<option value="#">Seleccione un Centro</option>'
        for c in centrosData:
            optionsCentros += (
                f'<option value="{c["id_centro"]}">{c["nombre_centro"]}</option>'
            )

        cuentasData = ""
        try:
            udcConn = connections["universal"]
            with udcConn.cursor() as cursor:
                cursor.callproc("CONTA_GET_CAT_CUENTAS", [empresa])
                column_names = [desc[0] for desc in cursor.description]
                cuentasData = [
                    dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
                ]

            udcConn.close()
        except Exception as e:
            return JsonResponse({"error": str(e)})

        sucursalesData = ""
        try:
            udcConn = connections["global_nube"]
            with udcConn.cursor() as cursor:
                cursor.callproc("GS_GET_SUCURSALES_X_EMPRESA", [0])
                column_names = [desc[0] for desc in cursor.description]
                sucursalesData = [
                    dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
                ]

            udcConn.close()
        except Exception as e:
            return JsonResponse({"error": str(e)})

        context = {
            "empresasData": getEmpresas(),
            "usersData": getUsers(),
            "formatoData": getFormatos(),
            "cuentasData": getCuentasAnaliticas(),
            "deptosData": getDepartametos(),
            "centrosData": centrosData,
            "varMonth": varMonth,
            "varAnio": varAnio,
            "date1": date1,
            "date": today,
            "empresa": empresa,
            "crearSolicitudGasto": crearSolicitudGasto,
            "adminIT": adminIT,
            "optionsCentros": optionsCentros,
            "sucursalesData": sucursalesData,
            "cuentasContablesData": cuentasData,
        }
        context.update(accesos_context)

        return render(request, "control_gestion/crear_solicitud_gasto.html", context)

    else:
        return HttpResponseRedirect(reverse("panel_contabilidad"))


def dataAcreedores(request):
    try:
        udcConn = connections["mastercontrol_EC2"]
        with udcConn.cursor() as cursor:
            cursor.callproc("CONTA_GET_ACREEDORES")
            column_names = [desc[0] for desc in cursor.description]
            acreedores = [
                dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
            ]
        udcConn.close()

        return JsonResponse({"data": acreedores})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def getNextAcreedorCode(request):
    try:
        with connections["mastercontrol_EC2"].cursor() as cursor:
            cursor.execute("SELECT MAX(PKacree) FROM acreedores")
            last_code = cursor.fetchone()[0] or "1"

            # Convertir a número y sumar 1
            next_code = str(int(last_code) + 1)

        return JsonResponse({"next_code": next_code})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def createAcreedor(request):
    if request.method == "POST":
        codigo = request.POST.get("codigo")
        rtn = request.POST.get("rtn")
        nombre_conocido = request.POST.get("nombre_conocido")
        nombre = request.POST.get("nombre")
        correo = request.POST.get("correo")
        telefono = request.POST.get("telefono")
        direccion = request.POST.get("direccion")
        userName = request.session.get("userName", "system")

        existe = 0

        try:
            with connections["mastercontrol_EC2"].cursor() as cursor:
                cursor.callproc(
                    "CONTA_INSERT_ACREEDOR",
                    [
                        codigo,
                        nombre_conocido,
                        nombre,
                        correo,
                        telefono,
                        direccion,
                        rtn,
                        userName,
                    ],
                )
                resultado = cursor.fetchall()

                if resultado:
                    for fila in resultado:
                        existe = fila[0]

            return JsonResponse({"success": True, "existe": existe})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


def ctrl_crear_solicitud_ingreso(request):
    user_id = request.session.get("user_id", "")

    crearSolicitudGasto = int(request.session.get("13081", 0))
    adminIT = int(request.session.get("ctrlGestionAdminIT", 0))

    empresa = 3

    if user_id == "":

        return HttpResponseRedirect(reverse("login"))

    elif crearSolicitudGasto == 1 or adminIT == 1:

        fecha_actual = datetime.now()
        date1 = date.today().replace(day=1).strftime("%Y-%m-%d")
        today = date.today().strftime("%Y-%m-%d")
        varMonth = fecha_actual.strftime("%m")
        varAnio = fecha_actual.strftime("%Y")

        # Accesos personalizados para centros
        permisos_control_gestion = {
            "acceso_crear_centros": "13055",
            "cierre_mensualVAIC": "13051",
            "crearSolicitudGasto": "13081",
        }

        # Construir accesos a partir de la sesión
        accesos_context = {
            nombre: request.session.get(codigo, 0)
            for nombre, codigo in permisos_control_gestion.items()
        }

        # Agregar también si es admin IT contable
        accesos_context["adminIT"] = request.session.get("ctrlGestionAdminIT", 0)

        centrosData = getCentrosGestion()

        optionsCentros = '<option value="#">Seleccione un Centro</option>'
        for c in centrosData:
            optionsCentros += (
                f'<option value="{c["id_centro"]}">{c["nombre_centro"]}</option>'
            )

        cuentasData = ""
        try:
            udcConn = connections["universal"]
            with udcConn.cursor() as cursor:
                cursor.callproc("CONTA_GET_CAT_CUENTAS", [empresa])
                column_names = [desc[0] for desc in cursor.description]
                cuentasData = [
                    dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
                ]

            udcConn.close()
        except Exception as e:
            return JsonResponse({"error": str(e)})

        sucursalesData = ""
        try:
            udcConn = connections["global_nube"]
            with udcConn.cursor() as cursor:
                cursor.callproc("GS_GET_SUCURSALES_X_EMPRESA", [0])
                column_names = [desc[0] for desc in cursor.description]
                sucursalesData = [
                    dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
                ]

            udcConn.close()
        except Exception as e:
            return JsonResponse({"error": str(e)})

        proveedoresData = ""
        try:
            udcConn = connections["mastercontrol_EC2"]
            with udcConn.cursor() as cursor:
                cursor.callproc("CONTA_GET_PROVEEDORES")
                column_names = [desc[0] for desc in cursor.description]
                proveedoresData = [
                    dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
                ]

            udcConn.close()
        except Exception as e:
            return JsonResponse({"error": str(e)})

        context = {
            "empresasData": getEmpresas(),
            "usersData": getUsers(),
            "formatoData": getFormatos(),
            "cuentasData": getCuentasAnaliticas(),
            "deptosData": getDepartametos(),
            "centrosData": centrosData,
            "varMonth": varMonth,
            "varAnio": varAnio,
            "date1": date1,
            "date": today,
            "empresa": empresa,
            "crearSolicitudGasto": crearSolicitudGasto,
            "adminIT": adminIT,
            "optionsCentros": optionsCentros,
            "sucursalesData": sucursalesData,
            "cuentasContablesData": cuentasData,
            "proveedoresData": proveedoresData,
        }
        context.update(accesos_context)

        return render(request, "control_gestion/crear_solicitud_ingreso.html", context)

    else:
        return HttpResponseRedirect(reverse("panel_contabilidad"))


def ctrl_ingresar_gastos_bancario(request):
    user_id = request.session.get("user_id", "")

    ingresarGastos = int(request.session.get("13053", 0))
    aprobarIngresoGastos = int(request.session.get("13054", 0))
    finalizarIngresoGastos_VAIC = int(request.session.get("13060", 0))

    adminIT = int(request.session.get("ctrlGestionAdminIT", 0))

    empresa = 3

    if user_id == "":

        return HttpResponseRedirect(reverse("login"))

    elif ingresarGastos == 1 or adminIT == 1:

        fecha_actual = datetime.now()
        date1 = (date.today().replace(day=1) - relativedelta(months=1)).strftime(
            "%Y-%m-%d"
        )
        today = date.today().strftime("%Y-%m-%d")
        varMonth = fecha_actual.strftime("%m")
        varAnio = fecha_actual.strftime("%Y")

        # Accesos personalizados para centros
        permisos_control_gestion = {
            "ingresarGastos": "13053",
            "aprobarIngresoGastos": "13054",
            "finalizarIngresoGastos_VAIC": "13060",
        }

        # Construir accesos a partir de la sesión
        accesos_context = {
            nombre: request.session.get(codigo, 0)
            for nombre, codigo in permisos_control_gestion.items()
        }

        # Agregar también si es admin IT contable
        accesos_context["adminIT"] = request.session.get("ctrlGestionAdminIT", 0)

        centrosData = []
        try:
            udcConn = connections["universal"]
            with udcConn.cursor() as cursor:
                cursor.callproc(
                    "VAIC_LIST_CENTROS_NOT_CERRADOS_X_PERIODO", [varMonth, varAnio]
                )
                column_names = [desc[0] for desc in cursor.description]
                centrosData = [
                    dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
                ]

            udcConn.close()
        except Exception as e:
            centrosData = "centrosData: {}".format(str(e))

        context = {
            "empresasData": getEmpresas(),
            "usersData": getUsers(),
            "centrosData": centrosData,
            "mes": varMonth,
            "anio": varAnio,
            "varMonth": varMonth,
            "varAnio": varAnio,
            "date1": date1,
            "date": today,
            "adminIT": adminIT,
        }
        context.update(accesos_context)

        return render(request, "control_gestion/ingresar_gastos_bancario.html", context)

    else:
        return HttpResponseRedirect(reverse("panel_contabilidad"))


def ctrl_balance_presupuesto_centros_view(request):
    user_id = request.session.get("user_id", "")
    reporteBalanceCentros_VAIC = int(request.session.get("13111", 0))
    adminIT = request.session.get("ctrlGestionAdminIT", 0)

    if user_id == "":
        return HttpResponseRedirect(reverse("login"))
    else:
        if reporteBalanceCentros_VAIC == 1 or adminIT == 1:

            fecha_actual = datetime.now()
            varMonth = fecha_actual.strftime("%m")
            varAnio = fecha_actual.strftime("%Y")

            context = {
                "empresasData": getEmpresas(),
                "varMonth": varMonth,
                "varAnio": varAnio,
                "reporteBalanceCentros_VAIC": reporteBalanceCentros_VAIC,
            }

            return render(
                request,
                "control_gestion/reporteria/balance_presupuesto_centros.html",
                context,
            )
        else:
            return HttpResponseRedirect(reverse("panel_contabilidad"))


def ctrl_balance_presupuesto_cuentas_view(request):
    user_id = request.session.get("user_id", "")
    reporteCuentasEmpresa_VAIC = int(request.session.get("13110", 0))
    adminIT = request.session.get("ctrlGestionAdminIT", 0)

    if user_id == "":
        return HttpResponseRedirect(reverse("login"))
    else:
        if reporteCuentasEmpresa_VAIC == 1 or adminIT == 1:

            fecha_actual = datetime.now()
            varMonth = fecha_actual.strftime("%m")
            varAnio = fecha_actual.strftime("%Y")

            context = {
                "empresasData": getEmpresas(),
                "varMonth": varMonth,
                "varAnio": varAnio,
            }

            return render(
                request,
                "control_gestion/reporteria/balance_presupuesto_cuentas.html",
                context,
            )
        else:
            return HttpResponseRedirect(reverse("panel_contabilidad"))


def ctrl_reporte_anual_centros_view(request):
    user_id = request.session.get("user_id", "")
    reporteBalanceCentros_VAIC = int(request.session.get("13111", 0))
    adminIT = request.session.get("ctrlGestionAdminIT", 0)

    if user_id == "":
        return HttpResponseRedirect(reverse("login"))
    else:
        if reporteBalanceCentros_VAIC == 1 or adminIT == 1:

            fecha_actual = datetime.now()
            varMonth = fecha_actual.strftime("%m")
            varAnio = fecha_actual.strftime("%Y")

            context = {
                "empresasData": getEmpresas(),
                "varMonth": varMonth,
                "varAnio": varAnio,
            }

            return render(
                request,
                "control_gestion/reporteria/reporte_anual_centros.html",
                context,
            )
        else:
            return HttpResponseRedirect(reverse("panel_contabilidad"))


def ctrl_reporte_anual_cuentas_view(request):
    user_id = request.session.get("user_id", "")
    reporteBalanceCentros_VAIC = int(request.session.get("13111", 0))
    adminIT = request.session.get("ctrlGestionAdminIT", 0)

    if user_id == "":
        return HttpResponseRedirect(reverse("login"))
    else:
        if reporteBalanceCentros_VAIC == 1 or adminIT == 1:

            fecha_actual = datetime.now()
            varMonth = fecha_actual.strftime("%m")
            varAnio = fecha_actual.strftime("%Y")

            context = {
                "empresasData": getEmpresas(),
                "varMonth": varMonth,
                "varAnio": varAnio,
            }

            return render(
                request,
                "control_gestion/reporteria/reporte_anual_cuentas.html",
                context,
            )
        else:
            return HttpResponseRedirect(reverse("panel_contabilidad"))


def ctrl_reporte_gastos_view(request):
    user_id = request.session.get("user_id", "")
    reporteGastos_VAIC = int(request.session.get("13059", 0))
    adminIT = request.session.get("ctrlGestionAdminIT", 0)

    if user_id == "":
        return HttpResponseRedirect(reverse("login"))
    else:
        if reporteGastos_VAIC == 1 or adminIT == 1:

            fecha_actual = datetime.now()
            varMonth = fecha_actual.strftime("%m")
            varAnio = fecha_actual.strftime("%Y")

            context = {
                "empresasData": getEmpresas(),
                "varMonth": varMonth,
                "varAnio": varAnio,
            }

            return render(
                request, "control_gestion/reporteria/reporte_gastos.html", context
            )
        else:
            return HttpResponseRedirect(reverse("panel_contabilidad"))


def ctrl_reporte_ingresos_view(request):
    user_id = request.session.get("user_id", "")
    reporteIngresos_VAIC = int(request.session.get("13109", 0))
    adminIT = request.session.get("ctrlGestionAdminIT", 0)

    if user_id == "":
        return HttpResponseRedirect(reverse("login"))
    else:
        if reporteIngresos_VAIC == 1 or adminIT == 1:

            fecha_actual = datetime.now()
            varMonth = fecha_actual.strftime("%m")
            varAnio = fecha_actual.strftime("%Y")

            context = {
                "empresasData": getEmpresas(),
                "varMonth": varMonth,
                "varAnio": varAnio,
            }

            return render(
                request, "control_gestion/reporteria/reporte_ingresos.html", context
            )
        else:
            return HttpResponseRedirect(reverse("panel_contabilidad"))


def ctrl_reporte_proyecciones_presupuestos_view(request):
    user_id = request.session.get("user_id", "")
    reporteGeneral_VAIC = int(request.session.get("13057", 0))
    adminIT = request.session.get("ctrlGestionAdminIT", 0)

    if user_id == "":
        return HttpResponseRedirect(reverse("login"))
    else:
        if reporteGeneral_VAIC == 1 or adminIT == 1:

            fecha_actual = datetime.now()
            varMonth = fecha_actual.strftime("%m")
            varAnio = fecha_actual.strftime("%Y")

            context = {
                "empresasData": getEmpresas(),
                "varMonth": varMonth,
                "varAnio": varAnio,
            }

            return render(
                request,
                "control_gestion/reporteria/reporte_proyecciones_presupuestos.html",
                context,
            )
        else:
            return HttpResponseRedirect(reverse("panel_contabilidad"))


def ctrl_reporte_saldo_cuentas_view(request):
    user_id = request.session.get("user_id", "")
    reporteSaldosCuentas = int(request.session.get("13078", 0))
    adminIT = request.session.get("ctrlGestionAdminIT", 0)

    if user_id == "":
        return HttpResponseRedirect(reverse("login"))
    else:
        if reporteSaldosCuentas == 1 or adminIT == 1:

            fecha_actual = datetime.now()
            varMonth = fecha_actual.strftime("%m")
            varAnio = fecha_actual.strftime("%Y")

            context = {
                "empresasData": getEmpresas(),
                "centrosData": getCentrosGestion(),
                "varMonth": varMonth,
                "varAnio": varAnio,
            }

            return render(
                request,
                "control_gestion/reporteria/reporte_saldos_cuentas.html",
                context,
            )
        else:
            return HttpResponseRedirect(reverse("panel_contabilidad"))


""" FUNCIONES """


def autorizar_rechazar_solicitud_ingreso(request):
    solicitud_id = request.POST.get("solicitud_id")
    opcion = request.POST.get("opcion")  # 1 = autorizar, 0 = rechazar

    # Normalizamos por si viene como string
    try:
        opcion = int(opcion) if opcion is not None else 0
    except ValueError:
        opcion = 0

    action = "AUTORIZAR" if opcion == 1 else "RECHAZAR"
    presentAction = action  # igual que en tu código original

    userName = request.session.get("userName")

    try:
        with connections["universal"].cursor() as cursor:
            # 1) Autorizar / Rechazar
            cursor.callproc(
                "VAIC_AUTORIZAR_SOLICITUD_INGRESO", [solicitud_id, opcion, userName]
            )
            # Drenamos posibles result sets
            drain_cursor(cursor)

            # 2) Log de evento
            mensaje = f"{userName} HA {presentAction} LA SOLICITUD DE INGRESO CON # {solicitud_id}"
            cursor.callproc(
                "DAC_INSERT_LOG_EVENTO",
                [action, mensaje, userName, "vaic_solicitud_ingresos"],
            )

            # Drenamos posibles result sets
            drain_cursor(cursor)

        return JsonResponse({"save": 1})
    except Exception as e:
        return JsonResponse({"save": 0, "error": str(e)})


def autorizar_rechazar_solicitud_gasto(request):
    solicitud_id = request.POST.get("solicitud_id")
    opcion = request.POST.get("opcion")  # 1 = autorizar, 0 = rechazar

    # Normalizamos por si viene como string
    try:
        opcion = int(opcion) if opcion is not None else 0
    except ValueError:
        opcion = 0

    action = "AUTORIZAR" if opcion == 1 else "RECHAZAR"
    presentAction = action  # igual que en tu código original

    userName = request.session.get("userName")

    try:
        with connections["universal"].cursor() as cursor:
            # 1) Autorizar / Rechazar
            cursor.callproc(
                "VAIC_AUTORIZAR_SOLICITUD_GASTO", [solicitud_id, opcion, userName]
            )
            # Drenamos posibles result sets
            drain_cursor(cursor)

            # 2) Log de evento
            mensaje = f"{userName} HA {presentAction} LA SOLICITUD DE GASTO CON # {solicitud_id}"
            cursor.callproc(
                "DAC_INSERT_LOG_EVENTO",
                [action, mensaje, userName, "vaic_solicitudes_gastos"],
            )

            # Drenamos posibles result sets
            drain_cursor(cursor)

        return JsonResponse({"save": 1})
    except Exception as e:
        return JsonResponse({"save": 0, "error": str(e)})


def save_solicitud_gasto_vaic(request):
    # ----- Encabezado solicitud -----
    fecha_doc = request.POST.get("fecha_doc")
    fecha_pago = request.POST.get("fecha_pago")
    tipo_doc = request.POST.get("tipo_doc")
    mes = request.POST.get("mes")
    anio = request.POST.get("anio")
    concepto_principal = request.POST.get("concepto_principal")

    # ----- Campos de PARTIDA CONTABLE -----
    empresaPartida = request.POST.get("empresaPartida")
    sucursalPartida = request.POST.get("sucursalPartida")
    acreedorSelect = request.POST.get("acreedorSelect")
    acreedorSelectText = (request.POST.get("acreedorSelectText") or "").strip()
    cuentaSelect = request.POST.get("cuentaSelect")  # cuenta contrapartida (Haber)
    cuentaSelectText = request.POST.get(
        "cuentaSelectText"
    )  # texto cuenta Haber (opcional)
    solicitud_valor = request.POST.get("solicitud_valor")  # total Haber

    userName = request.session.get("userName")

    # ----- Detalles (array de objetos) -----

    assignedSoliGastos = request.POST.get("assignedSoliGastos")
    try:
        if isinstance(assignedSoliGastos, str):
            assignedSoliGastos = json.loads(assignedSoliGastos or "[]")
    except Exception:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
            assignedSoliGastos = payload.get("assignedSoliGastos", [])
        except Exception:
            assignedSoliGastos = []

    # Conversión segura de total
    try:
        total_haber = float(str(solicitud_valor or 0).replace(",", ""))
    except Exception:
        total_haber = 0.0

    conn = connections["universal"]

    # Helper: ejecuta CALL y drena TODOS los result sets; retorna la PRIMERA grilla en dicts
    def call_and_drain(sql, params):
        with conn.cursor() as cur:
            cur.execute(sql, params)
            first_rs = []
            # primer result set (si lo hay)
            if cur.description:
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()
                first_rs = [dict(zip(map(str, cols), r)) for r in rows]
            else:
                # A veces no hay description pero sí sets subsecuentes; igual drenamos
                try:
                    cur.fetchall()
                except Exception:
                    pass
            # drenar siguientes sets (si existen)
            while True:
                try:
                    more = cur.nextset()
                except Exception:
                    more = None
                if not more:
                    break
                try:
                    # si devuelven más filas, hay que consumirlas también
                    if cur.description:
                        _ = cur.fetchall()
                    else:
                        cur.fetchall()
                except Exception:
                    pass
            return first_rs

    try:
        # =========================
        # PHASE 1: obtener id_encabezado
        # =========================
        phase = "get_max_id_encabezado"
        rs = call_and_drain("CALL VAIC_GET_MAX_ID_ENCABEZADO_GASTOS()", [])
        id_encabezado = rs[0]["id_encabezado"] if rs else None

        # =========================
        # PHASE 2: insertar detalles de la solicitud
        # =========================
        phase = "insert_detalle_solicitud"
        for g in assignedSoliGastos:
            concepto = g.get("concepto", "")
            valor = g.get("valor", 0)
            isv = g.get("isv", 0)
            centro = g.get("centro")
            cuenta = g.get("cuenta")

            call_and_drain(
                "CALL VAIC_SAVE_DETALLE_SOLICITUDES_GASTO(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    cuenta,
                    fecha_doc,
                    concepto,
                    centro,
                    valor,
                    isv,
                    userName,
                    id_encabezado,
                    fecha_pago,
                    tipo_doc,
                    concepto_principal,
                    mes,
                    anio,
                ],
            )

        # =========================
        # PHASE 3: encabezado de partida
        # =========================
        phase = "insert_encabezado_partida"
        sinopsis_enc = f"Gasto # {id_encabezado} | {acreedorSelectText}".strip()
        referencia_enc = f"{id_encabezado} | {acreedorSelectText}".strip()

        varPartida = 0
        varTipoPartida = "030"
        varSistema = 12
        varFechaPartida = fecha_doc
        varTasa = 0
        varBalance = 0
        varBalanceD = 0
        varEmpresa = empresaPartida
        varSucursal = sucursalPartida
        opc = 1  # insertar

        rs_head = call_and_drain(
            "CALL CONTA_INSERT_UPDATE_ENCABEZADO_PARTIDA(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                varPartida,
                varTipoPartida,
                sinopsis_enc,
                varSistema,
                varFechaPartida,
                varTasa,
                varBalance,
                varBalanceD,
                varEmpresa,
                userName,
                varSucursal,
                referencia_enc,
                opc,
            ],
        )
        id_partida = rs_head[0]["varID"] if rs_head else None
        numPartida = rs_head[0]["numPartida"] if rs_head else None

        # =========================
        # PHASE 4: detalles (DEBE)
        # =========================
        phase = "insert_detalles_debe"
        for g in assignedSoliGastos:
            concepto_linea = g.get("concepto", "")
            try:
                valor_linea = float(str(g.get("valor", 0)).replace(",", ""))
            except Exception:
                valor_linea = 0.0
            cuenta_linea = g.get("codigo")
            sinopsis_linea = g.get("descripcion")

            call_and_drain(
                "CALL CONTA_INSERT_UPDATE_DETALLE_PARTIDA(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                [
                    0,  # varDetalle
                    id_partida,  # varPartida
                    numPartida,  # varNumPartida
                    fecha_doc,  # varFechaHora
                    str(cuenta_linea),  # varCodigo
                    sinopsis_linea,  # varConcepto
                    sinopsis_linea,  # varSinopsis
                    valor_linea,  # varDebe
                    0,  # varHaber
                    userName,  # userName
                    0,
                ],
            )

        # =========================
        # PHASE 5: contrapartida (HABER)
        # =========================
        phase = "insert_contrapartida_haber"
        concepto_haber = f"Contrapartida {acreedorSelectText}".strip()
        sinopsis_haber = f"Contrapartida | {cuentaSelectText or ''}".strip()

        call_and_drain(
            "CALL CONTA_INSERT_UPDATE_DETALLE_PARTIDA(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                0,  # varDetalle
                id_partida,  # varPartida
                numPartida,  # varNumPartida
                fecha_doc,  # varFechaHora
                str(cuentaSelect),  # varCodigo (Haber)
                cuentaSelectText,  # varConcepto
                cuentaSelectText,  # varSinopsis
                0,  # varDebe
                total_haber,  # varHaber
                userName,  # userName
                0,
            ],
        )

        return JsonResponse(
            {
                "save": 1,
                "id_encabezado": id_encabezado,
                "id_partida": id_partida,
                "numPartida": numPartida,
                "sinopsis": sinopsis_enc,
                "referencia": referencia_enc,
            }
        )

    except Exception as e:
        # Te digo en qué fase caímos para debug
        return JsonResponse({"save": 0, "error": str(e), "phase": phase})


def save_solicitud_ingreso_vaic(request):
    # ----- Encabezado solicitud -----
    fecha_doc = request.POST.get("fecha_doc")
    fecha_pago = request.POST.get("fecha_pago")
    tipo_doc = request.POST.get("tipo_doc")
    mes = request.POST.get("mes")
    anio = request.POST.get("anio")
    concepto_principal = request.POST.get("concepto_principal")

    # ----- Campos de PARTIDA CONTABLE -----
    empresaPartida = request.POST.get("empresaPartida")
    sucursalPartida = request.POST.get("sucursalPartida")
    acreedorSelect = request.POST.get("acreedorSelect")
    acreedorSelectText = (request.POST.get("acreedorSelectText") or "").strip()
    cuentaSelect = request.POST.get("cuentaSelect")  # cuenta contrapartida (Haber)
    cuentaSelectText = request.POST.get(
        "cuentaSelectText"
    )  # texto cuenta Haber (opcional)
    solicitud_valor = request.POST.get("solicitud_valor")  # total Haber

    userName = request.session.get("userName")

    # ----- Detalles (array de objetos) -----
    import json

    assignedSoliGastos = request.POST.get("assignedSoliGastos")
    try:
        if isinstance(assignedSoliGastos, str):
            assignedSoliGastos = json.loads(assignedSoliGastos or "[]")
    except Exception:
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
            assignedSoliGastos = payload.get("assignedSoliGastos", [])
        except Exception:
            assignedSoliGastos = []

    # Conversión segura de total
    try:
        total_haber = float(str(solicitud_valor or 0).replace(",", ""))
    except Exception:
        total_haber = 0.0

    conn = connections["universal"]

    # Helper: ejecuta CALL y drena TODOS los result sets; retorna la PRIMERA grilla en dicts
    def call_and_drain(sql, params):
        with conn.cursor() as cur:
            cur.execute(sql, params)
            first_rs = []
            # primer result set (si lo hay)
            if cur.description:
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()
                first_rs = [dict(zip(map(str, cols), r)) for r in rows]
            else:
                # A veces no hay description pero sí sets subsecuentes; igual drenamos
                try:
                    cur.fetchall()
                except Exception:
                    pass
            # drenar siguientes sets (si existen)
            while True:
                try:
                    more = cur.nextset()
                except Exception:
                    more = None
                if not more:
                    break
                try:
                    # si devuelven más filas, hay que consumirlas también
                    if cur.description:
                        _ = cur.fetchall()
                    else:
                        cur.fetchall()
                except Exception:
                    pass
            return first_rs

    try:
        # =========================
        # PHASE 1: obtener id_encabezado
        # =========================
        phase = "get_max_id_encabezado"
        rs = call_and_drain("CALL VAIC_GET_MAX_ID_ENCABEZADO_INGRESOS()", [])
        id_encabezado = rs[0]["id_encabezado"] if rs else None

        # =========================
        # PHASE 2: insertar detalles de la solicitud
        # =========================
        phase = "insert_detalle_solicitud"
        for g in assignedSoliGastos:
            concepto = g.get("concepto", "")
            valor = g.get("valor", 0)
            isv = g.get("isv", 0)
            centro = g.get("centro")
            cuenta = g.get("cuenta")

            call_and_drain(
                "CALL VAIC_SAVE_DETALLE_SOLICITUDES_INGRESO(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                [
                    cuenta,
                    fecha_doc,
                    concepto,
                    centro,
                    valor,
                    isv,
                    userName,
                    id_encabezado,
                    fecha_pago,
                    tipo_doc,
                    concepto_principal,
                    mes,
                    anio,
                ],
            )

        # =========================
        # PHASE 3: encabezado de partida
        # =========================
        phase = "insert_encabezado_partida"
        sinopsis_enc = f"Gasto # {id_encabezado} | {acreedorSelectText}".strip()
        referencia_enc = f"{id_encabezado} | {acreedorSelectText}".strip()

        varPartida = 0
        varTipoPartida = "031"
        varSistema = 12
        varFechaPartida = fecha_doc
        varTasa = 0
        varBalance = 0
        varBalanceD = 0
        varEmpresa = empresaPartida
        varSucursal = sucursalPartida
        opc = 1  # insertar

        rs_head = call_and_drain(
            "CALL CONTA_INSERT_UPDATE_ENCABEZADO_PARTIDA(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                varPartida,
                varTipoPartida,
                sinopsis_enc,
                varSistema,
                varFechaPartida,
                varTasa,
                varBalance,
                varBalanceD,
                varEmpresa,
                userName,
                varSucursal,
                referencia_enc,
                opc,
            ],
        )
        id_partida = rs_head[0]["varID"] if rs_head else None
        numPartida = rs_head[0]["numPartida"] if rs_head else None

        # =========================
        # PHASE 4: detalles (DEBE)
        # =========================
        phase = "insert_detalles_debe"
        for g in assignedSoliGastos:
            concepto_linea = g.get("concepto", "")
            try:
                valor_linea = float(str(g.get("valor", 0)).replace(",", ""))
            except Exception:
                valor_linea = 0.0
            cuenta_linea = g.get("codigo")
            sinopsis_linea = g.get("descripcion")

            call_and_drain(
                "CALL CONTA_INSERT_UPDATE_DETALLE_PARTIDA(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                [
                    0,  # varDetalle
                    id_partida,  # varPartida
                    numPartida,  # varNumPartida
                    fecha_doc,  # varFechaHora
                    str(cuenta_linea),  # varCodigo
                    sinopsis_linea,  # varConcepto
                    sinopsis_linea,  # varSinopsis
                    valor_linea,  # varDebe
                    0,  # varHaber
                    userName,  # userName
                    0,
                ],
            )

        # =========================
        # PHASE 5: contrapartida (HABER)
        # =========================
        phase = "insert_contrapartida_haber"
        concepto_haber = f"Contrapartida {acreedorSelectText}".strip()
        sinopsis_haber = f"Contrapartida | {cuentaSelectText or ''}".strip()

        call_and_drain(
            "CALL CONTA_INSERT_UPDATE_DETALLE_PARTIDA(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [
                0,  # varDetalle
                id_partida,  # varPartida
                numPartida,  # varNumPartida
                fecha_doc,  # varFechaHora
                str(cuentaSelect),  # varCodigo (Haber)
                cuentaSelectText,  # varConcepto
                cuentaSelectText,  # varSinopsis
                0,  # varDebe
                total_haber,  # varHaber
                userName,  # userName
                0,
            ],
        )

        return JsonResponse(
            {
                "save": 1,
                "id_encabezado": id_encabezado,
                "id_partida": id_partida,
                "numPartida": numPartida,
                "sinopsis": sinopsis_enc,
                "referencia": referencia_enc,
            }
        )

    except Exception as e:
        # Te digo en qué fase caímos para debug
        return JsonResponse({"save": 0, "error": str(e), "phase": phase})


def aprobar_gasto_no_presupuesto_vaic(request):
    pkHistorial = request.POST.get("pkHistorial")
    pkAcreedor = request.POST.get("pkAcreedor")
    id_gasto = request.POST.get("id_gasto")

    userName = request.session.get("userName", "")

    try:
        # 1) Autoriza en la BD universal
        with connections["universal"].cursor() as cu:
            cu.callproc("VAIC_AUTORIZAR_GASTO_FUERA_PRESUPUESTO", [id_gasto, userName])
            drain_cursor(cu)

        # 2) Autoriza en la BD bancaria
        with connections["bankConn"].cursor() as cb:
            cb.callproc(
                "VAIC_AUTORIZAR_GASTO_FUERA_PRESUPUESTO",
                [pkAcreedor, pkHistorial, userName],
            )
            drain_cursor(cb)

        # 3) Log en universal
        with connections["universal"].cursor() as cu2:
            cu2.callproc(
                "DAC_INSERT_LOG_EVENTO",
                [
                    "GASTOS",
                    f"{userName} HA APROBADO EL GASTO FUERA DE PRESUPUESTO CON # DE ACREEDOR {pkAcreedor} Y # DE MOVIMIENTO DE INGRESO {pkHistorial}",
                    userName,
                    "vaic_gastos",
                ],
            )
            drain_cursor(cu2)

        return JsonResponse({"save": 1})
    except Exception as e:
        return JsonResponse({"save": 0, "error": str(e)})


def get_data_presupuesto(request):
    presupuesto_id = request.POST.get("presupuesto_id") or request.GET.get(
        "presupuesto_id"
    )
    centro_id = request.POST.get("centro_id") or request.GET.get(
        "centro_id"
    )  # no usado por el SP, pero lo recibimos igual
    mes = request.POST.get("mes") or request.GET.get("mes")  # no usado aquí
    anio = request.POST.get("anio") or request.GET.get("anio")  # no usado aquí

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_GET_DATA_X_PRESUPUESTO", [presupuesto_id])
            columns = (
                [col[0] for col in cursor.description] if cursor.description else []
            )
            rows = cursor.fetchall() if cursor.description else []

            # Drenar cualquier result set adicional (por si el SP retorna varios)
            drain_cursor(cursor)

        if rows:
            row = dict(zip(map(str, columns), rows[0]))

            # Ajustar nombres tal como en tu Laravel:
            # valor_autorizado <- disponible
            data = {
                "id_cuenta_contable": row.get("id_cuenta_contable", 0),
                "numero_cuenta": row.get("numero_cuenta", 0),
                "valor_autorizado": row.get("disponible", 0.00),
                "mes": row.get("mes", 0),
                "anio": row.get("anio", 0),
            }
        else:
            data = {
                "id_cuenta_contable": 0.00,
                "numero_cuenta": 0.00,
                "valor_autorizado": 0.00,
                "mes": 0,
                "anio": 0,
            }

        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"save": 0, "error": str(e)})


def fill_table_solicitudes_ingresos(request):
    date1 = request.GET.get("date1")
    date2 = request.GET.get("date2")
    userName = request.session.get(
        "userName", ""
    )  # por consistencia (no se usa en el SP)

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_LIST_SOLICITUDES_INGRESOS", [date1, date2, userName, 13050]
            )
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            data = []
            for row in rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Normaliza campos tipo BIT/bytes a int
                    if isinstance(val, (bytes, bytearray)):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def fill_table_gastos_bancario(request):
    date1 = request.GET.get("date1")
    date2 = request.GET.get("date2")
    userName = request.session.get(
        "userName", ""
    )  # por consistencia (no se usa en el SP)

    try:
        with connections["bankConn"].cursor() as cursor:
            cursor.callproc("VAIC_LIST_PAGO_ACREEDORES", [date1, date2])
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            data = []
            for row in rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Normaliza campos tipo BIT/bytes a int
                    if isinstance(val, (bytes, bytearray)):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def fill_table_gastos_fuera_presupuesto(request):
    mes = request.GET.get("mes")
    anio = request.GET.get("anio")
    userName = request.session.get(
        "userName", ""
    )  # por consistencia (no se usa en el SP)

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_GASTOS_INGRESADOS_FUERA_PRESUPUESTO", [mes, anio])
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            data = []
            for row in rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Normaliza campos tipo BIT/bytes a int
                    if isinstance(val, (bytes, bytearray)):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def fill_table_solicitudes_gastos(request):
    date1 = request.GET.get("date1")
    date2 = request.GET.get("date2")
    userName = request.session.get(
        "userName", ""
    )  # por consistencia (no se usa en el SP)

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_LIST_SOLICITUDES_GASTOS", [date1, date2])
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            data = []
            for row in rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Normaliza campos tipo BIT/bytes a int
                    if isinstance(val, (bytes, bytearray)):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def fill_select_cuentas_ingresos_centro(request):
    centro_id = request.POST.get("centro_id")
    mes = request.POST.get("mes")
    anio = request.POST.get("anio")

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_GET_CUENTAS_APROBADAS_INGRESOS", [centro_id, mes, anio]
            )
            columns = [c[0] for c in cursor.description]
            rows = cursor.fetchall()

        # Construir <option> como en Laravel
        if rows:
            options_html = '<option value="0" selected>Seleccione cuenta a Ingresar Ingreso</option>'
            for row in rows:
                row_dict = dict(zip(map(str, columns), row))
                options_html += (
                    f'<option value="{row_dict["id_presupuesto"]}">'
                    f'{row_dict["numero_cuenta"]} | {row_dict["descripcion_cuenta"]}'
                    f"</option>"
                )
        else:
            options_html = (
                '<option value="0" selected>Centro sin Cuentas Presupuestadas!</option>'
            )

        # Devolver string plano como JSON (para que $.ajax con dataType:"json" reciba un string)
        return JsonResponse(options_html, safe=False)

    except Exception as e:
        # En error, devuelve una opción informativa
        return JsonResponse(
            f'<option value="0" selected>Error: {str(e)}</option>', safe=False
        )


def fill_select_cuentas_centro(request):
    centro_id = request.POST.get("centro_id")
    mes = request.POST.get("mes")
    anio = request.POST.get("anio")

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_GET_CUENTAS_APROBADAS", [centro_id, mes, anio])
            columns = [c[0] for c in cursor.description]
            rows = cursor.fetchall()

        # Construir <option> como en Laravel
        if rows:
            options_html = (
                '<option value="0" selected>Seleccione cuenta a Ingresar Gasto</option>'
            )
            for row in rows:
                row_dict = dict(zip(map(str, columns), row))
                options_html += (
                    f'<option value="{row_dict["id_presupuesto"]}">'
                    f'{row_dict["numero_cuenta"]} | {row_dict["descripcion_cuenta"]}'
                    f"</option>"
                )
        else:
            options_html = (
                '<option value="0" selected>Centro sin Cuentas Presupuestadas!</option>'
            )

        # Devolver string plano como JSON (para que $.ajax con dataType:"json" reciba un string)
        return JsonResponse(options_html, safe=False)

    except Exception as e:
        # En error, devuelve una opción informativa
        return JsonResponse(
            f'<option value="0" selected>Error: {str(e)}</option>', safe=False
        )


# Otros datos
def ejecutar_sp(nombre_sp, conn_name, params=[]):
    try:
        with connections[conn_name].cursor() as cursor:
            cursor.callproc(nombre_sp, params)
            column_names = [desc[0] for desc in cursor.description]
            return [dict(zip(column_names, row)) for row in cursor.fetchall()]
    except Exception:
        return []


def revisar_gasto_vaic(request):
    datos = {}

    id_gasto = request.POST.get("id_gasto")
    userName = request.session.get("userName")

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_REVISAR_GASTO", [id_gasto, userName])

        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "DAC_INSERT_LOG_EVENTO",
                [
                    "GASTOS",
                    f"{userName} HA REVISADO EL GASTO CON # {id_gasto}",
                    userName,
                    "vaic_gastos",
                ],
            )

        datos["save"] = 1

    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


def guardar_presupuestos_vaic(request):
    datos = {}

    if request.method == "POST":
        centro_id = request.POST.get("centro_id")
        mes = request.POST.get("mes")
        anio = request.POST.get("anio")
        tipo = request.POST.get("tipo")

        mesA = datetime.now().month
        anioA = datetime.now().year

        userName = request.session.get("userName")

        try:
            # SP VALIDACIÓN TOTAL
            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_VALIDAR_ALL_MESES_PRESPUESTADOS_PROYECTADOS",
                    [centro_id, mesA, anioA, tipo],
                )
                resultTotal = cursor.fetchall()
                columns = [col[0] for col in cursor.description]

            if resultTotal:
                for rt in resultTotal:
                    row = dict(zip(columns, rt))
                    datos["total"] = row.get("creacion_total", 0)

                    if row.get("creacion_total") == 1:
                        with connections["universal"].cursor() as cursor:
                            cursor.callproc(
                                "VAIC_FINALIZAR_INIT_PRESUPUESTOS",
                                [centro_id, mes, anio, userName],
                            )
                            validate = cursor.fetchall()
                            v_columns = [col[0] for col in cursor.description]

                        if validate:
                            for vv in validate:
                                row_v = dict(zip(v_columns, vv))
                                datos["existe"] = row_v.get("existe", 0)

                                if row_v.get("existe") == 1:
                                    with connections["universal"].cursor() as cursor:
                                        cursor.callproc(
                                            "DAC_INSERT_LOG_EVENTO",
                                            [
                                                "PRESUPUESTOS",
                                                f"{userName} HA GUARDADO LOS PRESUPUESTOS DEL CENTRO CON # {centro_id}",
                                                userName,
                                                "vaic_presupuestos_ingresados",
                                            ],
                                        )
                        else:
                            datos["existe"] = 0
            else:
                datos["total"] = 0

            datos["save"] = 1

        except Exception as e:
            datos["save"] = 0
            datos["error"] = str(e)

    else:
        datos["save"] = 0
        datos["error"] = "Método no permitido"

    return JsonResponse(datos)


def replicar_presupuestos_centro_vaic(request):
    datos = {}

    if request.method == "POST":
        centro_id = request.POST.get("centro")
        varMes_i = request.POST.get("mes_i")
        varAnio_i = request.POST.get("anio_i")
        varMes = request.POST.get("mes")
        varAnio = request.POST.get("anio")
        tipo = request.POST.get("tipo")

        userName = request.session.get("userName")

        try:
            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_REPLICAR_PRESUPUESTOS",
                    [centro_id, tipo, varMes_i, varAnio_i, varMes, varAnio, userName],
                )
                results = cursor.fetchall()
                columns = [col[0] for col in cursor.description]

            for row in results:
                row_dict = dict(zip(columns, row))
                datos["existe"] = row_dict.get("existe")
                datos["futuro"] = row_dict.get("futuro")

            datos["save"] = 1

        except Exception as e:
            datos["save"] = 0
            datos["error"] = str(e)

    else:
        datos["save"] = 0
        datos["error"] = "Método no permitido"

    return JsonResponse(datos)


def replicar_presupuestos_ingresos_centro(request):
    if request.method == "POST":
        centro_id = request.POST.get("id_centro")
        mesR = request.POST.get("mes_replicar")
        anioR = request.POST.get("anio_replicar")
        mes = request.POST.get("mes_actual")
        anio = request.POST.get("anio_actual")

        userName = request.session.get("userName")  # sin prefijo dac_

        datos = {}
        try:
            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_REPLICAR_GASTOS_INGRESOS_X_CENTRO",
                    [mesR, anioR, mes, anio, centro_id, userName],
                )
            datos["save"] = 1
        except Exception as e:
            datos["save"] = 0
            datos["error"] = str(e)

        return JsonResponse(datos)


def fill_table_cuentas_contables_cat(request, opc):
    userName = request.session.get("userName")  # sin "dac_"
    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_LIST_CAT_CUENTAS_CONTABLES", [opc])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return JsonResponse({"success": True, "data": results})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def fill_table_desglose_vendedores(request, id, mes1, anio1, mes2, anio2):
    userName = request.session.get("userName")  # sin "dac_" como pediste

    with connections["universal"].cursor() as cursor:
        cursor.callproc(
            "VAIC_LIST_DESGLOSE_VENDEDORES_X_CENTRO", [id, mes1, anio1, mes2, anio2]
        )
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return JsonResponse({"success": True, "data": data})


def anular_proyeccion_vendedor(request):
    if request.method == "POST":
        id_desgloce_vendedor = request.POST.get("id_desgloce_vendedor")
        userName = request.session.get("userName")  # sin 'dac_'

        try:
            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_ANULAR_DESGLOSE_VENDEDOR", [id_desgloce_vendedor, userName]
                )

            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "DAC_INSERT_LOG_EVENTO",
                    [
                        "PROY. VENDEDORES",
                        f"{userName} HA ANULADO LA PROYECCION CON # {id_desgloce_vendedor}",
                        userName,
                        "vaic_proyecciones_vendedores",
                    ],
                )

            return JsonResponse({"save": 1})
        except Exception as e:
            return JsonResponse({"save": 0, "error": str(e)})

    return JsonResponse({"save": 0, "error": "Método no permitido"})


def edit_proyeccion_vendedor(request):
    if request.method == "POST":
        varID = request.POST.get("varID")
        vendedor = request.POST.get("vendedor")
        costo = request.POST.get("costo")
        venta = request.POST.get("venta")
        utilidad = request.POST.get("utilidad")
        margen = request.POST.get("margen")
        recaudacion = request.POST.get("recaudacion")
        minimo_cliente = request.POST.get("minimo_cliente")
        meta_clientes = request.POST.get("meta_clientes")
        checkOptionComision = request.POST.get("checkOptionComision")
        mes = request.POST.get("mes")
        anio = request.POST.get("anio")

        userName = request.session.get("userName")  # sin dac_

        try:
            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_UPDATE_DESGLOSE_VENDEDOR",
                    [
                        varID,
                        vendedor,
                        costo,
                        venta,
                        utilidad,
                        margen,
                        mes,
                        anio,
                        userName,
                        checkOptionComision,
                        recaudacion,
                        minimo_cliente,
                        meta_clientes,
                    ],
                )

            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "DAC_INSERT_LOG_EVENTO",
                    [
                        "PROY. VENDEDORES",
                        f"{userName} HA EDITADO LA PROYECCION DEL VENDEDOR {vendedor} CON # {varID}",
                        userName,
                        "vaic_proyecciones_vendedores",
                    ],
                )

            return JsonResponse({"save": 1})
        except Exception as e:
            return JsonResponse({"save": 0, "error": str(e)})

    return JsonResponse({"save": 0, "error": "Método no permitido"})


def request_updated_data(request):
    if request.method == "POST":
        centro_id = request.POST.get("centro_id")
        varMes = request.POST.get("varMes")
        varAnio = request.POST.get("varAnio")

        userName = request.session.get("userName")  # sin dac_

        try:
            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_GET_DATA_X_CENTRO_ACCESO",
                    [centro_id, varMes, varAnio, userName, "13050"],
                )
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

                if rows:
                    row = dict(zip(columns, rows[0]))

                    datos = {
                        "presupuesto_p": row.get("valor_proyectado"),
                        "presupuesto_a": row.get("valor_autorizado"),
                        "gasto_indirecto_solicitado_ami": row.get(
                            "gasto_indirecto_solicitado_ami"
                        ),
                        "gastos_ingresados_bancario": row.get(
                            "gastos_ingresados_bancario"
                        ),
                        "proyeccion_disponible_centro": row.get(
                            "proyeccion_disponible_centro"
                        ),
                        "proyeccion_disponible_centro_porc": row.get(
                            "proyeccion_disponible_centro_porc"
                        ),
                        "presupuesto_de_gasto_disponible": row.get(
                            "presupuesto_de_gasto_disponible"
                        ),
                        "presupuesto_de_gasto_porc": row.get(
                            "presupuesto_de_gasto_porc"
                        ),
                        "presupuesto_cn": row.get("presupuesto_cn"),
                        "presupuesto_disponible_cn": row.get(
                            "presupuesto_disponible_cn"
                        ),
                        "presupuesto_disponible_porc_cn": row.get(
                            "presupuesto_disponible_porc_cn"
                        ),
                        "diferencia_utilidad_disponible_presupuestar": row.get(
                            "diferencia_utilidad_disponible_presupuestar"
                        ),
                        "diferencia_utilidad_disponible_para_presupuestar": row.get(
                            "diferencia_utilidad_disponible_para_presupuestar"
                        ),
                        "disponible_proyectado_indirecto_proyectado": row.get(
                            "disponible_proyectado_indirecto_proyectado"
                        ),
                        "presupuesto_guardado": row.get("presupuesto_guardado"),
                        "presupuesto_disponible_gastos": row.get(
                            "presupuesto_disponible_gastos"
                        ),
                        "valor_indirecto_solicitar": row.get(
                            "valor_indirecto_solicitar"
                        ),
                        "gasto_que_debo_solicitar": row.get("gasto_que_debo_solicitar"),
                    }
                else:
                    datos = {
                        "presupuesto_p": 0.00,
                        "presupuesto_a": 0.00,
                        "gasto_indirecto_solicitado_ami": 0.00,
                        "gastos_ingresados_bancario": 0.00,
                        "proyeccion_disponible_centro": 0.00,
                        "proyeccion_disponible_centro_porc": 0.00,
                        "presupuesto_de_gasto_disponible": 0.00,
                        "presupuesto_de_gasto_porc": 0.00,
                        "presupuesto_cn": 0.00,
                        "presupuesto_disponible_cn": 0.00,
                        "presupuesto_disponible_porc_cn": 0.00,
                        "diferencia_utilidad_disponible_presupuestar": 0,
                        "diferencia_utilidad_disponible_para_presupuestar": 0,
                        "disponible_proyectado_indirecto_proyectado": 0,
                        "presupuesto_guardado": 0,
                        "presupuesto_disponible_gastos": 0,
                        "valor_indirecto_solicitar": 0,
                        "gasto_que_debo_solicitar": 0,
                    }

            datos["save"] = 1
        except Exception as e:
            datos = {"save": 0, "error": str(e)}

        return JsonResponse(datos)

    return JsonResponse({"save": 0, "error": "Método no permitido"})


def update_presupuesto_ingreso(request):
    if request.method == "POST":
        ingreso_id = request.POST.get("ingreso_id")
        valor_nuevo = request.POST.get("valor_nuevo")

        userName = request.session.get("userName")  # sin "dac_"

        try:
            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_UPDATE_VALOR_INGRESO", [ingreso_id, valor_nuevo, userName]
                )

            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "DAC_INSERT_LOG_EVENTO",
                    [
                        "INGRESOS",
                        f"{userName} HA EDITADO EL INGRESO PRESUPUESTADO CON # {ingreso_id}",
                        userName,
                        "vaic_ingresos",
                    ],
                )

            return JsonResponse({"save": 1})

        except Exception as e:
            return JsonResponse({"save": 0, "error": str(e)})

    return JsonResponse({"save": 0, "error": "Método no permitido"})


def anular_presupuesto_ingreso(request):
    if request.method == "POST":
        ingreso_id = request.POST.get("ingreso_id")
        userName = request.session.get("userName")  # sin "dac_"

        try:
            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_DELETE_INGRESO_PRESUPUESTO", [ingreso_id, userName]
                )

            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "DAC_INSERT_LOG_EVENTO",
                    [
                        "INGRESOS",
                        f"{userName} HA ANULADO EL INGRESO PRESUPUESTADO CON # {ingreso_id}",
                        userName,
                        "vaic_ingresos",
                    ],
                )

            return JsonResponse({"save": 1})

        except Exception as e:
            return JsonResponse({"save": 0, "error": str(e)})

    return JsonResponse({"save": 0, "error": "Método no permitido"})


def dataCentros(request):
    mes = request.POST.get("mes")
    anio = request.POST.get("anio")
    tipo = request.POST.get("tipo")

    userName = request.session.get("userName", "")

    adminIT = request.session.get("ctrlGestionAdminIT", 0)
    accesoTotalVAIC = request.session.get("13050", 0)

    if adminIT == 1 or adminIT == "1":
        acceso = 13050
    else:
        acceso = accesoTotalVAIC

    if accesoTotalVAIC == 1:
        acceso = 13050

    try:
        udcConn = connections["universal"]
        with udcConn.cursor() as cursor:
            cursor.callproc(
                "VAIC_LIST_ALL_CENTROS", [mes, anio, tipo, userName, acceso]
            )
            column_names = [desc[0] for desc in cursor.description]
            centrosData = [
                dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
            ]

        udcConn.close()

        return JsonResponse({"data": centrosData})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataResponsablesDisponibles(request):
    centro_id = request.POST.get("centro_id")

    userName = request.session.get("userName", "")

    try:
        udcConn = connections["universal"]
        with udcConn.cursor() as cursor:
            cursor.callproc("VAIC_LIST_USUARIOS_NOT_IN_CENTRO", [centro_id])
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            usersData = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                usersData.append(row_dict)

        udcConn.close()

        return JsonResponse({"data": usersData})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataResponsablesCentro(request):
    centro_id = request.POST.get("centro_id")

    userName = request.session.get("userName", "")

    try:
        udcConn = connections["universal"]
        with udcConn.cursor() as cursor:
            cursor.callproc("VAIC_LIST_RESPONSABLES_X_CENTRO", [centro_id])
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            usersData = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                usersData.append(row_dict)

        udcConn.close()

        return JsonResponse({"data": usersData})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataCanalesFormato(request):
    formato = request.POST.get("formato")

    userName = request.session.get("userName", "")

    try:
        udcConn = connections["universal"]
        with udcConn.cursor() as cursor:
            cursor.callproc("VAIC_LIST_ALL_CANALES_VENTA", [formato])
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            canalesData = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                canalesData.append(row_dict)

        udcConn.close()

        return JsonResponse({"data": canalesData})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def addResponsablesCentro(request):
    try:
        centro_id = request.POST.get("centro_id")
        cuenta_nic = request.POST.get("cuenta_nic")
        responsable = request.POST.get("userName")

        userName = request.session.get("userName", "")

        appConn = connections["universal"]
        with appConn.cursor() as cursor:
            cursor.callproc(
                "VAIC_INSERT_RESPONSABLE", [centro_id, responsable, userName]
            )
            results = cursor.fetchall()

        appConn.close()

        datos = {"save": 1}
    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def removeResponsablesCentro(request):
    try:
        centro_id = request.POST.get("centro_id")
        cuenta_nic = request.POST.get("cuenta_nic")

        userName = request.session.get("userName", "")

        appConn = connections["universal"]
        with appConn.cursor() as cursor:
            cursor.callproc(
                "VAIC_INSERT_RESPONSABLE", [centro_id, responsable, userName]
            )
            results = cursor.fetchall()

        appConn.close()

        datos = {"save": 1}
    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def insert_update_centro_vaic(request):
    try:
        centro_id = request.POST.get("centro_id")
        centro_opcion = request.POST.get("centro_opcion")
        centro_nombre = request.POST.get("centro_nombre")
        centro_tipo = request.POST.get("centro_tipo")
        centro_departamento = request.POST.get("centro_departamento")
        centro_formato = request.POST.get("centro_formato")
        centro_canal = request.POST.get("centro_canal")
        centro_canal_text = request.POST.get("centro_canal_text")
        centro_descripcion = request.POST.get("centro_descripcion")
        responsable_centro = request.POST.get("responsable_centro")
        centro_cuenta = request.POST.get("centro_cuenta")
        centro_empresa = request.POST.get("centro_empresa")

        userName = request.session.get("userName", "")

        datos = {}

        appConn = connections["universal"]
        with appConn.cursor() as cursor:
            cursor.callproc(
                "VAIC_INSERT_UPDATE_CENTRO",
                [
                    centro_id,
                    centro_opcion,
                    centro_nombre,
                    centro_descripcion,
                    centro_tipo,
                    centro_departamento,
                    centro_formato,
                    centro_canal,
                    centro_canal_text,
                    userName,
                    centro_cuenta,
                    centro_empresa,
                ],
            )
            resultado = cursor.fetchall()

        if resultado:
            for fila in resultado:
                existe = fila[0]
                varID = fila[1]

                datos["existe"] = existe
                datos["varID"] = varID

                if existe == 0:
                    if str(centro_opcion) == "1":
                        accion = "INSERTAR"
                        accionP = "CREADO"

                        # Insertar responsable por defecto
                        with appConn.cursor() as cursor:
                            cursor.callproc(
                                "VAIC_INSERT_RESPONSABLE",
                                [varID, responsable_centro, userName],
                            )
                    else:
                        accion = "EDITAR"
                        accionP = "EDITADO"

                    with appConn.cursor() as cursor:
                        cursor.callproc(
                            "DAC_INSERT_LOG_EVENTO",
                            [accion, descripcion_log, userName, "vaic_cat_centros"],
                        )

        appConn.close()

        datos = {"save": 1}
    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def validate_autorizacion_tipo(request):
    try:
        tipo_autorizacion = request.POST.get("tipo_autorizacion")
        username = request.POST.get("username")
        password = request.POST.get("password")

        existe = 0

        appConn = connections["universal"]
        with appConn.cursor() as cursor:
            cursor.callproc(
                "VAIC_SOLICITAR_AUTORIZACION", [tipo_autorizacion, username, password]
            )
            resultado = cursor.fetchall()

        if resultado:
            for fila in resultado:
                existe = fila[0]

        appConn.close()

        datos = {"save": 1, "existe": existe}
    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def ctrl_gestion_realizar_cierre_centros(request):
    try:
        mes = request.POST.get("varMes")
        anio = request.POST.get("varAnio")

        userName = request.session.get("userName", "")

        datos = {}

        appConn = connections["universal"]
        with appConn.cursor() as cursor:
            cursor.callproc("VAIC_CERRAR_CENTRO_PERIODO", [mes, anio, userName])
            column_names = [desc[0] for desc in cursor.description]
            resultado = cursor.fetchall()

            for fila in resultado:
                fila_dict = dict(zip(column_names, fila))

                datos["cierre"] = fila_dict["cierre"]
                datos["realizado"] = fila_dict["realizado"]
                datos["message"] = fila_dict["message"]

                if fila_dict["cierre"] == 0:
                    descripcion = (
                        userName
                        + " HA REALIZADO EL CIERRE DEL MES # "
                        + str(mes)
                        + " DEL AÑO "
                        + str(anio)
                    )
                    with appConn.cursor() as cursor2:
                        cursor2.callproc(
                            "DAC_INSERT_LOG_EVENTO",
                            ["CIERRE", descripcion, userName, "vaic_cierre_centro"],
                        )

        appConn.close()
        datos["save"] = 1

    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def update_presupuesto_proforma_vaic(request):
    if request.method == "POST":
        id = request.POST.get("id")
        editar_presupuesto_nuevo = request.POST.get("valor")
        mes = request.POST.get("mes")
        anio = request.POST.get("anio")

        userName = request.session.get("userName")  # sin prefijo dac_

        try:
            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_UPDATE_PRESUPUESTO_PROFORMA",
                    [id, editar_presupuesto_nuevo, userName, mes, anio],
                )

            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "DAC_INSERT_LOG_EVENTO",
                    [
                        "PRESUPUESTOS",
                        f"{userName} HA EDITAR EL PRESUPUESTO # {editar_presupuesto_nuevo} CON UN NUEVO DE L.{editar_presupuesto_nuevo}",
                        userName,
                        "vaic_presupuestos",
                    ],
                )

            return JsonResponse({"save": 1})

        except Exception as e:
            return JsonResponse({"save": 0, "error": str(e)})

    return JsonResponse({"save": 0, "error": "Método no permitido"})


def save_configuracion_porcentajes_centros(request):
    if request.method == "POST":
        try:
            centro = request.POST.get("centro")
            centro_name = request.POST.get("centro_name")
            mes = request.POST.get("mes")
            anio = request.POST.get("anio")
            assigned_centros = json.loads(
                request.POST.get("assignedCentros", "[]")
            )  # Se espera string JSON

            userName = request.session.get("userName")  # sin prefijo "dac_"

            for aC in assigned_centros:
                id_secuencia = aC.get("id_secuencia")
                porcentaje = aC.get("porcentaje")
                editado = aC.get("editado")
                anterior = aC.get("anterior")
                centro_solicitar = aC.get("centro")
                monto_solicitar_old = aC.get("monto_solicitar_old")
                monto_solicitar = aC.get("monto_solicitar")
                signo = aC.get("signo")

                if signo == "?":
                    monto_solicitar = 0.00

                with connections["universal"].cursor() as cursor:
                    cursor.callproc(
                        "VAIC_UPDATE_CONFIGURACION_PORCENTAJES_X_CENTRO",
                        [porcentaje, userName, id_secuencia, monto_solicitar],
                    )

            return JsonResponse({"save": 1})
        except Exception as e:
            return JsonResponse({"save": 0, "error": str(e)})

    return JsonResponse({"save": 0, "error": "Método no permitido"})


def finalizar_presupuestos_vaic(request):
    if request.method == "POST":
        id_presupuesto = request.POST.get("id_presupuesto")
        opcion = request.POST.get("opcion")
        userName = request.session.get("userName")  # sin "dac_"

        try:
            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_GUARDAR_ELIMINAR_PRESUPUESTO",
                    [id_presupuesto, opcion, userName],
                )

            with connections["universal"].cursor() as cursor:
                mensaje = f"{userName} HA GUARDADO/ELIMINADO EL PRESUPUESTO CON # {id_presupuesto}"
                cursor.callproc(
                    "DAC_INSERT_LOG_EVENTO",
                    ["VALIDAR", mensaje, userName, "vaic_presupuestos"],
                )

            return JsonResponse({"save": 1})

        except Exception as e:
            return JsonResponse({"save": 0, "error": str(e)})


def update_gasto_presupuesto(request):
    if request.method == "POST":
        id_presupuesto = request.POST.get("id_presupuesto")
        nuevo_valor = request.POST.get("nuevoValor")
        userName = request.session.get("userName")  # sin "dac_"

        try:
            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_UPDATE_GASTO_PRESUPUESTO",
                    [id_presupuesto, nuevo_valor, userName],
                )
            return JsonResponse({"save": 1})
        except Exception as e:
            return JsonResponse({"save": 0, "error": str(e)})


def convertir_a_compatibles(column_names, rows):
    datos = []
    for row in rows:
        row_dict = {}
        for col, val in zip(column_names, row):
            if isinstance(val, bytes):
                row_dict[str(col)] = int.from_bytes(val, byteorder="little")
            else:
                row_dict[str(col)] = val
        datos.append(row_dict)
    return datos


def fill_table_presupuesto_anual(request):
    centro = request.GET.get("centro")
    anio = request.GET.get("anio")
    userName = request.session.get("userName")

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_LIST_PRESUPUESTO_ANUAL_CUENTAS_BALANCE_CENTRO", [anio, centro]
            )
            column_names = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            result = convertir_a_compatibles(column_names, rows)
        return JsonResponse({"success": True, "data": result})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def fill_table_ingresos_presupuestados(request):
    id = request.GET.get("id")
    mes = request.GET.get("mes")
    anio = request.GET.get("anio")
    autoriza = request.GET.get("autoriza")
    userName = request.session.get("userName")
    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_LIST_DETALLE_INGRESOS_X_CENTRO", [id, mes, anio])
            column_names = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            ingresos_data = convertir_a_compatibles(column_names, rows)
        return JsonResponse({"success": True, "data": ingresos_data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def fill_table_gastos(request):
    id = request.GET.get("id")
    mes = request.GET.get("mes")
    anio = request.GET.get("anio")
    tipo = request.GET.get("tipo")
    view = request.GET.get("view")
    userName = request.session.get("userName")
    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_LIST_GASTOS_X_TIPO", [id, mes, anio, tipo, view])
            column_names = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            gastos_data = convertir_a_compatibles(column_names, rows)
        return JsonResponse({"success": True, "data": gastos_data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def fill_table_porcentajes_solicitar(request):
    centro = request.GET.get("centro")
    mes = request.GET.get("mes")
    anio = request.GET.get("anio")
    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_PORCENTAJES_LIST_CENTROS_X_NOT_CENTER", [centro, mes, anio]
            )
            column_names = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            centros_data = convertir_a_compatibles(column_names, rows)
        return JsonResponse({"success": True, "data": centros_data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def fill_table_meses_presupuestados(request):
    centro = request.GET.get("centro")
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year
    userName = request.session.get("userName")
    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_LIST_MESES_PRESUPUESTADOS", [centro, mes_actual, anio_actual]
            )
            column_names = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            meses_data = convertir_a_compatibles(column_names, rows)
        return JsonResponse({"success": True, "data": meses_data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def fill_table_cuentas_contables(request):
    tipo = request.GET.get("tipo")
    centro = request.GET.get("centro")
    mes = request.GET.get("mes")
    anio = request.GET.get("anio")
    userName = request.session.get("userName")
    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_LIST_ALL_CUENTAS_CONTABLES", [tipo, centro, mes, anio]
            )
            column_names = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            results = convertir_a_compatibles(column_names, rows)
        return JsonResponse({"success": True, "data": results})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def fill_table_gastos_presupuestados(request):
    id = request.GET.get("id")
    mes = request.GET.get("mes")
    anio = request.GET.get("anio")
    autoriza = request.GET.get("autoriza")
    userName = request.session.get("userName")
    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_LIST_GASTOS_PRESUPUESTADOS", [id, mes, anio, autoriza]
            )
            column_names = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            gastos_data = convertir_a_compatibles(column_names, rows)
        return JsonResponse({"success": True, "data": gastos_data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def fill_table_ajustes_cuentas(request):
    centro = request.GET.get("centro")
    mes = request.GET.get("mes")
    anio = request.GET.get("anio")
    userName = request.session.get("userName")

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_LIST_AJUSTES_CUENTAS_X_CENTRO", [centro, mes, anio])
            column_names = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            ajustes_data = []
            for row in rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                ajustes_data.append(row_dict)

        return JsonResponse({"success": True, "data": ajustes_data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def finalizar_presupuestos_vaic(request):
    if request.method != "POST":
        return JsonResponse({"save": 0, "error": "Método no permitido"}, status=405)

    id_presupuesto = request.POST.get("id_presupuesto")
    opcion = request.POST.get("opcion")
    userName = request.session.get("userName")  # sin "dac_"

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_GUARDAR_ELIMINAR_PRESUPUESTO", [id_presupuesto, opcion, userName]
            )
            cursor.callproc(
                "DAC_INSERT_LOG_EVENTO",
                [
                    "VALIDAR",
                    f"{userName} HA GUARDADO/ELIMINADO EL PRESUPUESTO CON # {id_presupuesto}",
                    userName,
                    "vaic_presupuestos",
                ],
            )

        return JsonResponse({"save": 1})
    except Exception as e:
        return JsonResponse({"save": 0, "error": str(e)})


def validate_presupuestos_creados_vaic(request):
    if request.method != "POST":
        return JsonResponse({"save": 0, "error": "Método no permitido"}, status=405)

    centro_id = request.POST.get("centro_id")
    mes = request.POST.get("varMes")
    anio = request.POST.get("varAnio")
    userName = request.session.get("userName")  # sin "dac_"

    datos = {}

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_VALIDATE_PRESUPUESTOS_CREADOS", [centro_id, mes, anio]
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            existe = 0
            for row in rows:
                row_dict = dict(zip(columns, row))
                existe = row_dict.get("conteo_existe", 0)

                if existe == 0:
                    cursor.callproc(
                        "DAC_INSERT_LOG_EVENTO",
                        [
                            "VALIDAR",
                            f"{userName} HA VALIDADO LA CREACION DEL PRESUPUESTO PARA EL CENTRO CON # {centro_id}",
                            userName,
                            "vaic_servicios_centros",
                        ],
                    )

            datos["existe"] = existe
            datos["save"] = 1
    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


def validate_proyeccion_presupuesto_vaic(request):
    id = request.GET.get("centro_id")
    mes = request.GET.get("varMes")
    anio = request.GET.get("varAnio")
    tipo = request.GET.get("tipo")
    userName = request.session.get("userName")

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_VALIDATE_PROYECCION_CREADA_GASTO_INDIRECTO", [id, mes, anio, tipo]
            )
            rows = cursor.fetchall()

            datos = {"existe": 1 if rows else 0, "save": 1}

    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def solicitar_autorizacion(request):
    tipo_autorizacion = request.GET.get("tipo_autorizacion")
    username = request.GET.get("username")
    password = request.GET.get("password")

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_SOLICITAR_AUTORIZACION", [tipo_autorizacion, username, password]
            )
            rows = cursor.fetchall()

            if rows:
                datos = {"existe": rows[0][0], "save": 1}
            else:
                datos = {"existe": 0, "save": 1}

    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def validate_proyeccion_presupuesto_vaic(request):
    id = request.GET.get("centro_id")
    mes = request.GET.get("varMes")
    anio = request.GET.get("varAnio")
    tipo = request.GET.get("tipo")

    userName = request.session.get("userName")  # sin "dac_"

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_VALIDATE_PROYECCION_CREADA_GASTO_INDIRECTO", [id, mes, anio, tipo]
            )
            rows = cursor.fetchall()

            datos = {"existe": 1 if rows else 0, "save": 1}

    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def save_edit_presupuesto_vaic(request):
    try:
        centro_id = request.POST.get("id_centro_actual")
        varMes = request.POST.get("varMes")
        varAnio = request.POST.get("varAnio")
        tipo = int(request.POST.get("tipo"))
        tipoCuenta = request.POST.get("tipoCuenta")
        userName = request.session.get("userName")

        assignedAccounts = request.POST.get("assignedAccounts")
        try:
            if isinstance(assignedAccounts, str):
                assignedAccounts = json.loads(assignedAccounts or "[]")
            else:
                assignedAccounts = []
        except Exception:
            assignedAccounts = []

        def call_and_drain(cursor, sql, params):
            cursor.callproc(sql, params)
            if cursor.description:
                cursor.fetchall()
            while cursor.nextset():
                if cursor.description:
                    cursor.fetchall()

        validacion = 2 if tipo == 1 else 0

        for account in assignedAccounts:
            id_cuenta_contable = account["id_cuenta_contable"]
            cuena_contable = account["cuena_contable"]
            nombre_cuenta = account["nombre_cuenta"]
            presupuesto = account["presupuesto"]

            with connections["universal"].cursor() as cursor:
                if tipoCuenta == "Gasto":
                    call_and_drain(
                        cursor,
                        "VAIC_INSERT_UPDATE_PRESUPUESTO",
                        [
                            centro_id,
                            id_cuenta_contable,
                            cuena_contable,
                            nombre_cuenta,
                            presupuesto,
                            varMes,
                            varAnio,
                            userName,
                            validacion,
                        ],
                    )
                    call_and_drain(
                        cursor,
                        "DAC_INSERT_LOG_EVENTO",
                        [
                            "PRESUPUESTO",
                            f"{userName} HA PRESUPUESTADO LA CUENTA CONTABLE DE GASTO {nombre_cuenta} CON NUMERO DE CUENTA {cuena_contable} Y CON UN VALOR DE L. {presupuesto}",
                            userName,
                            "vaic_presupuestos",
                        ],
                    )
                else:
                    call_and_drain(
                        cursor,
                        "VAIC_INSERT_UPDATE_PRESUPUESTO_INGRESO",
                        [
                            centro_id,
                            id_cuenta_contable,
                            cuena_contable,
                            nombre_cuenta,
                            presupuesto,
                            varMes,
                            varAnio,
                            userName,
                            validacion,
                        ],
                    )
                    call_and_drain(
                        cursor,
                        "DAC_INSERT_LOG_EVENTO",
                        [
                            "PRESUPUESTO",
                            f"{userName} HA PRESUPUESTADO LA CUENTA CONTABLE DE INGRESO {nombre_cuenta} CON NUMERO DE CUENTA {cuena_contable} Y CON UN VALOR DE L. {presupuesto}",
                            userName,
                            "vaic_ingresos",
                        ],
                    )

                result = cursor.fetchall()
                if result:
                    for row in result:
                        datos = {
                            "existe": row[0]
                        }  # asumiendo que devuelve una sola columna `existe`
                else:
                    datos = {"existe": 0}

        datos["save"] = 1

    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def save_edit_proyeccion_vendedores_vaic(request):
    try:
        centro_id = request.POST.get("id_centro_actual")
        presupuesto_mes = request.POST.get("varMes")
        presupuesto_anio = request.POST.get("varAnio")
        userName = request.session.get("userName")

        assignedVendedores = json.loads(request.POST.get("assignedVendedores"))

        for vendedor in assignedVendedores:
            nombre_vendedor = vendedor["vendedor"]
            costo = vendedor["costo"]
            venta = vendedor["venta"]
            utilidad = vendedor["utilidad"]
            margen = vendedor["margen"]
            aplicaComision = vendedor["aplicaComision"]
            recaudacion = vendedor["recaudacion"]
            minimo_cliente = vendedor["minimo_cliente"]
            meta_clientes = vendedor["meta_clientes"]

            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_INSERT_UPDATE_PROYECCION_VENDEDORES",
                    [
                        centro_id,
                        nombre_vendedor,
                        costo,
                        venta,
                        utilidad,
                        margen,
                        presupuesto_mes,
                        presupuesto_anio,
                        userName,
                        aplicaComision,
                        recaudacion,
                        minimo_cliente,
                        meta_clientes,
                    ],
                )

                # 👇 Consumir resultados pendientes
                while cursor.nextset():
                    pass

                cursor.callproc(
                    "DAC_INSERT_LOG_EVENTO",
                    [
                        "PROYECCION",
                        f"{userName} HA PROYECTADO AL VENDEDOR {nombre_vendedor} DEL CENTRO DE NEGOCIOS # {centro_id} UN COSTO DE L. {costo} , UNA VENTA DE L. {venta}",
                        userName,
                        "vaic_proyecciones_vendedores",
                    ],
                )

                while cursor.nextset():
                    pass

        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_PROYECCION_GENERAL_CENTRO",
                [centro_id, presupuesto_mes, presupuesto_anio, userName],
            )

            while cursor.nextset():
                pass

        return JsonResponse({"save": 1})

    except Exception as e:
        return JsonResponse({"save": 0, "error": str(e)})


def validate_proyeccion_presupuesto_vaic(request):
    id = request.POST.get("centro_id")
    mes = request.POST.get("varMes")
    anio = request.POST.get("varAnio")
    tipo = request.POST.get("tipo")

    userName = request.session.get("userName")  # sin dac_

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_VALIDATE_PROYECCION_CREADA_GASTO_INDIRECTO", [id, mes, anio, tipo]
            )
            rows = cursor.fetchall()

            datos = {"existe": 1 if rows else 0, "save": 1}
    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def get_monto_solicitar_indirecto_centro(request):
    id_centro = request.POST.get("id_centro")
    id_centro_indirecto = request.POST.get("id_centro_indirecto")
    mes = request.POST.get("mes")
    anio = request.POST.get("anio")

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_PORCENTAJES_INDIRECTO_SOLICITAR_CENTRO",
                [id_centro, mes, anio, id_centro_indirecto],
            )
            rows = cursor.fetchall()

            if rows:
                datos = {
                    "monto_solicitar": rows[0][
                        0
                    ],  # suponiendo que devuelve solo un valor
                    "save": 1,
                }
            else:
                datos = {"monto_solicitar": 0, "save": 1}

    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def update_presupuesto_ajuste_vaic(request):
    id = request.POST.get("id")
    editar_presupuesto_nuevo = request.POST.get("valor")
    mes = request.POST.get("mes")
    anio = request.POST.get("anio")
    userName = request.session.get("userName")

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_UPDATE_PRESUPUESTO_AJUSTE_CUENTA",
                [id, editar_presupuesto_nuevo, userName, mes, anio],
            )

            log_mensaje = f"{userName} HA AUTORIZADO EL AJUSTE DEL PRESUPUESTO # {editar_presupuesto_nuevo} CON UN NUEVO DE L.{editar_presupuesto_nuevo}"
            cursor.callproc(
                "DAC_INSERT_LOG_EVENTO",
                ["PRESUPUESTOS", log_mensaje, userName, "vaic_presupuestos_ajustes"],
            )

        datos = {"save": 1}

    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def fill_select_servicios(request):
    centro_id = request.GET.get("centro_id")

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_LIST_SERVICIOS_CENTRO", [1, centro_id])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            html = '<option value="">Seleccione un Servicio</option>'
            for row in rows:
                row_dict = dict(zip(columns, row))
                html += f'<option value="{row_dict["id_servicio"]}">{row_dict["servicio"]}</option>'

        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"<option>Error: {str(e)}</option>")


def save_edit_gastos_indirectos(request):
    id_centro_indirecto = request.POST.get("id_centro_indirecto")
    id_centro_directo = request.POST.get("id_centro_directo")
    centro_gasto_tipo = request.POST.get("centro_gasto_tipo")
    gasto_total = request.POST.get("gasto_total")
    descripcion_gasto = request.POST.get("descripcion_gasto")
    varMes = request.POST.get("varMes")
    varAnio = request.POST.get("varAnio")
    assignedDetalles = json.loads(
        request.POST.get("assignedDetalles", "[]")
    )  # Viene como JSON string

    userName = request.session.get("userName")  # sin "dac_"

    value_zero = 0
    datos = {}

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_INSERT_GASTO_MAIN",
                [
                    value_zero,
                    centro_gasto_tipo,
                    id_centro_directo,
                    id_centro_indirecto,
                    value_zero,
                    gasto_total,
                    value_zero,
                    varMes,
                    varAnio,
                    userName,
                    descripcion_gasto,
                ],
            )
            row = cursor.fetchone()
            varID = row[0]  # suponiendo que retorna solo un campo como en Laravel

        datos["varID"] = varID

        for detalle in assignedDetalles:
            id_servicio = detalle["id_servicio"]
            servicio = detalle["servicio"]
            costo = detalle["costo"]

            with connections["universal"].cursor() as cursor:
                cursor.callproc(
                    "VAIC_INSERT_GASTO_DETALLE",
                    [varID, id_servicio, servicio, costo, userName],
                )
                cursor.callproc(
                    "DAC_INSERT_LOG_EVENTO",
                    [
                        "GASTOS D",
                        f"{userName} HA CREADO EL DETALLE DEL GASTO INDIRECTO # {varID} - CON CONCEPTO DEL SERVICIO {servicio} Y CON UN VALOR DE L.{costo}",
                        userName,
                        "vaic_gastos_detalles",
                    ],
                )

        datos["save"] = 1
    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


def fill_table_detalles_gastos(request):
    id = request.GET.get("id")
    userName = request.session.get("userName")

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_LIST_DETALLE_GASTOS_X_GASTO", [id])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            detalles = [dict(zip(columns, row)) for row in rows]

        return JsonResponse({"success": True, "data": detalles})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def anular_presupuesto(request):
    id = request.POST.get("id")
    userName = request.session.get("userName")

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_ANULAR_PRESUPUESTO", [id, userName])
            cursor.callproc(
                "DAC_INSERT_LOG_EVENTO",
                [
                    "PRESUPUESTOS",
                    f"{userName} HA ANULADO EL PRESUPUESTO # {id}",
                    userName,
                    "vaic_gastos",
                ],
            )
        return JsonResponse({"save": 1})
    except Exception as e:
        return JsonResponse({"save": 0, "error": str(e)})


def gestion_gasto_indirecto(request):
    gasto_id = request.POST.get("id")
    gasto_autorizado = request.POST.get("valor_autorizado")
    comentario = request.POST.get("comentario")
    validacion = int(request.POST.get("validacion"))
    userName = request.session.get("userName")

    accion = "APROBADO" if validacion == 1 else "RECHAZADO"

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_VALIDAR_GASTOS_INDIRECTOS",
                [gasto_id, gasto_autorizado, comentario, userName, validacion],
            )
            cursor.callproc(
                "DAC_INSERT_LOG_EVENTO",
                [
                    "GASTOS",
                    f"{userName} HA {accion} EL GASTO INDIRECTO # {gasto_id} CON UN NUEVO VALOR DE L.{gasto_autorizado}",
                    userName,
                    "vaic_gastos",
                ],
            )
        return JsonResponse({"save": 1})
    except Exception as e:
        return JsonResponse({"save": 0, "error": str(e)})


def gestion_presupuesto_final(request):
    id = request.POST.get("id")
    valor_autorizado = request.POST.get("valor_autorizado")
    comentario = request.POST.get("comentario")
    validacion = int(request.POST.get("validacion"))
    centro_id = request.POST.get("centro_id")
    mes = request.POST.get("mes")
    anio = request.POST.get("anio")
    userName = request.session.get("userName")

    accion = "APROBADO" if validacion == 1 else "RECHAZADO"

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_VALIDAR_PRESUPUESTO",
                [id, valor_autorizado, comentario, userName, validacion, mes, anio],
            )
            cursor.callproc(
                "DAC_INSERT_LOG_EVENTO",
                [
                    "PRESUPUESTOS",
                    f"{userName} HA {accion} EL PRESUPUESTO # {id} CON UN NUEVO VALOR DE L.{valor_autorizado}",
                    userName,
                    "vaic_gastos",
                ],
            )
            cursor.callproc("VAIC_FINALIZAR_REVISION", [centro_id, mes, anio])
            validate = cursor.fetchall()
            if validate:
                datos = {"finaliza": validate[0][0], "save": 1}
            else:
                datos = {"finaliza": "no_finalizar", "save": 1}
    except Exception as e:
        datos = {"save": 0, "error": str(e)}

    return JsonResponse(datos)


def finalizar_centro_vaic(request):
    id = request.POST.get("centro_id")
    mes = request.POST.get("varMes")
    anio = request.POST.get("varAnio")
    userName = request.session.get("userName")

    datos = {}

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_REALIZAR_CIERRE_MENSUAL_CENTRO", [id, mes, anio, userName]
            )
            cierre_data = cursor.fetchall()

        if cierre_data:
            suma_cierre = cierre_data[0][
                0
            ]  # asumimos que viene como _suma_total en la 1era columna
            datos["suma_cierre"] = suma_cierre

            if suma_cierre == 0:
                with connections["universal"].cursor() as cursor:
                    cursor.callproc("VAIC_FINALIZAR_CENTRO", [id, mes, anio, userName])
                    cursor.callproc(
                        "DAC_INSERT_LOG_EVENTO",
                        [
                            "FINALIZAR",
                            f"{userName} HA FINALIZADO DEL CENTRO # {id} EN EL MES # {mes} DEL AÑO {anio}",
                            userName,
                            "vaic_centros_finalizados",
                        ],
                    )

        datos["save"] = 1
    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


def fill_table_centro_servicios(request):
    opc = request.GET.get("opc")
    centro_id = request.GET.get("centro_id")
    userName = request.session.get("userName")
    datos = {}

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_LIST_SERVICIOS_CENTRO", [opc, centro_id])
            columns = [col[0] for col in cursor.description]
            servicios_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        datos["success"] = True
        datos["data"] = servicios_data
    except Exception as e:
        datos["success"] = False
        datos["error"] = str(e)

    return JsonResponse(datos)


def change_status_servicios_centro(request):
    servicio_id = request.POST.get("servicio_id")
    estado_value = request.POST.get("estado_value")

    userName = request.session.get("userName")
    datos = {}

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_UPDATE_STATUS_SERVICIO_CENTRO",
                [estado_value, servicio_id, userName],
            )
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "DAC_INSERT_LOG_EVENTO",
                [
                    "EDITAR",
                    f"{userName} HA CAMBIADO EL ESTADO DEL SERVICIO # {servicio_id}",
                    userName,
                    "vaic_servicios_centros",
                ],
            )

        datos["save"] = 1
    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


def save_edit_servicios_centro(request):
    centro_id = request.POST.get("centro_id")
    opcion = request.POST.get("opcion")
    servicio_id = request.POST.get("servicio_id")
    servicio = request.POST.get("servicio")
    servicio_desc = request.POST.get("servicio_desc")

    userName = request.session.get("userName")
    datos = {}

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_INSERT_UPDATE_SERVICIO_CENTRO",
                [opcion, centro_id, servicio_id, servicio, servicio_desc, userName],
            )
            validate = cursor.fetchall()

        if validate:
            for vvv in validate:
                datos["existe"] = (
                    vvv[0] if isinstance(vvv, (list, tuple)) else vvv.existe
                )

                if datos["existe"] == 0:
                    with connections["universal"].cursor() as cursor:
                        cursor.callproc(
                            "DAC_INSERT_LOG_EVENTO",
                            [
                                "INSERTAR",
                                f"{userName} HA CREADO EL SERVICIO # {servicio}",
                                userName,
                                "vaic_servicios_centros",
                            ],
                        )
        else:
            datos["existe"] = 0

        datos["save"] = 1
    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


def solicitar_ajuste_cuenta(request):
    centro_id = request.POST.get("centro_id")
    presupuesto_id = request.POST.get("presupuesto_id")
    valor_anterior = request.POST.get("valor_anterior")
    valor_nuevo = request.POST.get("valor_nuevo")
    mes = request.POST.get("mes")
    anio = request.POST.get("anio")

    userName = request.session.get("userName")
    datos = {}

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_SOLICITAR_AJUSTE_CUENTA",
                [
                    centro_id,
                    presupuesto_id,
                    valor_anterior,
                    valor_nuevo,
                    userName,
                    mes,
                    anio,
                ],
            )
            result = cursor.fetchall()

        if result:
            for r in result:
                datos["existe"] = r[0] if isinstance(r, (list, tuple)) else r.existe
        else:
            datos["existe"] = 0

        datos["save"] = 1
    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


def editar_ajuste_cuenta(request):
    centro_id = request.POST.get("centro_id")
    presupuesto_id = request.POST.get("presupuesto_id")
    valor_anterior = request.POST.get("valor_anterior")
    valor_nuevo = request.POST.get("valor_nuevo")
    mes = request.POST.get("mes")
    anio = request.POST.get("anio")

    userName = request.session.get("userName")
    datos = {}

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_UPDATE_AJUSTE_CUENTA",
                [
                    centro_id,
                    presupuesto_id,
                    valor_anterior,
                    valor_nuevo,
                    userName,
                    mes,
                    anio,
                ],
            )

        datos["save"] = 1
    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


def guardar_ajuste_cuenta(request):
    presupuesto_id = request.POST.get("id")
    mes = request.POST.get("mes")
    anio = request.POST.get("anio")

    userName = request.session.get("userName")
    datos = {}

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "VAIC_GUARDAR_AJUSTE_CUENTA", [presupuesto_id, mes, anio, userName]
            )

        datos["save"] = 1
    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


def update_rechazar_ajuste_vaic(request):
    id = request.POST.get("id")
    editar_presupuesto_nuevo = request.POST.get("valor")
    mes = request.POST.get("mes")
    anio = request.POST.get("anio")
    opcion = request.POST.get("opcion")

    userName = request.session.get("userName")
    datos = {}

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("VAIC_RECHAZAR_AJUSTE", [id, userName, opcion])

        with connections["universal"].cursor() as cursor:
            cursor.callproc(
                "DAC_INSERT_LOG_EVENTO",
                [
                    "PRESUPUESTOS",
                    f"{userName} HA RECHAZADO EL AJUSTE DEL PRESUPUESTO # {editar_presupuesto_nuevo} CON UN NUEVO DE L.{editar_presupuesto_nuevo}",
                    userName,
                    "vaic_presupuestos_ajustes",
                ],
            )

        datos["save"] = 1
    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


# INGRESOS FUERA PRESUPUESTO SIN GESTIONAR
def validate_existe_gastos_fuera_presupuesto(request):
    datos = {"save": 1, "existe": 0}
    try:
        userName = request.session.get("userName", "")

        # universal = SQL Server/MySQL según tu config
        conn_uni = connections["universal"]
        with conn_uni.cursor() as cursor:
            # SP sin parámetros
            cursor.callproc("VAIC_VALIDATE_GASTOS_SIN_GESTION_CIERRE")
            rows = cursor.fetchall() or []

            # Tomar 'existe' (primera col). Si tu SP devuelve un alias 'existe', es la col 0.
            if rows:
                # Soporta tanto tuplas como dict-rows
                first = rows[0]
                try:
                    datos["existe"] = (
                        first[0]
                        if isinstance(first, (list, tuple))
                        else first.get("existe", 0)
                    )
                except Exception:
                    datos["existe"] = 0

        datos["save"] = 1
    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


# FINALIZAR INGRESO DE GASTOS
def finalizar_ingreso_gastos_vaic(request):
    datos = {"save": 1, "existe": 0}
    try:
        userName = request.session.get("userName", "")

        # 1) Validación/consulta en universal
        conn_uni = connections["universal"]
        with conn_uni.cursor() as cursor:
            cursor.callproc("VAIC_FINALIZAR_INGRESO_GASTOS_GENERAL")
            rows = cursor.fetchall() or []
            if rows:
                first = rows[0]
                try:
                    datos["existe"] = (
                        first[0]
                        if isinstance(first, (list, tuple))
                        else first.get("existe", 0)
                    )
                except Exception:
                    datos["existe"] = 0

        # 2) Cierre en banco (ajusta el alias si tu conexión se llama distinto)
        #    Si no tienes definida esta conexión, cámbiala por la correcta.
        conn_bank = connections["bank"]
        with conn_bank.cursor() as cursor:
            cursor.callproc("VAIC_CERRAR_GASTOS_INGRESADOS")

        # 3) Log en universal
        with conn_uni.cursor() as cursor:
            cursor.callproc(
                "DAC_INSERT_LOG_EVENTO",
                [
                    "CERRAR",
                    f"{userName} HA CERRADO EL INGRESO DE GASTOS EN EL PERIODO ACTUAL",
                    userName,
                    "pago_acreedr_detalle",
                ],
            )

        datos["save"] = 1
    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


def insert_gasto_bancario_presupuesto(request):
    datos = {"save": 1}
    try:
        # --- Sesión y POST ---
        userName = request.session.get("userName", "")

        fkBancario = request.POST.get("fkBancario")
        FechaDocumento = request.POST.get("FechaDocumento")

        hidden_id_cuenta_contable = request.POST.get("hidden_id_cuenta_contable")
        hidden_numero_cuenta = request.POST.get("hidden_numero_cuenta")

        centro_asignar = request.POST.get("centro_asignar")
        centro_asignar_text = request.POST.get("centro_asignar_text")

        cuenta_gasto_asignar = request.POST.get("cuenta_gasto_asignar")
        cuenta_gasto_asignar_text = request.POST.get("cuenta_gasto_asignar_text")

        presupuesto_cuenta_disp = (
            request.POST.get("presupuesto_cuenta_disponible") or "0"
        ).replace(",", "")
        TotalGasto = (request.POST.get("TotalGasto") or "0").replace(",", "")
        valor_gasto = (request.POST.get("valor_gasto") or "0").replace(",", "")
        SaldoGasto = (request.POST.get("SaldoGasto") or "0").replace(",", "")

        encabezado_gasto = request.POST.get("encabezado_gasto") or ""
        detalle_gasto = request.POST.get("detalle_gasto") or ""
        concepto = (
            request.POST.get("concepto") or f"{encabezado_gasto} | {detalle_gasto}"
        )

        validacion = int(request.POST.get("validacion", 0))
        mes = request.POST.get("mes")
        anio = request.POST.get("anio")
        tipo_ingreso = request.POST.get("tipo_ingreso") or 0

        # --- 1) Insert en banco: VAIC_INSERT_GASTO_BANCARIO ---
        #   CALL VAIC_INSERT_GASTO_BANCARIO(centro_asignar, centro_asignar_text, mes, anio, fkBancario, userName, validacion, valor_gasto)
        conn_bank = connections["bank"]
        with conn_bank.cursor() as cursor:
            cursor.callproc(
                "VAIC_INSERT_GASTO_BANCARIO",
                [
                    centro_asignar,
                    centro_asignar_text,
                    mes,
                    anio,
                    fkBancario,
                    userName,
                    validacion,
                    valor_gasto,
                ],
            )
            # Si el driver/motor emite result sets “vacíos”, drenarlos si fuese necesario:
            # while cursor.nextset(): pass

        # --- 2) Registrar histórico en banco y obtener varID(s) ---
        #   CALL VAIC_REGISTRAR_PAGO_ACREEDORD_DETALLE_ASIGNADO_HISTORIAL(...)
        pk_rows = []
        with conn_bank.cursor() as cursor:
            cursor.callproc(
                "VAIC_REGISTRAR_PAGO_ACREEDORD_DETALLE_ASIGNADO_HISTORIAL",
                [
                    fkBancario,
                    centro_asignar,
                    centro_asignar_text,
                    hidden_numero_cuenta,
                    TotalGasto,
                    valor_gasto,
                    SaldoGasto,
                    userName,
                    mes,
                    anio,
                    concepto,
                    validacion,
                    cuenta_gasto_asignar_text,
                ],
            )
            pk_rows = cursor.fetchall() or []
            # while cursor.nextset(): pass

        # --- 3) Insert espejo en universal por cada varID retornado ---
        #   CALL VAIC_INSERT_GASTO_BANCARIO(fkBancario, hidden_id_cuenta_contable, hidden_numero_cuenta, concepto,
        #                                   centro_asignar, valor_gasto, mes, anio, userName, validacion,
        #                                   FechaDocumento, varID, tipo_ingreso)
        conn_uni = connections["universal"]
        if pk_rows:
            with conn_uni.cursor() as cursor:
                for row in pk_rows:
                    # Soporta tupla o dict; en Laravel accedías como $pk->varID
                    varID = None
                    try:
                        varID = row.get("varID") if hasattr(row, "get") else row[0]
                    except Exception:
                        varID = row[0]
                    cursor.callproc(
                        "VAIC_INSERT_GASTO_BANCARIO",
                        [
                            fkBancario,
                            hidden_id_cuenta_contable,
                            hidden_numero_cuenta,
                            concepto,
                            centro_asignar,
                            valor_gasto,
                            mes,
                            anio,
                            userName,
                            validacion,
                            FechaDocumento,
                            varID,
                            tipo_ingreso,
                        ],
                    )
                # while cursor.nextset(): pass

        datos["save"] = 1

    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


def fill_table_desglose_gastos(request):
    datos = {"success": False, "data": []}
    try:
        userName = request.session.get("userName", "")

        # Obtiene el parámetro que mandás en la URL
        acc_id = request.GET.get("acc_id")

        conn_bank = connections["bank"]
        with conn_bank.cursor() as cursor:
            cursor.callproc("VAIC_LIST_HISTORIAL_ACREEDORES", [acc_id])
            rows = cursor.fetchall() or []
            # Si necesitás drenar más result sets en MySQL:
            # while cursor.nextset(): pass

        datos["success"] = True
        datos["data"] = rows

    except Exception as e:
        datos["success"] = False
        datos["error"] = str(e)

    return JsonResponse(datos)


def retirar_gasto_vaic(request):
    datos = {"save": 1}
    try:
        pkHistorial = request.POST.get("pkHistorial")
        pkAcreedor = request.POST.get("pkAcreedor")
        id_gasto = request.POST.get("id_gasto")
        userName = request.session.get("userName", "")

        # 1) Anular en banco
        conn_bank = connections["bank"]
        with conn_bank.cursor() as cursor:
            cursor.callproc("VAIC_RETIRAR_GASTO", [pkAcreedor, pkHistorial, userName])
            # while cursor.nextset(): pass   # (habilita si usas MySQL y hay múltiples result sets)

        # 2) Anular en universal
        conn_uni = connections["universal"]
        with conn_uni.cursor() as cursor:
            cursor.callproc("VAIC_RETIRAR_GASTO_BANCARIO", [id_gasto, userName])
            # while cursor.nextset(): pass

        # 3) Log en universal
        mensaje = (
            f"{userName} HA ANULADO EL GASTO CON # DE ACREEDORES {pkAcreedor} "
            f"Y # DE MOVIMIENTO HISTORICO DE SALDO {pkHistorial}"
        )
        with conn_uni.cursor() as cursor:
            cursor.callproc(
                "DAC_INSERT_LOG_EVENTO", ["GASTOS", mensaje, userName, "vaic_gastos"]
            )
            # while cursor.nextset(): pass

        datos["save"] = 1

    except Exception as e:
        datos["save"] = 0
        datos["error"] = str(e)

    return JsonResponse(datos)


def dataBalancePresupuestoCentros(request):
    datos = {"success": False, "data": []}
    try:
        userName = request.session.get("userName", "")

        mes1 = request.GET.get("mes1")
        anio1 = request.GET.get("anio1")
        mes2 = request.GET.get("mes2")
        anio2 = request.GET.get("anio2")
        empresa = request.GET.get("empresa")

        accesoTotalVAIC = int(request.session.get("13050", 0))
        reporteSaldoVerTodasCuentas = int(request.session.get("13079", 0))
        adminIT = request.session.get("ctrlGestionAdminIT", 0)

        if adminIT == 1:
            varAcceso = "13050"
        elif accesoTotalVAIC == 1 or reporteSaldoVerTodasCuentas == 1:
            varAcceso = "13050"
        else:
            varAcceso = "0"

        udcConn = connections["universal"]
        with udcConn.cursor() as cursor:
            cursor.callproc(
                "VAIC_V_REPORTE_CENTROS_GASTOS",
                [mes1, anio1, mes2, anio2, empresa, varAcceso, userName],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataBalancePresupuestosCentrosVAIC(request):
    try:

        mes1 = request.GET.get("mes1")
        anio1 = request.GET.get("anio1")
        mes2 = request.GET.get("mes2")
        anio2 = request.GET.get("anio2")
        id_centro = request.GET.get("id_centro")

        conn = connections["universal"]
        with conn.cursor() as cursor:
            cursor.callproc(
                "VAIC_V_REPORTE_SALDOS_PRESUPUESTOS_X_CENTRO",
                [mes1, anio1, mes2, anio2, id_centro],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataBalancePresupuestosCuentasVAIC(request):
    try:

        mes1 = request.GET.get("mes1")
        anio1 = request.GET.get("anio1")
        mes2 = request.GET.get("mes2")
        anio2 = request.GET.get("anio2")
        empresa = request.GET.get("empresa")

        userName = request.session.get("userName", "")

        accesoTotalVAIC = int(request.session.get("13050", 0))
        adminIT = request.session.get("ctrlGestionAdminIT", 0)

        if adminIT == 1:
            varAcceso = "13050"
        elif accesoTotalVAIC == 1:
            varAcceso = "13050"
        else:
            varAcceso = "0"

        conn = connections["universal"]
        with conn.cursor() as cursor:
            cursor.callproc(
                "VAIC_V_REPORTE_CUENTAS_EMPRESA_GASTOS",
                [mes1, anio1, mes2, anio2, empresa, varAcceso, userName],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataCentrosCuentaPresupuestada(request):
    try:

        mes1 = request.GET.get("mes1")
        anio1 = request.GET.get("anio1")
        mes2 = request.GET.get("mes2")
        anio2 = request.GET.get("anio2")
        cuenta = request.GET.get("cuenta")

        userName = request.session.get("userName", "")

        conn = connections["universal"]
        with conn.cursor() as cursor:
            cursor.callproc(
                "VAIC_V_REPORTE_CENTROS_X_CUENTA_EMPRESA",
                [mes1, anio1, mes2, anio2, cuenta],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataComparativaAnualCentros(request):
    try:
        mes1 = request.GET.get("mes1")
        anio1 = request.GET.get("anio1")
        mes2 = request.GET.get("mes2")
        anio2 = request.GET.get("anio2")
        empresa = request.GET.get("empresa")

        userName = request.session.get("userName", "")

        accesoTotalVAIC = int(request.session.get("13050", 0))
        adminIT = request.session.get("ctrlGestionAdminIT", 0)

        if adminIT == 1:
            varAcceso = "13050"
        elif accesoTotalVAIC == 1:
            varAcceso = "13050"
        else:
            varAcceso = "0"

        conn = connections["universal"]
        with conn.cursor() as cursor:
            cursor.callproc(
                "VAIC_V_REPORTE_CENTROS_GASTOS_DINAMICO",
                [mes1, anio1, mes2, anio2, empresa, varAcceso, userName],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataComparativaAnualCuentasContables(request):
    try:
        anio = request.GET.get("anio")
        empresa = request.GET.get("empresa")
        tipo = request.GET.get("tipo")

        userName = request.session.get("userName", "")

        accesoTotalVAIC = int(request.session.get("13050", 0))
        adminIT = request.session.get("ctrlGestionAdminIT", 0)

        if adminIT == 1:
            varAcceso = "13050"
        elif accesoTotalVAIC == 1:
            varAcceso = "13050"
        else:
            varAcceso = "0"

        conn = connections["universal"]
        with conn.cursor() as cursor:
            cursor.callproc(
                "VAIC_LIST_PRESUPUESTO_ANUAL_X_EMPRESA",
                [anio, empresa, tipo, varAcceso, userName],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataReporteGastosPresupuestos(request):
    try:
        mes1 = request.GET.get("mes1")
        anio1 = request.GET.get("anio1")
        mes2 = request.GET.get("mes2")
        anio2 = request.GET.get("anio2")
        empresa = request.GET.get("empresa")

        userName = request.session.get("userName", "")

        accesoTotalVAIC = int(request.session.get("13050", 0))
        reporteSaldoVerTodasCuentas = int(request.session.get("13079", 0))
        adminIT = request.session.get("ctrlGestionAdminIT", 0)

        if adminIT == 1:
            varAcceso = "13050"
        elif accesoTotalVAIC == 1 or reporteSaldoVerTodasCuentas == 1:
            varAcceso = "13050"
        else:
            varAcceso = "0"

        conn = connections["universal"]
        with conn.cursor() as cursor:
            cursor.callproc(
                "VAIC_V_REPORTE_SALDOS_PRESUPUESTOS",
                [mes1, anio1, mes2, anio2, userName, varAcceso, empresa],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataReporteGastosIngresados(request):
    try:
        mes1 = request.GET.get("mes1")
        anio1 = request.GET.get("anio1")
        mes2 = request.GET.get("mes2")
        anio2 = request.GET.get("anio2")
        empresa = request.GET.get("empresa")

        userName = request.session.get("userName", "")

        accesoTotalVAIC = int(request.session.get("13050", 0))
        reporteSaldoVerTodasCuentas = int(request.session.get("13079", 0))
        adminIT = request.session.get("ctrlGestionAdminIT", 0)

        if adminIT == 1:
            varAcceso = "13050"
        elif accesoTotalVAIC == 1 or reporteSaldoVerTodasCuentas == 1:
            varAcceso = "13050"
        else:
            varAcceso = "0"

        conn = connections["universal"]
        with conn.cursor() as cursor:
            cursor.callproc(
                "VAIC_V_REPORTE_GASTOS_INGRESADOS",
                [mes1, anio1, mes2, anio2, userName, varAcceso, empresa],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataReporteIngresosPresupuestos(request):
    try:
        mes1 = request.GET.get("mes1")
        anio1 = request.GET.get("anio1")
        mes2 = request.GET.get("mes2")
        anio2 = request.GET.get("anio2")
        empresa = request.GET.get("empresa")

        userName = request.session.get("userName", "")

        accesoTotalVAIC = int(request.session.get("13050", 0))
        reporteSaldoVerTodasCuentas = int(request.session.get("13079", 0))
        adminIT = request.session.get("ctrlGestionAdminIT", 0)

        if adminIT == 1:
            varAcceso = "13050"
        elif accesoTotalVAIC == 1 or reporteSaldoVerTodasCuentas == 1:
            varAcceso = "13050"
        else:
            varAcceso = "0"

        conn = connections["universal"]
        with conn.cursor() as cursor:
            cursor.callproc(
                "VAIC_V_REPORTE_SALDOS_INGRESOS",
                [mes1, anio1, mes2, anio2, userName, varAcceso, empresa],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataReporteIngresosLogrados(request):
    try:
        mes1 = request.GET.get("mes1")
        anio1 = request.GET.get("anio1")
        mes2 = request.GET.get("mes2")
        anio2 = request.GET.get("anio2")
        empresa = request.GET.get("empresa")

        userName = request.session.get("userName", "")

        accesoTotalVAIC = int(request.session.get("13050", 0))
        reporteSaldoVerTodasCuentas = int(request.session.get("13079", 0))
        adminIT = request.session.get("ctrlGestionAdminIT", 0)

        if adminIT == 1:
            varAcceso = "13050"
        elif accesoTotalVAIC == 1 or reporteSaldoVerTodasCuentas == 1:
            varAcceso = "13050"
        else:
            varAcceso = "0"

        conn = connections["universal"]
        with conn.cursor() as cursor:
            cursor.callproc(
                "VAIC_V_REPORTE_INGRESOS_LOGRADO",
                [mes1, anio1, mes2, anio2, userName, varAcceso, empresa],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataReporteEVA(request):
    try:
        mes1 = request.GET.get("mes1")
        anio1 = request.GET.get("anio1")
        mes2 = request.GET.get("mes2")
        anio2 = request.GET.get("anio2")
        empresa = request.GET.get("empresa")

        userName = request.session.get("userName", "")

        accesoTotalVAIC = int(request.session.get("13050", 0))
        reporteSaldoVerTodasCuentas = int(request.session.get("13079", 0))
        adminIT = request.session.get("ctrlGestionAdminIT", 0)

        if adminIT == 1:
            varAcceso = "13050"
        elif accesoTotalVAIC == 1 or reporteSaldoVerTodasCuentas == 1:
            varAcceso = "13050"
        else:
            varAcceso = "0"

        conn = connections["universal"]
        with conn.cursor() as cursor:
            cursor.callproc(
                "VAIC_V_REPORTE_CENTROS_EVA",
                [mes1, anio1, mes2, anio2, userName, varAcceso, empresa],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataVendedoresCentro(request):
    try:
        centro_id = request.GET.get("centro")
        mes1 = request.GET.get("mes1")
        anio1 = request.GET.get("anio1")
        mes2 = request.GET.get("mes2")
        anio2 = request.GET.get("anio2")

        userName = request.session.get("userName", "")

        accesoTotalVAIC = int(request.session.get("13050", 0))
        reporteSaldoVerTodasCuentas = int(request.session.get("13079", 0))
        adminIT = request.session.get("ctrlGestionAdminIT", 0)

        if adminIT == 1:
            varAcceso = "13050"
        elif accesoTotalVAIC == 1 or reporteSaldoVerTodasCuentas == 1:
            varAcceso = "13050"
        else:
            varAcceso = "0"

        conn = connections["universal"]
        with conn.cursor() as cursor:
            cursor.callproc(
                "VAIC_LIST_DESGLOSE_VENDEDORES_X_CENTRO",
                [centro_id, mes1, anio1, mes2, anio2],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def dataGastosPresupuesto(request):
    try:
        cuenta = request.GET.get("cuenta")
        centro_id = request.GET.get("centro")
        mes1 = request.GET.get("mes1")
        anio1 = request.GET.get("anio1")
        mes2 = request.GET.get("mes2")
        anio2 = request.GET.get("anio2")

        userName = request.session.get("userName", "")

        accesoTotalVAIC = int(request.session.get("13050", 0))
        reporteSaldoVerTodasCuentas = int(request.session.get("13079", 0))
        adminIT = request.session.get("ctrlGestionAdminIT", 0)

        if adminIT == 1:
            varAcceso = "13050"
        elif accesoTotalVAIC == 1 or reporteSaldoVerTodasCuentas == 1:
            varAcceso = "13050"
        else:
            varAcceso = "0"

        conn = connections["universal"]
        with conn.cursor() as cursor:
            cursor.callproc(
                "VAIC_LIST_DETAILS_GASTOS_PRESUPUESTOS",
                [cuenta, centro_id, mes1, anio1, mes2, anio2],
            )
            column_names = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()

            data = []
            for row in raw_rows:
                row_dict = {}
                for col, val in zip(column_names, row):
                    # Convertir campos tipo BIT (bytes) a int (0 o 1)
                    if isinstance(val, bytes):
                        row_dict[str(col)] = int.from_bytes(val, byteorder="little")
                    else:
                        row_dict[str(col)] = val
                data.append(row_dict)

        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)})


def list_all_cuentas_contables(request):
    varTipo = request.GET.get("varTipo", "")
    varCentro = request.GET.get("varCentro", 0)
    varMes = request.GET.get("varMes", 0)
    varAnio = request.GET.get("varAnio", 0)

    try:
        with connections["universal"].cursor() as cursor:
            cursor.callproc("CONTA_GET_CUENTAS_X_CENTRO", [varCentro])
            result = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        # Formatear resultados como una lista de diccionarios
        data = [dict(zip(columns, row)) for row in result]

        return JsonResponse({"success": True, "data": data})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
