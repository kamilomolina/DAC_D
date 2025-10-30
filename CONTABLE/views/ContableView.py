from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connections
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime, timedelta
import requests
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
from datetime import date, datetime
from django.http import JsonResponse, Http404
from django.urls import reverse
import csv
import tempfile
import pyodbc
import pymssql
from django.db import transaction


def obtener_empresas():
    empresas_list = []
    try:
        with connections['global_nube'].cursor() as cursor:
            cursor.execute("CALL TH_GET_EMPRESAS()")
            empresas = cursor.fetchall()
            empresas_list = [{'id': empresa[1], 'nombre': empresa[0]} for empresa in empresas]

    except Exception as e:
        empresas_list = ""
    return empresas_list

def get_accesos_contabilidad(request):
    user_id = request.session.get('user_id', '')
    request.session['contabilidadAdminIT'] = 0

    appConn = connections['global_nube']
    with appConn.cursor() as cursor:
        cursor.callproc('WEB_GET_ADMIN_IT', [user_id, 12])
        adminITQuery = cursor.fetchall()

        # Procesar los menús y establecer valores en la sesión
        if adminITQuery:
            request.session['contabilidadAdminIT'] = 1

        appConn.close()

    appConn = connections['global_nube']
    with appConn.cursor() as cursor:
        cursor.callproc('WEB_GET_MENUS_GRUPO_USUARIO', [user_id, 12])
        menuQuery = cursor.fetchall()

        # Procesar los menús y establecer valores en la sesión
        if menuQuery:
            for menu in menuQuery:
                posicion_menu = menu[2]
                permiso_menu = menu[6]

                if posicion_menu == '10000' and permiso_menu == 1:
                    request.session['tabContabilidad_CNT'] = 1
                elif posicion_menu == '10000' and permiso_menu == 0:
                    request.session['tabContabilidad_CNT'] = 0

                if posicion_menu == '10100' and permiso_menu == 1:
                    request.session['grupoLibros_CNT'] = 1
                elif posicion_menu == '10100' and permiso_menu == 0:
                    request.session['grupoLibros_CNT'] = 0

                if posicion_menu == '10101' and permiso_menu == 1:
                    request.session['nuevaPartidaManual_CNT'] = 1
                elif posicion_menu == '10101' and permiso_menu == 0:
                    request.session['nuevaPartidaManual_CNT'] = 0

                if posicion_menu == '10102' and permiso_menu == 1:
                    request.session['cargarDatosExcel_CNT'] = 1
                elif posicion_menu == '10102' and permiso_menu == 0:
                    request.session['cargarDatosExcel_CNT'] = 0

                if posicion_menu == '10103' and permiso_menu == 1:
                    request.session['libroDiario_CNT'] = 1
                elif posicion_menu == '10103' and permiso_menu == 0:
                    request.session['libroDiario_CNT'] = 0

                if posicion_menu == '10104' and permiso_menu == 1:
                    request.session['libroMayor_CNT'] = 1
                elif posicion_menu == '10104' and permiso_menu == 0:
                    request.session['libroMayor_CNT'] = 0

                if posicion_menu == '10105' and permiso_menu == 1:
                    request.session['libroMayor_Codigo_CNT'] = 1
                elif posicion_menu == '10105' and permiso_menu == 0:
                    request.session['libroMayor_Codigo_CNT'] = 0

                if posicion_menu == '10200' and permiso_menu == 1:
                    request.session['grupoCierreContables_CNT'] = 1
                elif posicion_menu == '10200' and permiso_menu == 0:
                    request.session['grupoCierreContables_CNT'] = 0

                if posicion_menu == '10201' and permiso_menu == 1:
                    request.session['cierreMes_CNT'] = 1
                elif posicion_menu == '10201' and permiso_menu == 0:
                    request.session['cierreMes_CNT'] = 0

                if posicion_menu == '10202' and permiso_menu == 1:
                    request.session['entregarMes_CNT'] = 1
                elif posicion_menu == '10202' and permiso_menu == 0:
                    request.session['entregarMes_CNT'] = 0

                if posicion_menu == '10203' and permiso_menu == 1:
                    request.session['actualizarDatosMesesCerrados_CNT'] = 1
                elif posicion_menu == '10203' and permiso_menu == 0:
                    request.session['actualizarDatosMesesCerrados_CNT'] = 0

                if posicion_menu == '10204' and permiso_menu == 1:
                    request.session['entregarPeriodo_CNT'] = 1
                elif posicion_menu == '10204' and permiso_menu == 0:
                    request.session['entregarPeriodo_CNT'] = 0

                if posicion_menu == '10205' and permiso_menu == 1:
                    request.session['verMesesCerradosEntregados_CNT'] = 1
                elif posicion_menu == '10205' and permiso_menu == 0:
                    request.session['verMesesCerradosEntregados_CNT'] = 0

                if posicion_menu == '20101' and permiso_menu == 1:
                    request.session['estadoResultadosAnuales_CNT'] = 1
                elif posicion_menu == '20101' and permiso_menu == 0:
                    request.session['estadoResultadosAnuales_CNT'] = 0

                if posicion_menu == '20102' and permiso_menu == 1:
                    request.session['estadoSituacionFinanciera_CNT'] = 1
                elif posicion_menu == '20102' and permiso_menu == 0:
                    request.session['estadoSituacionFinanciera_CNT'] = 0

                if posicion_menu == '20103' and permiso_menu == 1:
                    request.session['gastosPorMes_CNT'] = 1
                elif posicion_menu == '20103' and permiso_menu == 0:
                    request.session['gastosPorMes_CNT'] = 0

                if posicion_menu == '20104' and permiso_menu == 1:
                    request.session['estadoResultadoIntegral_CNT'] = 1
                elif posicion_menu == '20104' and permiso_menu == 0:
                    request.session['estadoResultadoIntegral_CNT'] = 0

                if posicion_menu == '20105' and permiso_menu == 1:
                    request.session['balanzaComprobacion_CNT'] = 1
                elif posicion_menu == '20105' and permiso_menu == 0:
                    request.session['balanzaComprobacion_CNT'] = 0

                if posicion_menu == '20106' and permiso_menu == 1:
                    request.session['estadoFlujoEfectivo_CNT'] = 1
                elif posicion_menu == '20106' and permiso_menu == 0:
                    request.session['estadoFlujoEfectivo_CNT'] = 0

                if posicion_menu == '20107' and permiso_menu == 1:
                    request.session['razonesFinancieras_CNT'] = 1
                elif posicion_menu == '20107' and permiso_menu == 0:
                    request.session['razonesFinancieras_CNT'] = 0

                if posicion_menu == '20108' and permiso_menu == 1:
                    request.session['effYdr_CNT'] = 1
                elif posicion_menu == '20108' and permiso_menu == 0:
                    request.session['effYdr_CNT'] = 0

                if posicion_menu == '20109' and permiso_menu == 1:
                    request.session['nofYcc_CNT'] = 1
                elif posicion_menu == '20109' and permiso_menu == 0:
                    request.session['nofYcc_CNT'] = 0

                if posicion_menu == '20110' and permiso_menu == 1:
                    request.session['nof_CNT'] = 1
                elif posicion_menu == '20110' and permiso_menu == 0:
                    request.session['nof_CNT'] = 0

                if posicion_menu == '20111' and permiso_menu == 1:
                    request.session['roeDupont_CNT'] = 1
                elif posicion_menu == '20111' and permiso_menu == 0:
                    request.session['roeDupont_CNT'] = 0

                if posicion_menu == '20112' and permiso_menu == 1:
                    request.session['freeCashFlow_CNT'] = 1
                elif posicion_menu == '20112' and permiso_menu == 0:
                    request.session['freeCashFlow_CNT'] = 0

                if posicion_menu == '30101' and permiso_menu == 1:
                    request.session['empresas_CNT'] = 1
                elif posicion_menu == '30101' and permiso_menu == 0:
                    request.session['empresas_CNT'] = 0

                if posicion_menu == '30102' and permiso_menu == 1:
                    request.session['cuentasContables_CNT'] = 1
                elif posicion_menu == '30102' and permiso_menu == 0:
                    request.session['cuentasContables_CNT'] = 0

                if posicion_menu == '30103' and permiso_menu == 1:
                    request.session['cuentasBalance_CNT'] = 1
                elif posicion_menu == '30103' and permiso_menu == 0:
                    request.session['cuentasBalance_CNT'] = 0

                if posicion_menu == '30104' and permiso_menu == 1:
                    request.session['sucursales_CNT'] = 1
                elif posicion_menu == '30104' and permiso_menu == 0:
                    request.session['sucursales_CNT'] = 0

                if posicion_menu == '30105' and permiso_menu == 1:
                    request.session['departamentos_CNT'] = 1
                elif posicion_menu == '30105' and permiso_menu == 0:
                    request.session['departamentos_CNT'] = 0

                if posicion_menu == '30106' and permiso_menu == 1:
                    request.session['cuentasGastos_CNT'] = 1
                elif posicion_menu == '30106' and permiso_menu == 0:
                    request.session['cuentasGastos_CNT'] = 0

                if posicion_menu == '30107' and permiso_menu == 1:
                    request.session['encargadosDepartamentos_CNT'] = 1
                elif posicion_menu == '30107' and permiso_menu == 0:
                    request.session['encargadosDepartamentos_CNT'] = 0

                if posicion_menu == '30108' and permiso_menu == 1:
                    request.session['reglasUsoCuentas_CNT'] = 1
                elif posicion_menu == '30108' and permiso_menu == 0:
                    request.session['reglasUsoCuentas_CNT'] = 0

                if posicion_menu == '20000' and permiso_menu == 1:
                    request.session['pestañaEstadosFinancieros_CNT'] = 1
                elif posicion_menu == '20000' and permiso_menu == 0:
                    request.session['pestañaEstadosFinancieros_CNT'] = 0

                if posicion_menu == '20100' and permiso_menu == 1:
                    request.session['grupoEstadosFinancieros_CNT'] = 1
                elif posicion_menu == '20100' and permiso_menu == 0:
                    request.session['grupoEstadosFinancieros_CNT'] = 0

                if posicion_menu == '30000' and permiso_menu == 1:
                    request.session['pestañaCatalogos_CNT'] = 1
                elif posicion_menu == '30000' and permiso_menu == 0:
                    request.session['pestañaCatalogos_CNT'] = 0

                if posicion_menu == '30100' and permiso_menu == 1:
                    request.session['grupoCatalogo_CNT'] = 1
                elif posicion_menu == '30100' and permiso_menu == 0:
                    request.session['grupoCatalogo_CNT'] = 0

                if posicion_menu == '30200' and permiso_menu == 1:
                    request.session['grupoNIC_CNT'] = 1
                elif posicion_menu == '30200' and permiso_menu == 0:
                    request.session['grupoNIC_CNT'] = 0

                if posicion_menu == '30201' and permiso_menu == 1:
                    request.session['perfilesNIC_CNT'] = 1
                elif posicion_menu == '30201' and permiso_menu == 0:
                    request.session['perfilesNIC_CNT'] = 0

                if posicion_menu == '30202' and permiso_menu == 1:
                    request.session['detallesNIC_CNT'] = 1
                elif posicion_menu == '30202' and permiso_menu == 0:
                    request.session['detallesNIC_CNT'] = 0

                if posicion_menu == '30300' and permiso_menu == 1:
                    request.session['grupoConfiguraciones_CNT'] = 1
                elif posicion_menu == '30300' and permiso_menu == 0:
                    request.session['grupoConfiguraciones_CNT'] = 0

                if posicion_menu == '30301' and permiso_menu == 1:
                    request.session['firmasEstadosFinancieros_CNT'] = 1
                elif posicion_menu == '30301' and permiso_menu == 0:
                    request.session['firmasEstadosFinancieros_CNT'] = 0

                if posicion_menu == '30302' and permiso_menu == 1:
                    request.session['definirDecimales_CNT'] = 1
                elif posicion_menu == '30302' and permiso_menu == 0:
                    request.session['definirDecimales_CNT'] = 0

                if posicion_menu == '30109' and permiso_menu == 1:
                    request.session['cuentasContablesPorSD_CNT'] = 1
                elif posicion_menu == '30109' and permiso_menu == 0:
                    request.session['cuentasContablesPorSD_CNT'] = 0

                if posicion_menu == '30500' and permiso_menu == 1:
                    request.session['clasificacionCuentas_CNT'] = 1
                elif posicion_menu == '30500' and permiso_menu == 0:
                    request.session['clasificacionCuentas_CNT'] = 0

                if posicion_menu == '30520' and permiso_menu == 1:
                    request.session['tasaCambio_CNT'] = 1
                elif posicion_menu == '30520' and permiso_menu == 0:
                    request.session['tasaCambio_CNT'] = 0

        appConn.close()

def panel_contabilidad(request):
    user_id = request.session.get('user_id', '')

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        get_accesos_contabilidad(request)
        
        return render(request, 'panel_contable.html')

def conta_clasificacion_cuentas(request):
    user_id = request.session.get('user_id', '')
    clasificacionCuentas_CNT = request.session.get('clasificacionCuentas_CNT', 0)
    adminIT = request.session.get('contabilidadAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if clasificacionCuentas_CNT == 1 or adminIT == 1:
            return render(request, 'catalogos/clasificacionCuentas.html')
        else:
            return HttpResponseRedirect(reverse('panel_contabilidad'))

def conta_clasificacion_cuentas_nic(request):
    user_id = request.session.get('user_id', '')
    clasificacionCuentas_NIC_CNT = request.session.get('detallesNIC_CNT', 0)
    adminIT = request.session.get('contabilidadAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if clasificacionCuentas_NIC_CNT == 1 or adminIT == 1:
            
            tiposNICData = ""
            try:
                udcConn = connections['universal']
                with udcConn.cursor() as cursor:
                    cursor.callproc("CONTA_GET_TIPOS_NIC", [1])
                    column_names = [desc[0] for desc in cursor.description]
                    tiposNICData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                # Cierra la conexión
                udcConn.close()
            except Exception as e:
                # Manejo de excepciones, puedes personalizar esto según tus necesidades
                return JsonResponse({'error': str(e)})

            cuentasBaseData = ""
            try:
                udcConn = connections['universal']
                with udcConn.cursor() as cursor:
                    cursor.callproc("CONTA_GET_CUENTAS_BASES", [1])
                    column_names = [desc[0] for desc in cursor.description]
                    cuentasBaseData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                # Cierra la conexión
                udcConn.close()
            except Exception as e:
                # Manejo de excepciones, puedes personalizar esto según tus necesidades
                return JsonResponse({'error': str(e)})

            empresasData = obtener_empresas()

            context = {
                "tiposNICData": tiposNICData,
                "cuentasBaseData": cuentasBaseData,
                "empresasData": empresasData,
            }

            return render(request, 'catalogos/clasificacionNIC.html', context)
        else:
            return HttpResponseRedirect(reverse('panel_contabilidad'))

def cuentas_nic(request):
    user_id = request.session.get('user_id', '')

    cuentas_NIC_CNT = request.session.get('perfilesNIC_CNT', 0)
    adminIT = request.session.get('contabilidadAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if cuentas_NIC_CNT == 1 or adminIT == 1:

            tiposNICData = ""
            try:
                udcConn = connections['universal']
                with udcConn.cursor() as cursor:
                    cursor.callproc("CONTA_GET_TIPOS_NIC", [1])
                    column_names = [desc[0] for desc in cursor.description]
                    tiposNICData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})
            
            cuentasBaseData = ""
            try:
                udcConn = connections['universal']
                with udcConn.cursor() as cursor:
                    cursor.callproc("CONTA_GET_CUENTAS_BASES", [1])
                    column_names = [desc[0] for desc in cursor.description]
                    cuentasBaseData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "tiposNICData": tiposNICData,
                "cuentasBaseData": cuentasBaseData,
            }

            return render(request, 'catalogos/cuentasNIC.html', context)
        else:
            return HttpResponseRedirect(reverse('panel_contabilidad'))




def dataCuentasDisponiblesNIC(request):
    empresa = request.POST.get('empresa')
    tipoNIC = request.POST.get('tipoNIC')
    padre = request.POST.get('padre')

    try:
        udcConn = connections['universal']
        with udcConn.cursor() as cursor:
            cursor.callproc("CONTA_CUENTAS_X_CLASIFICAR_NIC", [empresa, tipoNIC, padre])
            column_names = [desc[0] for desc in cursor.description]
            cuentasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': cuentasData})
    except Exception as e:
        return JsonResponse({'error': str(e)})



def dataCuentasAsociadasNIC(request):
    empresa = request.POST.get('empresa')
    tipoNIC = request.POST.get('tipoNIC')
    padre = request.POST.get('padre')

    try:
        udcConn = connections['universal']
        with udcConn.cursor() as cursor:
            cursor.callproc("CONTA_CUENTAS_X_NIC", [empresa, tipoNIC, padre])
            column_names = [desc[0] for desc in cursor.description]
            cuentasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': cuentasData})
    except Exception as e:
        return JsonResponse({'error': str(e)})




def insert_remove_cuenta_x_nic(request):
    try:
        empresa = request.POST.get('empresa')
        cuenta_nic = request.POST.get('cuenta_nic')
        id_cuenta = request.POST.get('id_cuenta')
        codigo = request.POST.get('codigo')
        opcion = request.POST.get('opcion')

        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('CONTA_ADD_REMOVE_CUENTA_X_NIC', [
                cuenta_nic,
                id_cuenta,
                codigo,
                empresa,
                opcion,
                userName
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)




def dataClasificacionCuentas(request):
    opcion = request.POST.get('opcion')

    try:
        udcConn = connections['universal']
        with udcConn.cursor() as cursor:
            cursor.callproc("CONTA_CUENTAS_BASES", [opcion])
            column_names = [desc[0] for desc in cursor.description]
            cuentasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': cuentasData})
    except Exception as e:
        return JsonResponse({'error': str(e)})



def dataCuentasNIC(request):
    tipoNIC = request.POST.get('tipoNIC')
    opcion = request.POST.get('opcion')

    try:
        udcConn = connections['universal']
        with udcConn.cursor() as cursor:
            cursor.callproc("CONTA_GET_CUENTAS_NIC_X_TIPO", [tipoNIC, opcion])
            column_names = [desc[0] for desc in cursor.description]
            cuentasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': cuentasData})
    except Exception as e:
        return JsonResponse({'error': str(e)})




def cuentas_contables(request):
    user_id = request.session.get('user_id', '')

    if user_id == '':  
        return HttpResponseRedirect(reverse('login'))
    else:
        context = {
            'cuentas_bases': obtener_cuentas_base(),
            'tipo_saldo': obtener_tipo_saldo(),
            'empresasData': obtener_empresas(),
        }

        return render(request, 'catalogos/cuentas_contables.html', context) 



def cuentas_gastos(request):
    user_id = request.session.get('user_id', '')

    cuentasGastos_CNT = request.session.get('cuentasGastos_CNT', 0)

    if user_id == '': 
        return HttpResponseRedirect(reverse('login'))
    else:
        if cuentasGastos_CNT == 1 or adminIT == 1:

            context = {
                "empresasData": obtener_empresas(),
            }

            return render(request, 'catalogos/cuentas_gastos.html', context) 
        else:
            return HttpResponseRedirect(reverse('panel_contabilidad'))



def dataCuentasGastos(request):
    empresa = request.POST.get('empresa')
    opcion = request.POST.get('opcion')

    try:
        udcConn = connections['universal']
        with udcConn.cursor() as cursor:
            cursor.callproc("CONTA_GET_CUENTAS_GASTOS", [empresa, opcion])
            column_names = [desc[0] for desc in cursor.description]
            cuentasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': cuentasData})
    except Exception as e:
        return JsonResponse({'error': str(e)})




def dataCuentasContables(request):
    empresa = request.POST.get('empresa')
    opcion = request.POST.get('opcion')

    try:
        udcConn = connections['universal']
        with udcConn.cursor() as cursor:
            cursor.callproc("CONTA_MOSTRAR_CUENTAS_CONTABLES", [opcion, empresa])
            column_names = [desc[0] for desc in cursor.description]
            cuentasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': cuentasData})
    except Exception as e:
        return JsonResponse({'error': str(e)})




def update_status_cuentas_contables(request):
    try:
        cuenta_id = request.POST.get('cuenta_id')
        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('CONTA_STATUS_UPDATE_CUENTAS_CONTABLES', [
                cuenta_id,
                userName
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def update_status_cuentas_gastos(request):
    try:
        cuenta_id = request.POST.get('cuenta_id')
        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('CONTA_STATUS_UPDATE_CUENTA_GASTO', [
                cuenta_id,
                userName
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)




def obtener_cuentas_base():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('CONTA_CUENTAS_BASES', [1])  
        results = cursor.fetchall()

    return results



def obtener_tipo_saldo():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('CONTA_TIPO_SALDO')  
        results = cursor.fetchall()

    return results



def obtener_subcuentas(request):
    cuenta_padre = request.GET.get('cuenta_padre')  
    if cuenta_padre:
        with connections['universal'].cursor() as cursor:
            cursor.callproc('CONTA_OBTENER_SUBCUENTAS', [cuenta_padre])
            subcuentas = cursor.fetchall()  
        
        data = [{'id': sub[0], 'nombre': sub[2]} for sub in subcuentas]
        return JsonResponse({'subcuentas': data}, safe=False)
    return JsonResponse({'error': 'No se proporcionó cuenta_padre'}, status=400)




def generar_codigo(request):
    cuenta_padre = request.GET.get('cuenta_padre', None)
    nuevo_codigo = None  

    try:
        with connections['universal'].cursor() as cursor:
            cursor.callproc('CONTA_GENERAR_CODIGO', [cuenta_padre, '@nuevo_codigo'])

            cursor.execute("SELECT @nuevo_codigo")
            resultado = cursor.fetchone()

            if resultado:
                nuevo_codigo = resultado[0]
            else:
                nuevo_codigo = None

    except Exception as e:
        nuevo_codigo = None

    return JsonResponse({'nuevo_codigo': nuevo_codigo})



def conta_update_es_cuenta_padre(request):
    try:
        cuenta_id = request.POST.get('cuenta_id', 0)
        es_padre = request.POST.get('es_padre', 0)
        userName = request.session.get('userName', '') 

        with connections['universal'].cursor() as cursor:
            cursor.callproc('CONTA_UPDATE_ES_CUENTA_PADRE', [cuenta_id, es_padre, userName])

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)




def conta_update_es_padre_cuentas_gastos(request):
    try:
        cuenta_id = request.POST.get('cuenta_id', 0)
        es_padre = request.POST.get('es_padre', 0)

        userName = request.session.get('userName', '') 

        with connections['universal'].cursor() as cursor:
            cursor.callproc('CONTA_UPDATE_ES_PADRE_CUENTA_GASTOS', [cuenta_id, es_padre, userName])

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)



def insertar_actualizar_cuenta(request):
    if request.method == 'POST':
      
        id_cuenta = request.POST.get('id_cuenta')  
        codigo = request.POST.get('codigo')       
        nombre = request.POST.get('nombre')      
        tipo_cuenta = request.POST.get('tipo_cuenta')  
        cuenta_padre = request.POST.get('cuenta_padre')  
        descripcion = request.POST.get('descripcion') 
        tipo_saldo = request.POST.get('tipo_saldo')  
        se_acredita_cuando = request.POST.get('se_acredita_cuando')  
        tratamiento_cuenta = request.POST.get('tratamiento_cuenta')  
        FkCuentaBase = request.POST.get('FkCuentaBase')  
        opcion = int(request.POST.get('opcion', 1))   
        creado_por = request.session.get('userName', '') 
        es_cuenta_padre = int(request.POST.get('es_cuenta_padre', 0))
        empresa = int(request.POST.get('empresa', 0))

        # Manejo de valores nulos
        cuenta_padre = None if not cuenta_padre else cuenta_padre
        tipo_saldo = None if not tipo_saldo else tipo_saldo
        se_acredita_cuando = '-'

        try:
            with connections['universal'].cursor() as cursor:
                # Llamada al procedimiento almacenado
                cursor.callproc('CONTA_INSERT_UPDATE_CUENTA_CONTABLE', [
                    id_cuenta,          # ID de la cuenta
                    codigo,             # Código de la cuenta
                    nombre,             # Nombre de la cuenta
                    tipo_cuenta,        # Tipo de cuenta
                    cuenta_padre,       # ID de la cuenta padre
                    creado_por,         # Usuario que realiza la acción
                    descripcion,        # Descripción
                    tipo_saldo,         # Tipo de saldo
                    se_acredita_cuando, # Se acredita cuando
                    tratamiento_cuenta,
                    FkCuentaBase,
                    es_cuenta_padre,
                    empresa,
                    opcion              # Opción: Insertar o Actualizar
                ])

                # Obtener el resultado del procedimiento almacenado
                result = cursor.fetchone()
                existe = result[0] if result else 0 

            # Respuesta según el resultado
            if existe == 0:
                return JsonResponse({'status': 'success', 'message': 'Operación realizada exitosamente.'})
            else:
                return JsonResponse({'status': 'fail', 'message': 'Registro duplicado. Verifique el código o el nombre.'})

        except Exception as e:
            # Manejo de errores
            return JsonResponse({'status': 'fail', 'error': str(e)})

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def insert_update_clasificacion_cuentas(request):
    try:
        existe = 0

        clasificacion_id = request.POST.get('clasificacion_id')  
        clasificacion = request.POST.get('clasificacion')
        descripcion = request.POST.get('descripcion')
        opcion = request.POST.get('opcion')

        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('CONTA_INSERT_UPDATE_CLASIFICACION_CUENTA', [
                clasificacion_id,
                clasificacion,
                descripcion,
                opcion,
                userName
            ]) 
            results = cursor.fetchall()

            if results:
                for result in results:
                    existe = result[0]
            else:
                existe = 0
        
        appConn.close()

        datos = {'save': 1, 'existe': existe}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def insert_update_cuenta_nic(request):
    try:
        existe = 0

        nic_id = request.POST.get('nic_id')  
        concepto = request.POST.get('concepto')
        cuenta_base = request.POST.get('cuenta_base')
        tipo_nic = request.POST.get('tipo_nic')
        opcion = request.POST.get('opcion')

        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('CONTA_INSERT_UPDATE_CUENTA_NIC', [
                nic_id,
                concepto,
                cuenta_base,
                tipo_nic,
                opcion,
                userName
            ]) 
            results = cursor.fetchall()

            if results:
                for result in results:
                    existe = result[0]
            else:
                existe = 0
        
        appConn.close()

        datos = {'save': 1, 'existe': existe}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def insert_update_cuentas_gastos(request):
    try:
        existe = 0

        cuenta_id = request.POST.get('cuenta_id')  
        nombre = request.POST.get('nombre')
        codigo = request.POST.get('codigo')
        padre = request.POST.get('padre')
        empresa = request.POST.get('empresa')
        opcion = request.POST.get('opcion')

        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('CONTA_INSERT_UPDATE_CUENTA_GASTO', [
                cuenta_id,
                nombre,
                codigo,
                padre,
                empresa,
                opcion,
                userName
            ]) 
            results = cursor.fetchall()

            if results:
                for result in results:
                    existe = result[0]
            else:
                existe = 0
        
        appConn.close()

        datos = {'save': 1, 'existe': existe}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)




def update_status_clasificacion_cuentas(request):
    try:
        clasificacion_id = request.POST.get('clasificacion_id')
        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('CONTA_UPDATE_STATUS_CLASIFICACION_CUENTA', [
                clasificacion_id,
                userName
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)



def update_status_cuentas_nic(request):
    try:
        nic_id = request.POST.get('nic_id')
        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('CONTA_UPDATE_STATUS_CUENTAS_NIC', [
                nic_id,
                userName
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)






def firmas_view(request):
    user_id = request.session.get('user_id', '')
    firmas_CNT = request.session.get('firmasEstadosFinancieros_CNT', 0)
    adminIT = request.session.get('contabilidadAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if firmas_CNT == 1 or adminIT == 1:
            empresasData = obtener_empresas()

            empleadosData = ""
            try:
                udcConn = connections['universal']
                with udcConn.cursor() as cursor:
                    cursor.callproc("CONTA_GET_EMPLEADOS_CARGOS", [0])
                    column_names = [desc[0] for desc in cursor.description]
                    empleadosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                # Cierra la conexión
                udcConn.close()
            except Exception as e:
                # Manejo de excepciones, puedes personalizar esto según tus necesidades
                return JsonResponse({'error': str(e)})


            secuenciasFirmasData = ""
            try:
                udcConn = connections['universal']
                with udcConn.cursor() as cursor:
                    cursor.callproc("CONTA_GET_TIPOS_FIRMAS_NUMERACION", [1])
                    column_names = [desc[0] for desc in cursor.description]
                    secuenciasFirmasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                # Cierra la conexión
                udcConn.close()
            except Exception as e:
                # Manejo de excepciones, puedes personalizar esto según tus necesidades
                return JsonResponse({'error': str(e)})

            context = {
                "empresasData": empresasData,
                "empleadosData": empleadosData,
                "secuenciasFirmasData": secuenciasFirmasData,
            }
            
            return render(request, 'catalogos/firmas_financieras.html', context)


def dataFirmasFinancieras(request):
    empresa = request.POST.get('empresa')
    opcion = request.POST.get('opcion')

    try:
        udcConn = connections['universal']
        with udcConn.cursor() as cursor:
            cursor.callproc("CONTA_GET_FIRMAS", [empresa, opcion])
            column_names = [desc[0] for desc in cursor.description]
            firmasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': firmasData})
    except Exception as e:
        return JsonResponse({'error': str(e)})






def conta_new_edit_partida(request, partida, empresa):
    user_id = request.session.get('user_id', '')
    libroDiario_CNT = request.session.get('libroDiario_CNT', 0)
    nuevaPartidaManual_CNT = request.session.get('nuevaPartidaManual_CNT', 0)
    adminIT = request.session.get('contabilidadAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if nuevaPartidaManual_CNT == 1 or libroDiario_CNT == 1 or adminIT == 1:
            empresasData = obtener_empresas()

            fecha_hora_actual = datetime.now().strftime('%Y-%m-%dT%H:%M')

            secuenciasFirmasData = ""
            try:
                udcConn = connections['universal']
                with udcConn.cursor() as cursor:
                    cursor.callproc("CONTA_GET_TIPOS_FIRMAS_NUMERACION", [1])
                    column_names = [desc[0] for desc in cursor.description]
                    secuenciasFirmasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                # Cierra la conexión
                udcConn.close()
            except Exception as e:
                # Manejo de excepciones, puedes personalizar esto según tus necesidades
                return JsonResponse({'error': str(e)})

            cuentasData = ""
            try:
                udcConn = connections['universal']
                with udcConn.cursor() as cursor:
                    cursor.callproc("CONTA_GET_CAT_CUENTAS", [empresa])
                    column_names = [desc[0] for desc in cursor.description]
                    cuentasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                # Cierra la conexión
                udcConn.close()
            except Exception as e:
                # Manejo de excepciones, puedes personalizar esto según tus necesidades
                return JsonResponse({'error': str(e)})


            num_partida = ''
            sinopsis = ''
            tasaCambio = 0.00
            balance = 0.00

            try:
                udcConn = connections['universal']
                with udcConn.cursor() as cursor:
                    cursor.callproc('CONTA_GET_DATA_X_PARTIDA', [
                        partida
                    ])
                    result = [col[0] for col in cursor.description]
                    partidaQuery = [dict(zip(result, row)) for row in cursor.fetchall()]
                    cursor.nextset()

                    if partidaQuery:
                        for p in partidaQuery:
                            partida_id = p["PkEncPartida"]
                            num_partida = p["Npartida"]
                            sinopsis = p["Sinopsis"]
                            fecha_hora_actual = p["FechaPartida"].strftime('%Y-%m-%dT%H:%M')
                            tasaCambio = p["TasaCambio"]
                            balance = p["Balance"]
                            empresa = p["FkEmpresa"]
            except Exception as e:
                return JsonResponse({'error': str(e)})


            detallesPartidaData = ""
            try:
                udcConn = connections['universal']
                with udcConn.cursor() as cursor:
                    cursor.callproc("CONTA_GET_PARTIDA_DETALLE_X_FECHA_NPARTIDA", [partida])
                    column_names = [desc[0] for desc in cursor.description]
                    detallesPartidaData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                # Cierra la conexión
                udcConn.close()
            except Exception as e:
                # Manejo de excepciones, puedes personalizar esto según tus necesidades
                return JsonResponse({'error': str(e)})

            context = {
                "partida_id": partida,
                "sinopsis": sinopsis,
                "tasaCambio": tasaCambio,
                "balance": balance,
                "empresa": empresa,
                "empresasData": empresasData,
                "secuenciasFirmasData": secuenciasFirmasData,
                "fecha_hora_actual": fecha_hora_actual,
                "cuentasData": cuentasData,
                "detallesPartidaData": detallesPartidaData,
            }
            
            return render(request, 'contabilidad/partida_manual.html', context)


def insert_update_partidas_header_details(request):
    try:
        existe = 0
        varID = 0
        numPartida = ''

        partida_id = request.POST.get('partida_id')
        tipo_partida = request.POST.get('tipo_partida')
        sinopsisPartida = request.POST.get('sinopsisPartida')
        fecha_partida = request.POST.get('fecha_partida')
        debe = request.POST.get('debe')
        haber = request.POST.get('haber')
        empresa = request.POST.get('empresa')
        tasa = request.POST.get('tasa')
        balance = request.POST.get('balance')
        balanceD = request.POST.get('balanceD')
        opcion = request.POST.get('opcion')
        
        sistema = 12

        arr_detalles = json.loads(request.POST.get('arrDetalles', '[]'))
        
        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('CONTA_INSERT_UPDATE_ENCABEZADO_PARTIDA', [
                partida_id,
                tipo_partida,
                sinopsisPartida,
                sistema,
                fecha_partida,
                tasa,
                balance,
                balanceD,
                empresa,
                userName,
                opcion
            ]) 
            results = cursor.fetchall()

            if results:
                for result in results:
                    existe = result[0]
                    varID = result[1]
                    numPartida = result[2]

        appConn.commit()

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('CONTA_DELETE_DETALLES_X_PARTIDA', [
                partida_id,
                userName
            ])
        
        appConn.commit()
        for detalle in arr_detalles:
            detalle_id = detalle.get('detalle_id')
            codigo = detalle.get('codigo')
            texto = detalle.get('texto')
            sinopsis = detalle.get('sinopsis', '')
            debe = detalle.get('debe', '')
            haber = detalle.get('haber', '')

            with connections['universal'].cursor() as cursor:
                cursor.callproc('CONTA_INSERT_UPDATE_DETALLE_PARTIDA', [
                    detalle_id,
                    varID,
                    numPartida,
                    fecha_partida,
                    codigo,
                    texto,
                    sinopsis,
                    debe,
                    haber,
                    userName,
                    opcion
                ])

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)



def get_tasa_cambio_x_fecha(request):
    try:
        existe = 0
        varID = 0
        tasa_cambio = 0.00

        fecha_partida = request.POST.get('fecha_partida')

        udcConn = connections['universal']
        with udcConn.cursor() as cursor:
            cursor.callproc('CONTA_GET_TASA_CAMBIO_X_FECHA', [
                fecha_partida
            ])
            result = [col[0] for col in cursor.description]
            tasaCambioQuery = [dict(zip(result, row)) for row in cursor.fetchall()]
            cursor.nextset()

            if tasaCambioQuery:
                for tc in tasaCambioQuery:
                    tasa_cambio = tc["TasaCambio"]

        datos = {'save': 1, 'tasa_cambio': tasa_cambio}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)




def conta_tasa_cambio(request):
    user_id = request.session.get('user_id', '')
    tasaCambio_CNT = request.session.get('tasaCambio_CNT', 0)
    adminIT = request.session.get('contabilidadAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if tasaCambio_CNT == 1 or adminIT == 1:
            empresasData = obtener_empresas()

            context = {
                "empresasData": empresasData,
            }
            
            return render(request, 'catalogos/tasa_cambio.html', context)



def dataTasaCambio(request):
    opcion = request.POST.get('opcion')

    try:
        udcConn = connections['universal']
        with udcConn.cursor() as cursor:
            cursor.callproc("CONTA_GET_TASA_CAMBIO", [opcion])
            column_names = [desc[0] for desc in cursor.description]
            tasaCambioData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': tasaCambioData})
    except Exception as e:
        return JsonResponse({'error': str(e)})



def insert_update_tasa_cambio(request):
    try:
        existe = 0

        tasa_id = request.POST.get('tasa_id')  
        fecha = request.POST.get('fecha')
        tasaCambio = request.POST.get('tasaCambio')
        tasaCompra = request.POST.get('tasaCompra')
        tasaBanco = request.POST.get('tasaBanco')

        opcion = request.POST.get('opcion')

        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('CONTA_INSERT_UPDATE_TASA_CAMBIO', [
                tasa_id,
                fecha,
                tasaCambio,
                tasaCompra,
                tasaBanco,
                userName,
                opcion
            ]) 
            results = cursor.fetchall()

            if results:
                for result in results:
                    existe = result[0]
            else:
                existe = 0
        
        appConn.close()

        datos = {'save': 1, 'existe': existe}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)



def update_status_tasa_cambio(request):
    try:
        tasa_id = request.POST.get('tasa_id')
        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('CONTA_STATUS_UPDATE_TASA_CAMBIO', [
                tasa_id,
                userName
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)




def conta_libro_mayor(request, empresa):
    user_id = request.session.get('user_id', '')
    libroMayor_CNT = request.session.get('libroMayor_CNT', 0)
    adminIT = request.session.get('contabilidadAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if libroMayor_CNT == 1 or adminIT == 1:
            empresasData = obtener_empresas()

            cuentasData = ""
            try:
                udcConn = connections['universal']
                with udcConn.cursor() as cursor:
                    cursor.callproc("CONTA_GET_ALL_CUENTAS_LIBRO_MAYOR", [empresa])
                    column_names = [desc[0] for desc in cursor.description]
                    cuentasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                # Cierra la conexión
                udcConn.close()
            except Exception as e:
                # Manejo de excepciones, puedes personalizar esto según tus necesidades
                return JsonResponse({'error': str(e)})
            
            context = {
                "empresa": empresa,
                "empresasData": empresasData,
                "cuentasData": cuentasData,
                'date1': datetime.now().strftime('%Y-%m-01'),
                'date2': datetime.now().strftime('%Y-%m-%d'),
            }
            
            return render(request, 'contabilidad/libro_mayor.html', context)




def dataLibroMayor(request):
    codigo = request.POST.get('codigo')
    date1 = request.POST.get('date1')
    date2 = request.POST.get('date2')
    empresa = request.POST.get('empresa')

    try:
        udcConn = connections['universal']
        with udcConn.cursor() as cursor:
            cursor.callproc("CONTA_GET_LIBRO_MAYOR_X_CUENTA", [codigo, date1, date2, empresa])
            column_names = [desc[0] for desc in cursor.description]
            libroMayorData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': libroMayorData})
    except Exception as e:
        return JsonResponse({'error': str(e)})




def conta_entregar_periodos(request, empresa):
    user_id = request.session.get('user_id', '')
    entregarPeriodo_CNT = request.session.get('entregarPeriodo_CNT', 0)
    adminIT = request.session.get('contabilidadAdminIT', 0)

    MesInicial = ''
    AnioInicial = ''
    MesFinal = ''
    AnioFinal = ''
    mesInicial_Text = ''
    mesFinal_Text = ''
    fechaPartida = ''

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if entregarPeriodo_CNT == 1 or adminIT == 1:
            empresasData = obtener_empresas()


            try:
                udcConn = connections['universal']
                with udcConn.cursor() as cursor:
                    cursor.callproc("CONTA_GET_PERIODOS_ENTREGADOS", [empresa])
                    column_names = [desc[0] for desc in cursor.description]
                    periodosEntregadosQuery = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                    
                    if periodosEntregadosQuery:
                        for p in periodosEntregadosQuery:

                            MesInicial = p["MesInicial"]
                            AnioInicial = p["AnioInicial"]
                            MesFinal = p["MesFinal"]
                            AnioFinal = p["AnioFinal"]
                            mesInicial_Text = p["mesInicial_Text"]
                            mesFinal_Text = p["mesFinal_Text"]
                            fechaPartida = p["fechaPartida"].strftime('%Y-%m-%d')
                
                # Cierra la conexión
                udcConn.close()
            except Exception as e:
                # Manejo de excepciones, puedes personalizar esto según tus necesidades
                return JsonResponse({'error': str(e)})
            

            context = {
                "empresa": empresa,
                "empresasData": empresasData,
                "MesInicial": MesInicial,
                "AnioInicial": AnioInicial,
                "MesFinal": MesFinal,
                "AnioFinal": AnioFinal,
                "mesInicial_Text": mesInicial_Text,
                "mesFinal_Text": mesFinal_Text,
                "fechaPartida": fechaPartida,
                'date1': datetime.now().strftime('%Y-%m-01'),
                'date2': datetime.now().strftime('%Y-%m-%d'),
            }
            
            return render(request, 'contabilidad/entregar_periodos.html', context)

