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




LOGIN_URL = 'http://3.230.160.184:81/CWS'


def vista_principal(request):
    # Obtener el user_id de la sesión
    user_id = request.session.get('user_id', None)

    # Si no hay usuario en la sesión, redirigir al login
    if not user_id:
        request.session.flush()
        return HttpResponseRedirect(LOGIN_URL)
    
    # Llamada al procedimiento almacenado para obtener los menús
    with connections['global_nube'].cursor() as cursor:
        cursor.callproc('WEB_GET_MENUS_GRUPO_USUARIO', [user_id, 19])
        myMenus = cursor.fetchall()

    # Procesar los resultados del procedimiento almacenado
    menus = []
    if myMenus:
        for menu in myMenus:
            # Solo agregar los menús a los que el usuario tiene acceso
            if menu[6] == 1:  # 'tiene_acceso' es el índice 6
                menus.append({
                    'posicionMenu': menu[2],  # Posición del menú
                    'nombreMenu': menu[3],    # Nombre del menú
                    'permiso': menu[4],       # Permiso del usuario
                })

    # Si la solicitud es AJAX, retornar los menús como JSON junto con el user_id
    if request.is_ajax():
        return JsonResponse({'menus': menus, 'user_id': user_id})

    # Si no es una solicitud AJAX, renderizar el template normal
    return render(request, 'lobby.html')    


def check_session(request):
    if request.session.get('user_id'):
        return JsonResponse({'status': 'active'})
    else:
        return JsonResponse({'status': 'expired'})


def get_info_menu(request):
    var_modulo = request.GET.get('varModulo')  # Obtener parámetro 'varModulo' desde la URL
    var_menu = request.GET.get('varMenu')      # Obtener parámetro 'varMenu' desde la URL

    with connections['global_local'].cursor() as cursor:
        # Ejecutar el procedimiento almacenado con los parámetros
        cursor.execute("CALL GS_GET_INFO_MENU(%s, %s)", [var_modulo, var_menu])
        rows = cursor.fetchall()

    # Formatear los resultados en un diccionario
    results = []
    for row in rows:
        results.append({
            'id': row[0],            # Mapea las columnas según el orden en tu SELECT
            'posicion': row[1],
            'fkModulo': row[2],
            # Añade los campos necesarios
        })

    return JsonResponse(results, safe=False)

def menuRequest(request):
    user_id = request.POST.get('user_id')
    username = request.POST.get('username')
    menu = request.POST.get('menu')
    

    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc("SDK_GET_USER_MENU_ACCESS", [menu, user_id])
            menuQuery = cursor.fetchall()
            
            appConn.close()

            if menuQuery:
                menu = 1

                web_get_menus_grupo_usuario(request)

        datos = {'save': 1, 'module': menu}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)



def verificar_acceso(request):
    user_id = request.POST.get('user_id')
    num_menu = request.POST.get('num_menu')
    modulo = request.POST.get('modulo')
    descripcion = ''

    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc("GS_GET_INFO_MENU", [modulo, num_menu])
            menuQuery = cursor.fetchall()
            
            appConn.close()

            if menuQuery:
                for menu in menuQuery:
                    descripcion = menu[10]
                
        datos = {'save': 1, 'descripcion': descripcion}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)


def web_get_menus_grupo_usuario(request):
    user_id = request.session.get('user_id', '')
    request.session['talentoHumanoAdminIT'] = 0

    appConn = connections['global_nube']
    with appConn.cursor() as cursor:
        cursor.callproc('WEB_GET_ADMIN_IT', [user_id, 19])
        adminITQuery = cursor.fetchall()

        # Procesar los menús y establecer valores en la sesión
        if adminITQuery:
            request.session['talentoHumanoAdminIT'] = 1

        appConn.close()

    appConn = connections['global_nube']
    with appConn.cursor() as cursor:
        cursor.callproc('WEB_GET_MENUS_GRUPO_USUARIO', [user_id, 19])
        menuQuery = cursor.fetchall()

        # Procesar los menús y establecer valores en la sesión
        if menuQuery:
            for menu in menuQuery:
                posicion_menu = menu[2]
                permiso_menu = menu[6]

                if posicion_menu == 'TH201' and permiso_menu == 1:
                    request.session['verTodasLasAsistencias'] = 1
                elif posicion_menu == 'TH201' and permiso_menu == 0:
                    request.session['verTodasLasAsistencias'] = 0

                if posicion_menu == 'TH202' and permiso_menu == 1:
                    request.session['verAsistenciasMisColaboradores'] = 1
                elif posicion_menu == 'TH202' and permiso_menu == 0:
                    request.session['verAsistenciasMisColaboradores'] = 0

                if posicion_menu == 'TH203' and permiso_menu == 1:
                    request.session['configTurnos'] = 1
                elif posicion_menu == 'TH203' and permiso_menu == 0:
                    request.session['configTurnos'] = 0
        appConn.close()









def vista_principal_empleados(request, ):
    posiciones = obtener_posicion()
    estados_empleado = obtener_estados_empleado()
    
    return render(request, 'empleados.html', {
        'posiciones': posiciones,
        'estado': estados_empleado
    })


def gestion_empleado(request, parametro=None):
    habilidades = obtener_habilidades()
    departamentos = obtener_departamento()
    centros =get_centro_costos()
  
    posiciones = obtener_posicion()
    estados_empleados, estado_activo_id = obtener_estados_empleado()
    formas_pago = obtener_formas_pago()
    tipo_contratos = get_tipo_contratos()
    categoria_retiro = obtener_categorias_retiros()
    motivos_retiro = obtener_motivos_retiros()
    forma_pago = obtener_formas_pago()
    obtener_cuenta= obtener_tipo_cuenta()
    paises = obtener_paises()
    generos = obtener_generos()
    estado_civil=obtener_estados_civiles()
    certificacion=obtener_certificaciones()
    sucursal=obtener_sucursales()
    curriculo =obtener_todos_tipos_curriculum()
    beneficios_adicional=obtener_beneficios_adicionales()
    beneficios_laborales= obtener_beneficios_laborales()
    estado_curriculum= obtener_estado_curriculum()
    banco= obtener_banco()
    empresas =obtener_empresas()
    nacionalidad=obtener_cat_nacionalidad
    centros_educativos = obtener_cat_centros_educativos()
    profesiones_oficios = obtener_profesiones_oficios()
    parentesco= obtener_parentesco()
    asociaciones= obtener_asociacion()
    obtener_equipos = obtener_equipos_()
    jefes=get_empleados_info_jefes()
    superior=get_empleados_info_superiores()
    gerentes=get_empleados_info_gerente
    empresa_seguros=obtener_empresa_seguros()
    sangre=obtener_tipo_sangre()
    enfermedades=obtener_enfermedades()
    roles=get_tipo_empleados()
    departament=getDepartamentoPais()
    municipies=getMunicipiesDepartamentoPais()
    barrios_municipies=GETBARRIOSCOLONIAS()
    vehiculo =obtener_tipo_vehiculo()
    poliza = obtener_poliza_por_empresa_seguros()
    grados = obtener_listado_grado()
    usuarios = obtener_usuarios()
    usuarios_biometrico = obtener_usuarios_biometrico()

    context = {
        'parametro': parametro,
        'habilidades': habilidades,
        'departamentos': departamentos,
        'estados_empleados': estados_empleados,  
        'estado_activo_id': estado_activo_id, 
        'formas_pago': formas_pago,
        'posiciones': posiciones,
        'contratos': tipo_contratos,
        'categorias': categoria_retiro,  
        'motivos': motivos_retiro,
        'formas': forma_pago,      
        'cuentas': obtener_cuenta,
        'paises': paises,
        'generos': generos,
        'civil': estado_civil,
        'certificaciones': certificacion,
        'sucursales': sucursal,
        'curriculos': curriculo,
        'beneficios': beneficios_adicional,
        'laborales': beneficios_laborales,
        'estado_curriculum': estado_curriculum,
        'bancos': banco,
        'empresas': empresas,
        'nacionalidades': nacionalidad, 
        'centros_educativos' : centros_educativos,
        'profesiones_oficios': profesiones_oficios,
        'parentescos': parentesco,
        'asociaciones': asociaciones,
        'equipos': obtener_equipos,
        'jefes': jefes,
    	'superior': superior,
        'gerentes': gerentes,
        'empresa_seguros': empresa_seguros,
        'sangres': sangre,
        'enfermedades': enfermedades,
        'roles': roles,
        'departament_pais': departament,
        'municipies_departamento': municipies,
        'usuarios': usuarios,
        'barrios_municipios': barrios_municipies,
        'vehiculo': vehiculo,
        'poliza': poliza,
        'grado': grados,
        'centros': centros,
        'usuarios_biometrico' : usuarios_biometrico   
    }
    
    return render(request, 'gestion_empleado.html', context)


def crear_departamento(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')  # Valor por defecto si no se proporciona

        # Validar que el campo nombre esté presente
        if not nombre:
            return JsonResponse({'status': 'fail', 'error': 'El campo nombre es obligatorio.'}, status=400)

        try:
            # Insertar en la base de datos local y obtener el último ID insertado
            with connections['global_local'].cursor() as cursor_local:
                cursor_local.callproc('TH_INSERT_GRUPOS', [
                    nombre, 
                    descripcion, 
                    11,  # fkModulo predeterminado a 11
                    0    # isBuiltIn predeterminado a 0 (falso)
                ])
                # Obtener el último ID del grupo recién insertado
                resultado = cursor_local.fetchone()
                nuevo_grupo_id = resultado[0] if resultado else None

            if nuevo_grupo_id:
                return JsonResponse({'status': 'success', 'id': nuevo_grupo_id, 'message': 'Departamento creado exitosamente'})
            else:
                return JsonResponse({'status': 'fail', 'error': 'No se pudo obtener el ID del grupo recién insertado.'}, status=500)

        except OperationalError as e:
            # Mostrar el mensaje exacto que causa el error
            error_message = str(e)
            logger.error(f"Error en la base de datos: {error_message}")
            
            # Devuelve el mensaje exacto si el nombre ya existe
            if "El nombre del departamento ya existe" in error_message:
                return JsonResponse({'status': 'fail', 'error': 'El nombre del departamento ya existe.'}, status=400)
            else:
                return JsonResponse({'status': 'fail', 'error': 'Error en la base de datos.'}, status=500)
        
        except Exception as e:
            # Manejar errores inesperados
            logger.error(f"Error inesperado: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': f'Ocurrió un error inesperado: {str(e)}'}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido.'}, status=405)

def crear_area(request):
    if request.method == 'POST':
        sub_grupo = request.POST.get('nombre_area')
        FKgrupo = request.POST.get('departamento_empresa')
        creado_por = request.POST.get('creado_por')

        if not all([sub_grupo, FKgrupo, creado_por]):
            return JsonResponse({'status': 'fail', 'error': 'Todos los campos son obligatorios.'}, status=400)

        try:
            with connections['global_local'].cursor() as cursor_local:
                # Llamar al procedimiento almacenado
                cursor_local.callproc('TH_INSERT_SUB_GRUPOS', [
                    sub_grupo, 
                    FKgrupo, 
                    creado_por
                ])
                
                # Obtener el ID del subgrupo recién insertado
                resultado = cursor_local.fetchone()
                print(f"Resultado obtenido: {resultado}")  # Debugging para ver qué está devolviendo

                if resultado:
                    nuevo_sub_grupo_id = resultado[0]
                    return JsonResponse({'status': 'success', 'id': nuevo_sub_grupo_id, 'message': 'Área creada exitosamente.'})
                else:
                    print("Error: No se obtuvo un resultado válido.")
                    return JsonResponse({'status': 'fail', 'error': 'No se pudo obtener el ID del área recién insertada.'}, status=500)

        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': f'Ocurrió un error inesperado: {str(e)}'}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido.'}, status=405)

def crear_cargo(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        grado = request.POST.get('grado', 'D')
        id_area = request.POST.get('id_area')
        creado_por = request.POST.get('creado_por')
        modificado_por = request.POST.get('modificado_por', creado_por)

        # Validar que los campos requeridos estén presentes
        if not all([nombre, id_area, creado_por]):
            return JsonResponse({'status': 'fail', 'error': 'Todos los campos son obligatorios.'}, status=400)

        try:
            # Conexión a la base de datos 'global_local' y ejecución del procedimiento
            with connections['global_local'].cursor() as cursor_local:
                # Llamada al procedimiento almacenado 'TH_INSERT_CARGOS_AREA'
                cursor_local.callproc('TH_INSERT_CARGOS_AREA', [
                    nombre,
                    grado,
                    id_area,
                    creado_por,
                    modificado_por
                ])

                # Obtener el resultado del procedimiento
                resultado = cursor_local.fetchone()

                if resultado:
                    nuevo_cargo_id = resultado[0]  # Obtener el ID del cargo
                else:
                    return JsonResponse({'status': 'fail', 'error': 'No se pudo obtener el ID del cargo recién insertado.'}, status=500)

            # Retornar el ID del nuevo cargo en la respuesta JSON
            return JsonResponse({'status': 'success', 'id': nuevo_cargo_id})

        # Manejar errores de duplicado
        except OperationalError as e:
            error_message = str(e)
            logger.error(f"Error en la base de datos: {error_message}")

            # Si el error es porque el cargo ya existe
            if "El cargo ya existe para esta área" in error_message:
                return JsonResponse({'status': 'fail', 'error': 'El cargo ya existe para esta área.'}, status=400)
            else:
                return JsonResponse({'status': 'fail', 'error': 'Error en la base de datos.'}, status=500)

        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': f'Ocurrió un error inesperado: {str(e)}'}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido.'}, status=405)



def obtener_departamento():
    with connections['global_local'].cursor() as cursor:
        cursor.callproc('TH_GET_GRUPOS_DEPARTAMENTOS')  
        results = cursor.fetchall()

    return results

from django.core.cache import cache


def filtrar_subgrupos_por_grupo(request):
    if request.method == 'GET':
        pk_grupo = request.GET.get('pk_grupo')
        cache_key = f'subgrupos_{pk_grupo}'
        subgrupos_data = cache.get(cache_key)

        if not subgrupos_data:
            try:
                with connections['global_nube'].cursor() as cursor:
                    cursor.execute("CALL FiltrarSubgruposPorGrupo(%s)", [pk_grupo])
                    subgrupos = cursor.fetchall()

                # Convertir el resultado en un formato JSON
                subgrupos_data = []
                for subgrupo in subgrupos:
                    subgrupos_data.append({
                        'PKsubgrupo': subgrupo[0],
                        'sub_grupo': subgrupo[1]
                    })

                # Guardar en caché por 10 minutos
                cache.set(cache_key, subgrupos_data, 600)

            except Exception as e:
                # Capturar el error y enviarlo como respuesta JSON detallada
                error_message = str(e)
                print(f"Error en la consulta de subgrupos: {error_message}")  # Lo imprime en la consola
                return JsonResponse({
                    'error': f'Error interno del servidor: {error_message}'
                }, status=500)

        return JsonResponse({'subgrupos': subgrupos_data})

def obtener_cargos_por_area(request):
    if request.method == 'POST':
        try:
            # Intentar decodificar los datos como JSON
            data = json.loads(request.body.decode('utf-8'))
            id_area = data.get('id_area')
        except json.JSONDecodeError:
            # Si la decodificación falla, asumir que los datos vienen de un formulario estándar
            id_area = request.POST.get('id_area')

        # Validar que se haya proporcionado el parámetro `id_area`
        if not id_area:
            return JsonResponse({'status': 'fail', 'error': 'El parámetro id_area es requerido'}, status=400)

        # Crear una clave única de caché para este área
        cache_key = f'cargos_area_{id_area}'
        cargos_area = cache.get(cache_key)

        # Si los resultados están en caché, devolverlos directamente
        if cargos_area:
            return JsonResponse({'status': 'success', 'cargos': cargos_area})

        try:
            # Si no hay resultados en caché, ejecutar el procedimiento almacenado
            with connections['global_nube'].cursor() as cursor:
                cursor.execute("CALL TH_GET_CARGOS_AREAS(%s)", [id_area])
                cargos = cursor.fetchall()

            # Construir la respuesta JSON con los resultados
            cargos_area = [
                {
                    'id': cargo[0],  # Considerando que el id_cargo es el primer elemento
                    'nombre': cargo[1]  # Considerando que el nombre del cargo es el segundo
                } for cargo in cargos
            ]

            # Almacenar los resultados en caché por 10 minutos (600 segundos)
            cache.set(cache_key, cargos_area, timeout=600)

            return JsonResponse({'status': 'success', 'cargos': cargos_area})

        except Exception as e:
            # Manejo de errores y registro en caso de excepción
            logger.error(f'Error retrieving cargos: {e}', exc_info=True)
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    else:
        # Responder con error si el método no es POST
        return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)
  

def contar_empleados(request):
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_COUNT_EMPLEADOS')
        total_empleados = cursor.fetchone()[0]  # Obtener el resultado del procedimiento
    return JsonResponse({'total_empleados': total_empleados})

def validar_contrato(request):
    if request.method == 'POST':
        empleado_id = request.POST.get('empleado_id')
        
        # Llamada al procedimiento almacenado
        with connections['universal'].cursor() as cursor:
            cursor.callproc('EVA_VALIDATE_CONTRATO', [empleado_id])
            resultado = cursor.fetchall()

        # Si no hay resultados, el empleado no tiene contrato válido
        if len(resultado) == 0:
            return JsonResponse({'status': 'error', 'message': 'El empleado no tiene un contrato activo. Por favor, agregue un contrato antes de continuar.'})
        else:
            # Si el empleado tiene contrato, solo se devuelve el status sin mensaje
            return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'})



def obtener_tipo_sangre():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_TIPO_SANGRE')  
        results = cursor.fetchall()
    return results

def obtener_listado_grado():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('EVA_LIST_GRADOS')  
        results = cursor.fetchall()
    return results

def obtener_tipo_vehiculo():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('GET_CAT_TIPO_VEHICULO')  
        results = cursor.fetchall()
    return results

def obtener_poliza_por_empresa_seguros():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_POLIZAS_POR_EMPRESA_SEGUROS')  
        results = cursor.fetchall()
    return results

    


def getDepartamentoPais():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('GET_DEPARTMENT_PAIS')  
        results = cursor.fetchall()
    return results

def getMunicipiesDepartamentoPais():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('GET_MUNICIPAL_DEPARTAMENT')  
        results = cursor.fetchall()
    return results

def GETBARRIOSCOLONIAS():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('GETBARRIOSCOLONIAS')  
        results = cursor.fetchall()
    return results



def obtener_enfermedades():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_CAT_ENFERMEDADES_BASE')  
        results = cursor.fetchall()
    return results

def obtener_motivos_retiros():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_CAT_MOTIVOS_RETIRO')  
        results = cursor.fetchall()

    return results

def obtener_equipos_():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('obtener_equipos')  
        results = cursor.fetchall()

    return results


def obtener_parentesco():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('obtener_parentescos')  
        results = cursor.fetchall()

    return results

def obtener_asociacion():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('CAT_GET_ASOCIACIONES')  
        results = cursor.fetchall()

    return results


def obtener_asociaciones(request):
    id_empleado = request.GET.get('id_empleado')  # Obtener el ID del empleado desde los parámetros de la solicitud

    try:
        if not id_empleado:
            raise ValueError("El ID del empleado no fue proporcionado.")
        
        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_GET_ASOCIACIONES_EMPLEADO', [id_empleado])
            results = cursor.fetchall()

        data = [
            {
                "id_asociacion": row[0],
                "id_empleado": row[1],
                "nombre_asociacion": row[2],
                "id_asociacion_catalogo": row[3]
            }
            for row in results
        ]

        return JsonResponse({'status': 'success', 'data': data})
    
    except Exception as e:
        logger.error(f"Error al obtener asociaciones para el empleado {id_empleado}: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



def obtener_profesiones_oficios():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('obtener_profesiones_oficios')  
        results = cursor.fetchall()
    return results


def obtener_empresas():
    empresas_list = []  # Inicializar la variable
    try:
        with connections['global_nube'].cursor() as cursor:
            cursor.execute("CALL TH_GET_EMPRESAS()")
            empresas = cursor.fetchall()
            empresas_list = [{'id': empresa[1], 'nombre': empresa[0]} for empresa in empresas]
    except Exception as e:
        print(e)
    return empresas_list  

def obtener_sucursales():
        with connections['global_nube'].cursor() as cursor:
            cursor.callproc('obtener_sucursales')  
            results = cursor.fetchall()

        return results

def obtener_direccion_sucursal(request):
    if request.method == 'GET':
        id_sucursal = request.GET.get('id_sucursal')

        if id_sucursal:
            with connections['global_nube'].cursor() as cursor:
                cursor.callproc('TH_GET_DIRECCION_SUCURSAL', [id_sucursal])
                result = cursor.fetchone()
            
            # Verificar si se encontró la sucursal
            if result:
                direccion = result[2]  # Suponiendo que la dirección está en la columna 2
                return JsonResponse({'direccion': direccion})
            else:
                return JsonResponse({'error': 'Sucursal no encontrada.'}, status=404)
        else:
            return JsonResponse({'error': 'ID de sucursal no proporcionado.'}, status=400)

    return JsonResponse({'error': 'Método no permitido.'}, status=405)
            


def obtener_certificaciones():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_CAT_CERTIFICACIONES')  
        results = cursor.fetchall()

    return results



def obtener_usuarios():
    with connections['global_nube'].cursor() as cursor:
        cursor.callproc('TH_GET_USUARIOS_GLOBAL')  
        results = cursor.fetchall()

    return results


def obtener_usuarios_biometrico():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_ASOCIAR_EMPLEADOS_BIOMETRICOS_FICHA_EMPLEADO')  
        results = cursor.fetchall()

    return results

@csrf_exempt
def obtener_motivos_retiro(request):
    if request.method == 'GET':
        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_CAT_MOTIVOS_RETIRO')
                result = cursor.fetchall()
                motivos = [{'id_motivo_retiro': row[0], 'motivo_retiro': row[1]} for row in result]
            return JsonResponse({'status': 'success', 'motivos': motivos})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def obtener_formas_pago():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_FORMAS_PAGO')  
        results = cursor.fetchall()

    return results

def obtener_tipo_cuenta():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('VAIC_TH_GET_TIPOS_CUENTA')  
        results = cursor.fetchall()
    return results

def obtener_paises():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_CAT_PAISES')  
        results = cursor.fetchall()
    return results

def obtener_cat_nacionalidad(request):
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_CAT_PAISES')  
        results = cursor.fetchall()
    return results
    
    

def obtener_cat_centros_educativos():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('cat_obtener_centros_educativos')  
        results = cursor.fetchall()
    return results



def obtener_generos():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_GENERO')  
        results = cursor.fetchall()
    return results

def obtener_estados_civiles():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_CAT_ESTADO_CIVIL')  
        results = cursor.fetchall()
    return results

def get_centro_costos():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('VAIC_TH_CAT_CENTROS')  
        results = cursor.fetchall()
    return results

def get_empleados_info_gerente():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_GERENTES')
        resultados = cursor.fetchall()       
    return resultados

def get_tipo_empleados():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_TIPO_EMPLEADO')
        resultados = cursor.fetchall()       
    return resultados



def get_empleados_info_jefes():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_JEFES')
        resultados = cursor.fetchall()     
    return resultados

def get_empleados_info_superiores():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_SUPERIORES')
        resultados = cursor.fetchall()     
    return resultados

def obtener_categorias_retiros():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_CAT_CATEGORIAS_RETIRO')  
        results = cursor.fetchall()

    return results

def get_tipo_contratos():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('EVA_GET_TIPOS_CONTRATOS', [3])  
        results = cursor.fetchall()

    return results


def obtener_todos_tipos_curriculum():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_ALL_TIPOS_CURRICULUM')  
        results = cursor.fetchall()

    return results

def obtener_habilidades():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_HABILIDADES')  
        results = cursor.fetchall()
    return results

def obtener_beneficios_adicionales():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_BENEFICIOS_ADICIONALES')  
        results = cursor.fetchall()
    return results

def obtener_beneficios_laborales():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_BENEFICIOS_LABORALES')  
        results = cursor.fetchall()
    return results

def obtener_estado_curriculum():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_ESTADO_CURRICULUM')  
        results = cursor.fetchall()
    return results

def obtener_banco():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_BANCOS')  
        results = cursor.fetchall()
    return results


def obtener_empresa_seguros():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_EMPRESAS_SEGUROS')  
        results = cursor.fetchall()
    return results

def obtener_cargo():
    with connections['global_nube'].cursor() as cursor:
        cursor.callproc('TH_GET_SUB_GRUPOS_AREA')  
        results = cursor.fetchall()
    return results



def obtener_estados_empleado():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_ESTADOS_EMPLEADOS')
        results = cursor.fetchall()

    # Crear la lista de estados con las claves correctas
    estados_empleados = [{'id_estado': estado[0], 'estado_empleado': estado[1]} for estado in results]

    # Identificar el estado "Activo"
    estado_activo_id = None
    for estado in estados_empleados:
        if estado['estado_empleado'].strip().lower() == 'activo':
            estado_activo_id = estado['id_estado']
            break

    return estados_empleados, estado_activo_id

def obtener_estados_empleado_json(request):
    estados_empleados, estado_activo_id = obtener_estados_empleado()
    data = {
        'estados': estados_empleados,
        'estado_activo_id': estado_activo_id,
    }
    return JsonResponse(data)




@csrf_exempt
def obtener_estados_empleados(request):
    if request.method == 'GET':
        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_ESTADOS_EMPLEADOS')
                estados = cursor.fetchall()
                estados_empleados = [{'id': estado[0], 'nombre': estado[1]} for estado in estados]
            return JsonResponse({'status': 'success', 'estados': estados_empleados})
        except Exception as e:
            logger.error(f'Error retrieving estados empleados: {e}', exc_info=True)
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def obtener_formas_pago():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_FORMAS_PAGO')  # Llama al procedimiento almacenado
        results = cursor.fetchall()
    return results

def obtener_posicion():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_GET_POSICIONES')  # Llama al procedimiento almacenado
        results = cursor.fetchall()
    return results

@csrf_exempt
def obtener_posiciones(request):
    if request.method == 'GET':
        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_POSICIONES')
                results = cursor.fetchall()
                posiciones = [{'id': row[0], 'nombre': row[1]} for row in results]

            return JsonResponse({'status': 'success', 'posiciones': posiciones})
        except Exception as e:
            logger.error(f'Error retrieving posiciones: {e}', exc_info=True)
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail'}, status=400)

def modulos(request):
    return render(request, 'modulos.html')

import logging
from django.db import connections, OperationalError

logger = logging.getLogger(__name__)

def insertar_identidad(request):
    if request.method == 'POST':
        identidad = request.POST.get('identidad')
        creado_por = request.POST.get('creado_por')
        logger.debug(f'Received identidad: {identidad}')
        print(request.POST)
        try:
            with connections['universal'].cursor() as cursor:
                # Insertar por identidad
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_DNI', [
                            identidad,  # p_identidad
                            '',         # p_nombre_completo
                            '',         # p_apellido_completo
                            0,          # p_rtn
                            0,          # p_telefono
                            '',         # p_correo
                            '',         # p_direccion
                            0.00,       # p_distancia_km
                            '',         # p_placa_vehiculo_privada
                            0,          # p_id_nacionalidad
                            0,          # p_id_sexo
                            '',         # p_pasaporte
                            '0000-00-00', # p_fecha_nacimiento
                            0,          # p_pais_nacimiento
                            '',         # p_imagen
                            0,          # p_id_banco
                            '',         # p_cuenta_bancaria
                            0,          # p_id_nivel_certificado
                            '',         # p_campo_estudio
                            0,          # p_estado
                            creado_por  # p_creado_por
                        ])

                result = cursor.fetchone()
                id_empleado = result[0]  # Obtener el ID del empleado
                codigo_empleado = result[1]  # Obtener el código del empleado
                logger.debug(f'Inserted id_empleado: {id_empleado}, codigo_empleado: {codigo_empleado}')

            # Asegurarse de cerrar el cursor antes de realizar la segunda operación
            with connections['universal'].cursor() as cursor:
                 cursor.callproc('TH_INSERT_TH_EMPLEADOS_FICHAS', [
                    id_empleado,               # p_id_empleado
                    0,                         # p_id_gerente
                    0,                         # p_id_jefe_inmediato
                    0,                         # p_id_jefe_inmediato
                    '',                        # p_dirrecion_laboral
                    '',                        # p_correo_empresarial
                    '',                        # p_telefono_empresarial
                    0,                         # p_tipo_cuenta
                    0,                         # p_id_centro_costo
                    '',                        # p_id_cuenta_contable
                    0,                         # p_id_tipo_contrato
                    '0000-00-00',              # p_fecha_ingreso
                    0,                         # p_id_categoria_retiro
                    0,                         # p_id_motivo_retiro
                    '',                        # p_observaciones_retiro
                    '0000-00-00',              # p_fecha_retiro
                    0.00,                      # p_salario
                    '0000-00-00',              # p_inicio_contrato
                    '0000-00-00',              # p_fin_contrato
                    0,                         # p_id_forma_pago
                    0,                         # p_aplica_seguro
                    1,                         # p_estado
                    creado_por,                # p_creado_por
                    '',                        # observaciones_generales
                    0,                         # p_id_usuario
                    0,                         # p_id_departamento
                    0,                         # p_id_cargo
                    0,                         # p_id_area
                    0,                         # p_id_empresa
                    0,                         # p_id_sucursal
                    0,                         # p_id_empleado_biometrico
                ])

            return JsonResponse({'status': 'success', 'id_empleado': id_empleado, 'codigo_empleado': codigo_empleado})

        except OperationalError as e:
            error_message = str(e)
            logger.error(f'Error inserting identidad (OperationalError): {error_message}', exc_info=True)
            return JsonResponse({'status': 'fail', 'error': 'Ocurrió un error al intentar insertar la identidad.', 'details': error_message}, status=500)

        except Exception as e:
            # Captura y devuelve el traceback completo para depuración
            error_traceback = traceback.format_exc()
            logger.error(f'Error inserting identidad: {e}\n{error_traceback}', exc_info=True)
            return JsonResponse({
                'status': 'fail',
                'error': 'Ocurrió un error inesperado.',
                'traceback': error_traceback  # Incluir el traceback completo en la respuesta
            }, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido.'}, status=405)


def obtener_equipo_empleado(request):
    if request.method == 'GET':
        id_empleado = request.GET.get('id_empleado')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_EMPLEADO_EQUIPO_ASIGNADO', [id_empleado])
                resultados = cursor.fetchall()

                equipo = []
                for row in resultados:
                    equipo.append({
                        'id_equipo_asignado': row[0],
                        'nombre_equipo_asignado': row[1],
                        # Puedes agregar más campos si es necesario
                    })

            return JsonResponse({'data': equipo})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def desactivar_familiar(request):
    try:

        id_familiar = request.POST.get('id_familiar')
        modificado_por = request.session.get('userName', '')

        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_DELETE_EMPLEADOS_FAMILIARES', [id_familiar, modificado_por])

        datos = {'save': 1, 'message': 'Familiar desactivado exitosamente.'}
    except Exception as e:

        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)

@csrf_exempt
def obtener_contactos_emergencia(request):
    if request.method == 'GET':
        id_empleado = request.GET.get('id_empleado')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_EMPLEADOS_CONTACTOS_EMERGENCIA', [id_empleado])
                resultados = cursor.fetchall()

                contactos = []
                for row in resultados:
                    contacto = {
                        'id_contacto': row[0],
                        'id_empleado': row[1],
                        'nombre_contacto': row[2],
                        'telefono_contacto': row[3],
                        'parentesco': row[4],
                        'id_parentesco': row[5]
                    }
                    contactos.append(contacto)

            return JsonResponse({'data': contactos})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def obtener_seguros(request):
    if request.method == 'GET':
        id_empleado = request.GET.get('id_empleado')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_EMPLEADO_SEGUROS', [id_empleado])
                resultados = cursor.fetchall()

                seguros = []
                for row in resultados:
                    seguros.append({
                        'id_seguro': row[0],
                        'id_empleado': row[1],
                        'id_empresa': row[2],  # ID de la empresa de seguros
                        'nombre_seguro': row[3],  # Nombre de la empresa de seguros
                        'id_poliza': row[4],  # ID de la póliza
                        'poliza': row[9],  # Descripción de la póliza
                        'valor_mensual': row[6],  # Valor mensual del seguro
                        'fecha_inicio': row[7],  # Fecha de inicio del seguro
                        'fecha_fin': row[8],  # Fecha final del seguro
                        'estado': row[10],
                        'creado_por': row[11],
                        'fecha_hora_creado': row[12],
                        'modificado_por': row[13],
                        'fecha_hora_modificacion': row[14],
                    })

            return JsonResponse({'data': seguros})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

   

def obtener_beneficio_laboral(request):
    if request.method == 'GET':
        id_empleado = request.GET.get('id_empleado')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_EMPLEADOS_BENEFICIOS_LABORALES', [id_empleado])
                resultados = cursor.fetchall()

                laboral = []
                for row in resultados:
                    laboral.append({
                        'id_beneficio_laboral': row[0],
                        'id_empleado': row[1],
                        'id_laboral': row[2],
                        'nombre_beneficio_cat': row[3],
                        'descripcion': row[5],  # Descripción del beneficio laboral
                        'valor_beneficio': row[6],  # Valor del beneficio
                        'estado': row[7],  # Estado del beneficio
                        'creado_por': row[8],  # Creado por
                        'fecha_hora_creado': row[9],  # Fecha de creación
                        'modificado_por': row[10],  # Modificado por
                        'fecha_hora_modificado': row[11],  # Fecha de modificación
                    })

            return JsonResponse({'data': laboral})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)
def insertar_enfermedad_base(request):
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre_enfermedad = request.POST.get('nombre_enfermedad')
        descripcion = request.POST.get('descripcion')
        creado_por = request.POST.get('creado_por')

        # Verificar que los datos necesarios estén presentes
        if not nombre_enfermedad:
            error_msg = "El nombre de la enfermedad es obligatorio."
            logger.error(error_msg)
            return JsonResponse({'status': 'fail', 'error': error_msg}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                # Añadir logs para depurar la llamada al procedimiento almacenado
                logger.debug(f"Llamando al procedimiento TH_INSERT_CAT_ENFERMEDADES_BASE con parámetros: {nombre_enfermedad}, {descripcion}, {creado_por}")
                
                cursor.callproc('TH_INSERT_CAT_ENFERMEDADES_BASE', [
                    nombre_enfermedad,
                    descripcion,
                    creado_por
                ])

                # Añadir logs para verificar si hay resultados
                resultado = cursor.fetchone()
                logger.debug(f"Resultado obtenido del procedimiento almacenado: {resultado}")
                
                nueva_enfermedad_id = resultado[0] if resultado else None

            return JsonResponse({'status': 'success', 'id': nueva_enfermedad_id})

        except OperationalError as e:
            error_msg = f"Error en la base de datos: {str(e)}"
            logger.error(error_msg)
            return JsonResponse({'status': 'fail', 'error': error_msg}, status=500)
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(error_msg)
            return JsonResponse({'status': 'fail', 'error': error_msg}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def crear_rol_empleado(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre_rol = request.POST.get('nombre-rol')
        descripcion_rol = request.POST.get('descripcion-rol')
    
        # Verificar que los datos necesarios estén presentes
        if not nombre_rol:
            error_msg = "El nombre del rol es obligatorio."
            logger.error(error_msg)
            return JsonResponse({'status': 'fail', 'error': error_msg}, status=400)

        try:
            with connections['universal'].cursor() as cursor:  # Reemplaza 'default' por el nombre de tu conexión si es diferente
                # Añadir logs para depurar la llamada al procedimiento almacenado
                logger.debug(f"Llamando al procedimiento TH_INSERT_ROL_EMPLEADO con parámetros: {nombre_rol}, {descripcion_rol}")
                
                cursor.callproc('CAT_INSERT_TIPO_EMPLEADO', [
                    nombre_rol,
                    descripcion_rol,
                   
                ])

                # Obtener el resultado del procedimiento
                resultado = cursor.fetchone()
                logger.debug(f"Resultado obtenido del procedimiento almacenado: {resultado}")
                
                nuevo_rol_id = resultado[0] if resultado else None

            return JsonResponse({'status': 'success', 'id': nuevo_rol_id})

        except OperationalError as e:
            error_msg = f"Error en la base de datos: {str(e)}"
            logger.error(error_msg)
            return JsonResponse({'status': 'fail', 'error': error_msg}, status=500)
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(error_msg)
            return JsonResponse({'status': 'fail', 'error': error_msg}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def obtener_beneficio_adicional(request):
    if request.method == 'GET':
        id_empleado = request.GET.get('id_empleado')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_EMPLEADOS_BENEFICIOS_ADICIONALES', [id_empleado])
                resultados = cursor.fetchall()

                adicionales = []
                for row in resultados:
                    adicionales.append({
                        'id_beneficio_adicionales': row[0],  # ID del beneficio adicional
                        'nombre_beneficio_cat': row[1],  # Nombre del beneficio adicional desde el catálogo
                        'descripcion': row[2],  # Descripción del beneficio adicional
                        'valor_beneficio': row[3],  # Valor del beneficio adicional
                        'id_beneficio': row[4],  # ID del beneficio en la tabla de catálogos
                    })

            return JsonResponse({'data': adicionales})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)



def obtener_contactos_familiar(request):
    if request.method == 'GET':
        id_empleado = request.GET.get('id_empleado')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_FAMILIARES_EMPLEADO', [id_empleado])
                resultados = cursor.fetchall()

                contactos = []
                for row in resultados:
                    contacto = {
                        'id_familiar': row[0],
                        'id_empleado': row[1],
                        'nombre_familiar': row[2],
                        'telefono_familiar': row[3],
                        'parentesco': row[4],
                        'id_parentesco': row[5], 
                        'estado': row[6],
                        'creado_por': row[7],
                        'fecha_hora_creado': row[8],
                        'modificado_por': row[9],
                        'fecha_hora_modificado': row[10],
                        'residencia': row[11],
                    
                    }

                    contactos.append(contacto)

            return JsonResponse({'data': contactos})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def actualizar_empleado(request):
    if request.method == 'POST':
        try:
            # Obtener los datos del formulario
            id_empleado = request.POST.get('id_empleado')
            nombre_completo = request.POST.get('nombre_empleado', '')
            identidad = request.POST.get('puesto_trabajo')
            rtn = request.POST.get('rtn', 0)
            telefono = request.POST.get('telefono_personal', 0)
            correo = request.POST.get('correo_contacto', '')
            direccion = request.POST.get('direccion_contacto', '')
            distancia_km = request.POST.get('distancia_km', 0.00)
            tipo_vehiculo_privada = request.POST.get('tipo_vehiculo', '')
            placa_vehiculo_privada = request.POST.get('placa_vehiculo', '')
            nacionalidad = request.POST.get('nacionalidad', '0')
            id_sexo = request.POST.get('sexo', 0)
            pasaporte = request.POST.get('pasaporte', '')
            fecha_nacimiento = request.POST.get('fecha_nac', '0000-00-00')
            pais_nacimiento = request.POST.get('nuevo_pais-nac', 0)
            id_banco = request.POST.get('nuevo_banco', 0)
            cuenta_bancaria = request.POST.get('cuenta_bancaria', '')
            id_nivel_certificado = request.POST.get('nivel_certificado', 0)
            campo_estudio = request.POST.get('nuevo_campo-estudio', 0)
            id_municipio = request.POST.get('nuevo_municipio-departamento', 0)
            nombre_ciudad = request.POST.get('ciudad_nac', '')
            profesion = request.POST.get('profesion_empleado', '')
            estado = request.POST.get('estado_empleado')
            modificado_por = request.POST.get('creado_por', '')
            estado_civil = request.POST.get('estado_civil', 0)
            numero_hijos = request.POST.get('numero_hijos', 0)
            apellido_completo = request.POST.get('apellido_empleado', '')
            id_residencia = request.POST.get('residencia', 0)
            id_departamento = request.POST.get('departamento_pais', 0)
            id_barrio = request.POST.get('nuevo_barrio-ciudad', 0)
            id_tipo_sangre = request.POST.get('tipo_sangre', 0)
            id_rol_empleado = request.POST.get('rol_empleado', 0)
            punto_referencia = request.POST.get('punto_referencia', '')
            imagen = request.FILES.get('foto', None)  # Nueva imagen
            foto_actual_base64 = request.POST.get('foto_actual', None)  # Imagen actual en base64

            imagen_path = ''

            # Recuperar la imagen actual desde la base de datos
            try:
                with connections['universal'].cursor() as cursor:
                    cursor.execute("SELECT imagen FROM th_empleados WHERE id_empleado = %s", [id_empleado])
                    imagen_actual_db = cursor.fetchone()

                    print(f"DEBUG: Imagen actual de la DB: {imagen_actual_db}")
            except Exception as e:
                print(f"ERROR al obtener imagen de la base de datos: {str(e)}")
                return JsonResponse({'status': 'fail', 'error': 'Error al obtener imagen'}, status=500)

            # Lógica para manejo de imágenes (nueva o base64)
            if imagen:
                try:
                    imagen_nombre = imagen.name
                    imagen_path = os.path.join('imagenes', imagen_nombre)
                    full_imagen_path = os.path.join(settings.MEDIA_ROOT, imagen_path)
                    print(f"DEBUG: Guardando nueva imagen en: {full_imagen_path}")
                    with open(full_imagen_path, 'wb+') as destination:
                        for chunk in imagen.chunks():
                            destination.write(chunk)
                    print("DEBUG: Nueva imagen guardada correctamente")
                except Exception as e:
                    print(f"ERROR al guardar la nueva imagen: {str(e)}")
                    return JsonResponse({'status': 'fail', 'error': 'Error al guardar imagen nueva'}, status=500)

            elif foto_actual_base64:
                print(f"DEBUG: Recibida imagen actual en base64")
                try:
                    header, image_data = foto_actual_base64.split(',', 1)
                    imagen_nombre = "imagen_actual.jpg"
                    imagen_path = os.path.join('imagenes', imagen_nombre)
                    full_imagen_path = os.path.join(settings.MEDIA_ROOT, imagen_path)

                    os.makedirs(os.path.dirname(full_imagen_path), exist_ok=True)

                    with open(full_imagen_path, 'wb') as destination:
                        destination.write(base64.b64decode(image_data))
                    print("DEBUG: Imagen base64 guardada correctamente")
                except Exception as e:
                    print(f"ERROR al guardar la imagen base64: {str(e)}")
                    return JsonResponse({'status': 'fail', 'error': 'Error al procesar imagen base64'}, status=500)

            else:
                imagen_path = imagen_actual_db[0] if imagen_actual_db else None
                print(f"DEBUG: Usando la imagen actual de la base de datos: {imagen_path}")

            # Llamar al procedimiento almacenado
            try:
                print(f"DEBUG: Llamando al procedimiento almacenado con parámetros")
                with connections['universal'].cursor() as cursor:
                    cursor.callproc('TH_UPDATE_TH_EMPLEADOS', [
                        id_empleado, identidad, nombre_completo, rtn, telefono, correo, direccion, distancia_km, tipo_vehiculo_privada,
                        placa_vehiculo_privada, nacionalidad, id_sexo, pasaporte, fecha_nacimiento, 
                        pais_nacimiento, imagen_path, id_banco, cuenta_bancaria, id_nivel_certificado, 
                        campo_estudio, estado, modificado_por, estado_civil, numero_hijos, apellido_completo, 
                        id_municipio, nombre_ciudad, profesion, id_residencia, id_departamento, 
                        id_barrio, id_tipo_sangre, id_rol_empleado, punto_referencia
                    ])
                print('Datos actualizados correctamente')
                return JsonResponse({'status': 'success'})
            except Exception as e:
                print(f"ERROR al ejecutar el procedimiento almacenado: {str(e)}")
                return JsonResponse({'status': 'fail', 'error': 'Error en el procedimiento almacenado'}, status=500)

        except Exception as e:
            print(f"ERROR general: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    print('Método de solicitud no permitido')
    return JsonResponse({'status': 'fail', 'error': 'Invalid request method'}, status=400)

@csrf_exempt
def insertar_ficha_empleado(request):
    if request.method == 'POST':
        try:
            # Obtener todos los parámetros del formulario
            id_empleado = request.POST.get('id_empleado', 0)
            id_sucursal = request.POST.get('sucursal', 0)
            id_departamento = request.POST.get('departamento-empresa', 0)
            id_area = request.POST.get('areas-empresa', 0)
            id_cargo = request.POST.get('cargos-empresa', 0)
            id_posicion = request.POST.get('puesto-empresa', 0)
            id_gerente = request.POST.get('gerente', 0)
            id_jefe_inmediato = request.POST.get('jefe_inmediato', 0)
            direccion_laboral = request.POST.get('direccion_laboral', '')
            correo_empresarial = request.POST.get('email_trabajo', '')
            telefono_empresarial = request.POST.get('telefono_empresa', '')
            tipo_cuenta = request.POST.get('tipo_cuenta', 0)
            id_centro_costo = request.POST.get('centro_costo', 0)
            id_cuenta_contable = request.POST.get('cuenta_contable', 0)
            id_tipo_contrato = request.POST.get('tipo_contrato', 0)
            fecha_ingreso = request.POST.get('fecha_ingreso', '0000-00-00')
            id_categoria_retiro = request.POST.get('categoria_retiro', 0)
            id_motivo_retiro = request.POST.get('cat_motivos', 0)
            observaciones_retiro = request.POST.get('observaciones_retiro', '')
            fecha_retiro = request.POST.get('fecha_retiro', '0000-00-00')
            salario = request.POST.get('salario', 0.00)
            inicio_contrato = request.POST.get('inicio_contrato', '0000-00-00')
            fin_contrato = request.POST.get('fin_contrato', '0000-00-00')
            beneficios_laborales = request.POST.get('beneficios_laborales', '')
            id_forma_pago = request.POST.get('forma_pago', 0)
            beneficios_adicionales = request.POST.get('beneficios_adicionales', '')
            aplica_seguro = request.POST.get('aplica_seguro', 0)
            estado = request.POST.get('estado', 1)
            creado_por = request.POST.get('creado_por', 'system') 
            usuario_biometrico = request.POST.get('usuario_biometrico', 0) 

            # Verificar si ya existe una ficha para este id_empleado
            with connections['universal'].cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM th_empleados_fichas WHERE id_empleado = %s", [id_empleado])
                existing_ficha = cursor.fetchone()[0]

                if existing_ficha == 0:
                    # Si no existe, proceder a insertar la nueva ficha
                    cursor.callproc('TH_INSERT_TH_EMPLEADOS_FICHAS', [
                        id_empleado, id_sucursal, id_departamento, id_area, id_cargo, id_posicion, id_gerente, id_jefe_inmediato, direccion_laboral,
                        correo_empresarial, telefono_empresarial, tipo_cuenta, id_centro_costo, id_cuenta_contable, id_tipo_contrato, fecha_ingreso, id_categoria_retiro,
                        id_motivo_retiro, observaciones_retiro, fecha_retiro, salario, inicio_contrato, fin_contrato, beneficios_laborales, id_forma_pago,
                        beneficios_adicionales, aplica_seguro, estado, creado_por, usuario_biometrico
                    ])

            # Siempre devolver status success, sin importar si se insertó o ya existía
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail'}, status=400)

def obtener_info_empleado(request):
    if request.method == 'GET':
        search_term = request.GET.get('search', '')  # El término de búsqueda, puede ser nombre, identidad o rol
        offset = int(request.GET.get('offset', 0))  # Obtener el parámetro 'offset'
        limite = int(request.GET.get('limite', 50))  # Obtener el parámetro 'limite', por defecto es 20

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado con search_term, offset y limite
                cursor.callproc('TH_GET_EMPLEADO_INFO', [search_term, offset, limite])
                result = cursor.fetchall()

                if not result:
                    return JsonResponse({'status': 'success', 'data': []})

                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in result]

                return JsonResponse({'status': 'success', 'data': data})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail'}, status=400)

def empleados(request):
    return render(request, 'empleados.html')


@csrf_exempt
def obtener_empleados_info(request):
    if request.method == 'GET':
        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_EMPLEADOS_INFO_ALL')
                result = cursor.fetchall()
                
                # Si no hay resultados, devuelve una lista vacía pero con status success
                if not result:
                    return JsonResponse({'status': 'success', 'data': []})
                
                if cursor.description is None:
                    return JsonResponse({'status': 'fail', 'error': 'Cursor description is None'}, status=500)
                
                columns = [col[0] for col in cursor.description]
                data = []

                for row in result:
                    row_dict = {}
                    for idx, value in enumerate(row):
                        if isinstance(value, bytes):
                            value = value.decode('utf-8')
                        row_dict[columns[idx]] = value
                    data.append(row_dict)
                
                return JsonResponse({'status': 'success', 'data': data})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail'}, status=400)

def obtener_bitacora_empleados(request):
    if request.method == 'GET':
        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado para obtener la bitácora de empleados
                cursor.callproc('TH_GET_BITACORA_EMPLEADOS')
                result = cursor.fetchall()
                
                # Si no hay resultados, devolver una lista vacía con estado 200
                if not result:
                    return JsonResponse({'status': 'success', 'data': []}, status=200)
                
                # Verificar que el cursor tenga descripción de las columnas
                if cursor.description is None:
                    return JsonResponse({'status': 'fail', 'error': 'Descripción del cursor no disponible'}, status=500)
                
                # Obtener los nombres de las columnas
                columns = [col[0] for col in cursor.description]
                data = []

                # Iterar sobre las filas y convertir cada fila en un diccionario
                for row in result:
                    row_dict = {}
                    for idx, value in enumerate(row):
                        if isinstance(value, bytes):
                            value = value.decode('utf-8')  # Decodificar bytes a string si es necesario
                        row_dict[columns[idx]] = value
                    data.append(row_dict)
                
                # Devolver los datos en formato JSON
                return JsonResponse({'status': 'success', 'data': data}, status=200)
        
        except Exception as e:
            # Manejar excepciones y devolver el mensaje de error
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    # Si no es un método GET, devolver un error de solicitud no válida
    return JsonResponse({'status': 'fail', 'error': 'Método de solicitud no válido'}, status=400)

def obtener_datos_X_bitacora_empleado(request, id_empleado):
    if request.method == 'GET':
        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado para obtener la bitácora del empleado específico
                cursor.callproc('TH_GET_BITACORA_EMPLEADOS', [id_empleado])
                result = cursor.fetchall()
                
                # Si no hay resultados, devolver una lista vacía con status success
                if not result:
                    return JsonResponse({'status': 'success', 'data': []}, status=200)
                
                # Verificar que el cursor tenga descripción de las columnas
                if cursor.description is None:
                    return JsonResponse({'status': 'fail', 'error': 'Descripción del cursor no disponible'}, status=500)
                
                # Obtener los nombres de las columnas
                columns = [col[0] for col in cursor.description]
                data = []

                # Iterar sobre las filas y convertir cada fila en un diccionario
                for row in result:
                    row_dict = {}
                    for idx, value in enumerate(row):
                        if isinstance(value, bytes):
                            value = value.decode('utf-8')  # Decodificar bytes a string si es necesario
                        row_dict[columns[idx]] = value
                    data.append(row_dict)
                
                # Devolver los datos en formato JSON
                return JsonResponse({'status': 'success', 'data': data}, status=200)
        
        except Exception as e:
            # Manejar excepciones y devolver el mensaje de error
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    # Si no es un método GET, devolver un error de solicitud no válida
    return JsonResponse({'status': 'fail', 'error': 'Método de solicitud no válido'}, status=400)

@csrf_exempt
def obtener_datos_empleado(request, id_empleado):
    if request.method == 'GET':
        try:
            logger.debug(f"Inicio del procedimiento con id_empleado: {id_empleado}")
            
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_EMPLEADO_BY_ID', [id_empleado])
                result = cursor.fetchall()
                
                logger.debug(f"Resultados del procedimiento almacenado: {result}")
                
                columns = [col[0] for col in cursor.description]
                
                logger.debug(f"Columnas obtenidas: {columns}")
                
                # Convertir los datos a un formato JSON serializable
                data = [dict(zip(columns, row)) for row in result]
                
                logger.debug(f"Datos procesados: {data}")
                
                for item in data:
                    for key, value in item.items():
                        if key == 'imagen' and value:
                            image_path = os.path.join(settings.MEDIA_ROOT, value)
                            logger.debug(f"Ruta de la imagen: {image_path}")
                            
                            if os.path.exists(image_path):
                                with open(image_path, "rb") as image_file:
                                    item[key] = base64.b64encode(image_file.read()).decode('utf-8')
                            else:
                                logger.warning(f"Imagen no encontrada en la ruta: {image_path}")
                                item[key] = None
                        elif isinstance(value, bytes):
                            item[key] = base64.b64encode(value).decode('utf-8')
                
                if data:
                    logger.debug("Datos enviados en la respuesta: {data[0]}")
                    return JsonResponse({'status': 'success', 'data': data[0]})
                else:
                    logger.warning("No se encontraron datos para el id_empleado proporcionado")
                    return JsonResponse({'status': 'fail', 'error': 'Datos no encontrados'}, status=404)
        
        except Exception as e:
            logger.error(f"Error durante la obtención de datos del empleado: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    
    logger.warning("Método HTTP no soportado para esta solicitud")
    return JsonResponse({'status': 'fail'}, status=400)



def obtener_empleado_enfermedades_base(request):
    if request.method == 'GET':
        # Obtener el parámetro p_id_empleado desde la URL o como parámetro GET
        p_id_empleado = request.GET.get('id_empleado')

        if not p_id_empleado:
            return JsonResponse({'status': 'fail', 'error': 'Falta el parámetro id_empleado'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado
                cursor.callproc('TH_GET_EMPLEADO_ENFERMEDADES_BASE', [p_id_empleado])
                resultados = cursor.fetchall()

                # Procesar los resultados en un formato de diccionario para retornar como JSON
                enfermedades_empleado = []
                for row in resultados:
                    enfermedades_empleado.append({
                        'id_enfermedad': row[0],
                        'id_empleado': row[1],
                        'id_enfermedad_catalogo': row[2],
                        'nombre_enfermedad': row[3],  # Nuevo campo
                        'descripcion_enfermedad': row[4],  # Nuevo campo
                        'estado': row[5],
                        'creado_por': row[6],
                        'fecha_hora_creado': row[7],
                        'modificado_por': row[8],
                        'fecha_hora_modficacion': row[9]
                    })

            return JsonResponse({'status': 'success', 'data': enfermedades_empleado})
        
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def insertar_empleado_enfermedades_base(request):
    if request.method == 'POST':
        # Obtener los parámetros desde la solicitud POST
        p_id_empleado = request.POST.get('id_empleado')
        p_id_enfermedad_catalogo = request.POST.get('enfermedad_base')
        p_creado_por = request.POST.get('creado_por')

        # Verificar que todos los parámetros necesarios están presentes
        if not p_id_empleado or not p_id_enfermedad_catalogo or not p_creado_por:
            return JsonResponse({'status': 'fail', 'error': 'Faltan parámetros obligatorios'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado para insertar la enfermedad del empleado
                cursor.callproc('TH_INSERT_EMPLEADO_ENFERMEDADES_BASE', [
                    p_id_empleado,
                    p_id_enfermedad_catalogo,
                    p_creado_por
                ])

            return JsonResponse({'status': 'success', 'message': 'Enfermedad del empleado insertada correctamente'})

        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def crear_profesion_oficio(request):
    if request.method == 'POST':
        nombre_profesion_oficio = request.POST.get('nombre_profesion_oficio')
        descripcion = request.POST.get('descripcion', '')  # Descripción es opcional
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado para insertar la profesión u oficio
                cursor.callproc('TH_INSERT_CAT_PROFESIONES_OFICIOS', [
                    nombre_profesion_oficio,
                    descripcion,
                    creado_por
                ])
                # Obtener el ID del último registro insertado
                resultado = cursor.fetchone()
                nuevo_profesion_id = resultado[0] if resultado else None

            if nuevo_profesion_id:
                return JsonResponse({'status': 'success', 'id': nuevo_profesion_id})
            else:
                return JsonResponse({'status': 'fail', 'message': 'No se pudo obtener el ID de la profesión u oficio.'})
                
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)




def crear_centro_educativo(request):
    if request.method == 'POST':
        nombre_centro = request.POST.get('nombre_centro')
        direccion = request.POST.get('direccion', '')  # Dirección es opcional
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado para insertar el centro educativo
                cursor.callproc('TH_INSERT_CAT_CENTROS_EDUCATIVOS', [
                    nombre_centro,
                    direccion,
                    creado_por
                ])
                # Obtener el ID del último centro educativo insertado
                resultado = cursor.fetchone()
                nuevo_centro_id = resultado[0] if resultado else None

            if nuevo_centro_id:
                return JsonResponse({'status': 'success', 'id': nuevo_centro_id})
            else:
                return JsonResponse({'status': 'fail', 'message': 'No se pudo obtener el ID del centro educativo.'})
                
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


@csrf_exempt
def crear_habilidad(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            habilidad = data.get('nueva-habilidad-input')
            descripcion = data.get('descripcion-habilidad-input')
            creado_por = data.get('creado_por')

            if not habilidad or not descripcion or not creado_por:
                return JsonResponse({'status': 'fail', 'error': 'Todos los campos son obligatorios'}, status=400)

            # Llamar al procedimiento almacenado con el nuevo orden de parámetros
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_TH_CAT_HABILIDADES', [habilidad, descripcion, creado_por])
                result = cursor.fetchone()
                id_habilidad = result[0] if result else None

            if not id_habilidad:
                raise Exception("No se pudo obtener el ID de la habilidad insertada.")

            nueva_habilidad = {
                'id_habilidad': id_habilidad,
                'habilidad': habilidad,
                'descripcion': descripcion,
                'creado_por': creado_por
            }

            return JsonResponse({'status': 'success', 'habilidad': nueva_habilidad})
        except Exception as e:
            logger.error("Error al insertar habilidad: %s", str(e))
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def crear_Equipo(request):
    if request.method == 'POST':
        id_empleado = request.POST.get('id_empleado')
        nombre_equipo = request.POST.get('nombre_equipo')
        creado_por = request.POST.get('creado_por')


        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_EQUIPO_ASIGNADO', [id_empleado, nombre_equipo, creado_por])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def crear_cat_equipo(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre_equipo = request.POST.get('nombre_equipo_asignado')
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado para insertar el equipo
                cursor.callproc('TH_INSERT_CAT_EQUIPO_ASIGNADO', [
                    nombre_equipo,
                    creado_por
                ])
                # Obtener el ID del equipo recién creado
                resultado = cursor.fetchone()
                nuevo_equipo_id = resultado[0] if resultado else None

            return JsonResponse({'status': 'success', 'id': nuevo_equipo_id})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def crear_pais(request):
    if request.method == 'POST':
        pais = request.POST.get('nombre_pais')
        creado_por = request.POST.get('creado_por')
        nacionalidad = request.POST.get('nacionalidad')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamamos al procedimiento almacenado y capturamos el último id insertado
                cursor.callproc('CAT_INSERT_PAIS', [pais, nacionalidad, creado_por, creado_por])
                last_id = cursor.fetchone()[0]  # Captura el resultado de SELECT LAST_INSERT_ID()
            
            return JsonResponse({'status': 'success', 'last_id': last_id})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def crear_departamento_pais(request):
    if request.method == 'POST':
        id_pais = request.POST.get('id_pais')
        nombre_departamento = request.POST.get('nombre_departamento')
        ingresado_por = request.POST.get('ingresado_por')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamamos al procedimiento almacenado y capturamos el último id insertado
                cursor.callproc('CAT_INSERT_DEPARTAMENTO', [id_pais, nombre_departamento, ingresado_por, ingresado_por])
                last_id = cursor.fetchone()[0]  # Captura el resultado de SELECT LAST_INSERT_ID()
            
            return JsonResponse({'status': 'success', 'last_id': last_id})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def crear_municipio(request):
    if request.method == 'POST':
        id_departamento = request.POST.get('id_departamento')
        nombre_municipio = request.POST.get('nombre_municipio')
        ingresado_por = request.POST.get('ingresado_por')
        modificado_por = request.POST.get('modificado_por')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamamos al procedimiento almacenado y capturamos el último id insertado
                cursor.callproc('CAT_INSERT_MUNICIPIOS', [
                    id_departamento,
                    nombre_municipio,
                    ingresado_por,
                    modificado_por
                ])
                last_id = cursor.fetchone()[0]  # Captura el resultado de SELECT LAST_INSERT_ID()
            
            return JsonResponse({'status': 'success', 'last_id': last_id})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def crear_barrio_colonia(request):
    if request.method == 'POST':
        id_ciudad = request.POST.get('id_ciudad')
        nombre_barrio = request.POST.get('nombre_barrio')
        ingresado_por = request.POST.get('ingresado_por')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamamos al procedimiento almacenado y capturamos el último id insertado
                cursor.callproc('CAT_INSERT_BARRIOS_COLONIAS_MUNICIPIOS', [
                    id_ciudad,
                    nombre_barrio,
                    ingresado_por
                ])
                last_id = cursor.fetchone()[0]  # Captura el resultado de SELECT LAST_INSERT_ID()
            
            return JsonResponse({'status': 'success', 'last_id': last_id})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def crear_ciudad(request):
    if request.method == 'POST':
        id_municipio = request.POST.get('id_municipio')
        nombre_ciudad = request.POST.get('nombre_ciudad')
        ingresado_por = request.POST.get('ingresado_por')
        modificado_por = request.POST.get('modificado_por')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('CAT_INSERT_CIUDADES', [
                    id_municipio,
                    nombre_ciudad,
                    ingresado_por,
                    modificado_por
                ])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def obtener_departamentos_por_pais(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            id_pais = data.get('id_pais')
        except json.JSONDecodeError:
            id_pais = request.POST.get('id_pais')

        if not id_pais:
            return JsonResponse({'status': 'fail', 'error': 'El parámetro id_pais es requerido'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('obtener_departamentos_por_pais', [id_pais])
                departamentos = cursor.fetchall()

                departamentos_pais = [
                    {
                        'id_pais': depto[0],
                        'id_departamento': depto[1],
                        'nombre_departamento': depto[2],
                        'ingresado_por': depto[3],
                        'fecha_ingreso': depto[4],
                        'modificacion': depto[5],
                        'modificado_por': depto[6],
                        'fecha_modificacion': depto[7]
                    } for depto in departamentos
                ]

            return JsonResponse({'status': 'success', 'departamentos': departamentos_pais})
        except Exception as e:
            logger.error(f'Error retrieving departamentos: {e}', exc_info=True)
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def obtener_nacionalidades_por_pais(request):
    pais_id = request.GET.get('pais_id')
    
    try:
        with connections['universal'].cursor() as cursor:
            cursor.callproc('CAT_GET_NACIONALIDADES_BY_PAIS', [pais_id])
            nacionalidades = cursor.fetchall()
            
            nacionalidades_list = [
                {'id': nacionalidad[0], 'nombre': nacionalidad[1]} 
                for nacionalidad in nacionalidades
            ]
        
        return JsonResponse({'nacionalidades': nacionalidades_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def obtener_municipios_por_departamento(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            id_departamento = data.get('id_departamento')
        except json.JSONDecodeError:
            id_departamento = request.POST.get('id_departamento')

        if not id_departamento:
            return JsonResponse({'status': 'fail', 'error': 'El parámetro id_departamento es requerido'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('CAT_GET_MUNICIPIOS_BY_DEPARTAMENTO', [id_departamento])
                municipios = cursor.fetchall()

                municipios_departamento = [
                    {
                        'id_departamento': municipio[0],
                        'id_municipio': municipio[1],
                        'nombre_municipio': municipio[2],
                        'ingresado_por': municipio[3],
                        'fecha_ingreso': municipio[4],
                        'modificacion': municipio[5],
                        'modificado_por': municipio[6],
                        'fecha_modificacion': municipio[7]
                    } for municipio in municipios
                ]

            return JsonResponse({'status': 'success', 'municipios': municipios_departamento})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def obtener_ciudades_por_municipio(request):
    municipio_id = request.GET.get('municipio_id')
    
    try:
        with connections['universal'].cursor() as cursor:
            cursor.callproc('CAT_GET_CIUDADES_MUNICIPIOS', [municipio_id])
            ciudades = cursor.fetchall()
            
            ciudades_list = [
                {
                    'id_ciudad': ciudad[0], 
                    'nombre_ciudad': ciudad[1]
                } 
                for ciudad in ciudades
            ]
        
        return JsonResponse({'ciudades': ciudades_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def obtener_barrios_por_ciudad(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            id_municipio = data.get('id_municipio')
        except json.JSONDecodeError:
            id_municipio = request.POST.get('id_municipio')

        if not id_municipio:
            return JsonResponse({'status': 'fail', 'error': 'El parámetro id_municipio es requerido'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('CAT_GET_BARRIOS_BY_MUNICIPIO', [id_municipio])
                barrios = cursor.fetchall()

                barrios_municipio = [
                    {
                        'id_barrio_colonia': barrio[0],
                        'id_municipio': barrio[1],
                        'nombre_barrio': barrio[2],
                        'ingresado_por': barrio[3],
                        'fecha_ingreso': barrio[4],
                        'modificacion': barrio[5],
                        'modificado_por': barrio[6],
                        'fecha_modificacion': barrio[7]
                    } for barrio in barrios
                ]

            return JsonResponse({'status': 'success', 'barrios': barrios_municipio})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def insertar_contacto_emergencia(request):
    if request.method == 'POST':
        # Obtener datos del formulario
        id_empleado = request.POST.get('id_empleado')
        nombre_contacto = request.POST.get('nombre_contacto')
        telefono_contacto = request.POST.get('telefono_contacto')
        parentesco = request.POST.get('nuevo_parentesco_contacto')
        creado_por = request.user.username  # Usando el nombre de usuario actual

        # Verificar que todos los datos estén presentes
        if not all([id_empleado, nombre_contacto, telefono_contacto, parentesco, creado_por]):
            error_msg = "Faltan datos en la solicitud"
            logger.error(error_msg)
            return JsonResponse({'status': 'fail', 'error': error_msg}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_CONTACTOS_EMERGENCIAS', [
                    id_empleado, 
                    nombre_contacto, 
                    telefono_contacto, 
                    int(parentesco),  # Asegurarse de que el parentesco sea un número entero
                    creado_por
                ])
            return JsonResponse({'status': 'success'})
        except OperationalError as e:
            error_msg = f"Error en la base de datos: {str(e)}"
            logger.error(error_msg)
            return JsonResponse({'status': 'fail', 'error': error_msg}, status=500)
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(error_msg)
            return JsonResponse({'status': 'fail', 'error': error_msg}, status=500)
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def insertar_empleados_empresa(request):
    if request.method == 'POST':
        id_empleado = request.POST.get('id_empleado')
        id_empresa = request.POST.get('centro')
        creado_por = request.POST.get('creado_por')

        if not all([id_empleado, id_empresa, creado_por]):
            return JsonResponse({'status': 'fail', 'error': 'Faltan datos en la solicitud'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_EMPRESA', [
                    id_empleado, id_empresa, creado_por
                ])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def insertar_empleados_sucursal(request):
    if request.method == 'POST':
        # Agregamos logs para depurar
        print("Datos recibidos en la vista:")
        print(f"id_empleado: {request.POST.get('id_empleado')}")
        print(f"id_sucursal: {request.POST.get('sucursal')}")
        print(f"creado_por: {request.POST.get('creado_por')}")

        id_empleado = request.POST.get('id_empleado')
        id_sucursal = request.POST.get('sucursal')
        creado_por = request.POST.get('creado_por')

        if not all([id_empleado, id_sucursal, creado_por]):
            print("Error: Faltan datos en la solicitud")
            return JsonResponse({'status': 'fail', 'error': 'Faltan datos en la solicitud'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                print("Llamando al procedimiento almacenado")
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_SUCURSAL', [
                    id_empleado, id_sucursal, creado_por
                ])
            print("Procedimiento almacenado ejecutado correctamente")
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error en el procedimiento almacenado: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    print("Método no permitido")
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def insertar_empleados_departamentos(request):
    if request.method == 'POST':
        # Agregamos logs para depurar
        print("Datos recibidos en la vista:")
        print(f"id_empleado: {request.POST.get('id_empleado')}")
        print(f"id_departamento: {request.POST.get('departamento_empresa')}")
        print(f"creado_por: {request.POST.get('creado_por')}")

        id_empleado = request.POST.get('id_empleado')
        id_departamento = request.POST.get('id_departamento')
        creado_por = request.POST.get('creado_por')

        if not all([id_empleado, id_departamento, creado_por]):
            print("Error: Faltan datos en la solicitud")
            return JsonResponse({'status': 'fail', 'error': 'Faltan datos en la solicitud'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                print("Llamando al procedimiento almacenado")
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_DEPARTAMENTOS', [
                    id_empleado, id_departamento, creado_por
                ])
            print("Procedimiento almacenado ejecutado correctamente")
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error en el procedimiento almacenado: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    print("Método no permitido")
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def insertar_empleados_area(request):
    if request.method == 'POST':
        # Agregar logs para depuración
        print("Datos recibidos en la vista:")
        print(f"id_empleado: {request.POST.get('id_empleado')}")
        print(f"id_area: {request.POST.get('id_area')}")  # Debes recibir 'id_area' correctamente aquí
        print(f"creado_por: {request.POST.get('creado_por')}")

        id_empleado = request.POST.get('id_empleado')
        id_area = request.POST.get('id_area')  # Asegúrate de que este nombre sea el mismo
        creado_por = request.POST.get('creado_por')

        if not all([id_empleado, id_area, creado_por]):
            print("Error: Faltan datos en la solicitud")
            return JsonResponse({'status': 'fail', 'error': 'Faltan datos en la solicitud'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                print("Llamando al procedimiento almacenado: TH_INSERT_TH_EMPLEADOS_AREA")
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_AREA', [
                    id_empleado, id_area, creado_por
                ])
            print("Procedimiento almacenado ejecutado correctamente")
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error en el procedimiento almacenado: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    print("Método no permitido")
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def insertar_empleados_cargo(request):
    if request.method == 'POST':
        # Agregar logs para depuración
        print("Datos recibidos en la vista:")
        print(f"id_empleado: {request.POST.get('id_empleado')}")
        print(f"id_cargo: {request.POST.get('id_cargo')}")
        print(f"creado_por: {request.user.username}")

        id_empleado = request.POST.get('id_empleado')
        id_cargo = request.POST.get('id_cargo')
        creado_por = request.POST.get('creado_por') # Se obtiene de la sesión del usuario

        if not all([id_empleado, id_cargo, creado_por]):
            print("Error: Faltan datos en la solicitud")
            return JsonResponse({'status': 'fail', 'error': 'Faltan datos en la solicitud'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                print("Llamando al procedimiento almacenado: TH_INSERT_TH_EMPLEADOS_CARGO")
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_CARGO', [
                    id_empleado, id_cargo, creado_por
                ])
            print("Procedimiento almacenado ejecutado correctamente")
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error en el procedimiento almacenado: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    print("Método no permitido")
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def insertar_empleados_rol(request):
    if request.method == 'POST':
        id_empleado = request.POST.get('id_empleado')
        id_rol = request.POST.get('id_rol')
        creado_por = request.user.username

        if not all([id_empleado, id_rol, creado_por]):
            return JsonResponse({'status': 'fail', 'error': 'Faltan datos en la solicitud'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_ROL', [
                    id_empleado, id_rol, creado_por
                ])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def obtener_empleados_empresa(request):
    if request.method == 'GET':
        id_empleado = request.GET.get('id_empleado')

        if not id_empleado:
            return JsonResponse({'status': 'fail', 'error': 'Falta el id del empleado'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado
                cursor.callproc('TH_GET_HISTORIAL_EMPRESAS', [id_empleado])
                
                # Obtener los resultados
                resultados = cursor.fetchall()

                historial = []
                for row in resultados:
                    registro_historial = {
                        'id_empleado': row[0],
                        'id_empresa': row[1],
                        'NombreEmpresa': row[2],  # Nombre de la empresa
                        'modificado_por': row[3],
                        'fecha_hora_modificacion': row[4]
                    }
                    historial.append(registro_historial)

            return JsonResponse({'status': 'success', 'historial': historial})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def obtener_empleados_sucursal(request):
    if request.method == 'GET':
        id_empleado = request.GET.get('id_empleado')

        if not id_empleado:
            return JsonResponse({'status': 'fail', 'error': 'Falta el id del empleado'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado que incluye la unión con la tabla sucursales
                cursor.callproc('TH_GET_TH_EMPLEADOS_SUCURSAL', [id_empleado])
                resultados = cursor.fetchall()

                sucursales = []
                for row in resultados:
                    sucursal = {
                        'id_sucursal_empleados': row[0],
                        'id_empleado': row[1],
                        'nombre_sucursal': row[2],  # nombre_sucursal devuelto desde el procedimiento
                        'direccion': row[3],  # Ahora obtenemos la dirección
                        'estado': row[4],
                        'creado_por': row[5],
                        'fecha_hora_creado': row[6],
                        'modificado_por': row[7],
                        'fecha_hora_modificacion': row[8]
                    }
                    sucursales.append(sucursal)

            return JsonResponse({'status': 'success', 'sucursales': sucursales})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)


    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)
def obtener_empleados_departamento(request):
    if request.method == 'GET':
        id_empleado = request.GET.get('id_empleado')

        if not id_empleado:
            return JsonResponse({'status': 'fail', 'error': 'Falta el id del empleado'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_TH_EMPLEADOS_DEPARTAMENTOS', [id_empleado])
                resultados = cursor.fetchall()

                departamentos = []
                for row in resultados:
                    departamento = {
                        'id_departamentos_empleados': row[0],
                        'id_empleado': row[1],
                        'id_departamento': row[2],
                        'nombre_departamento': row[3],  # Nombre del departamento desde el JOIN
                        'estado': row[4],
                        'creado_por': row[5],
                        'fecha_hora_creado': row[6],
                        'modificado_por': row[7],
                        'fecha_hora_modificacion': row[8]
                    }
                    departamentos.append(departamento)

            return JsonResponse({'status': 'success', 'departamentos': departamentos})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def obtener_empleados_area(request):
    if request.method == 'GET':
        id_empleado = request.GET.get('id_empleado')

        if not id_empleado:
            return JsonResponse({'status': 'fail', 'error': 'Falta el id del empleado'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_TH_EMPLEADOS_AREA', [id_empleado])
                resultados = cursor.fetchall()

                areas = []
                for row in resultados:
                    area = {
                        'id_area_empleados': row[0],
                        'id_empleado': row[1],
                        'id_area': row[2],
                        'sub_grupo': row[3],  # Usar "sub_grupo" aquí también
                        'estado': row[4],
                        'creado_por': row[5],
                        'fecha_hora_creado': row[6],
                        'modificado_por': row[7],
                        'fecha_hora_modificacion': row[8]
                    }
                    areas.append(area)

            return JsonResponse({'status': 'success', 'areas': areas})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def obtener_empleados_cargo(request):
    if request.method == 'GET':
        id_empleado = request.GET.get('id_empleado')

        if not id_empleado:
            return JsonResponse({'status': 'fail', 'error': 'Falta el id del empleado'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_TH_EMPLEADOS_CARGO', [id_empleado])
                resultados = cursor.fetchall()

                cargos = []
                for row in resultados:
                    cargo = {
                        'id_cargo_empleados': row[0],
                        'id_empleado': row[1],
                        'id_cargo': row[2],
                        'nombre_cargo': row[3],  # Se añade el nombre del cargo
                        'grado_cargo': row[4],   # Se añade el grado del cargo
                        'estado': row[5],
                        'creado_por': row[6],
                        'fecha_hora_creado': row[7],
                        'modificado_por': row[8],
                        'fecha_hora_modificacion': row[9]
                    }
                    cargos.append(cargo)

            return JsonResponse({'status': 'success', 'cargos': cargos})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def obtener_empleados_rol(request):
    if request.method == 'GET':
        id_empleado = request.GET.get('id_empleado')

        if not id_empleado:
            return JsonResponse({'status': 'fail', 'error': 'Falta el id del empleado'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_TH_EMPLEADOS_ROL', [id_empleado])
                resultados = cursor.fetchall()

                roles = []
                for row in resultados:
                    rol = {
                        'id_rol_empleados': row[0],
                        'id_empleado': row[1],
                        'id_rol': row[2],
                        'estado': row[3],
                        'creado_por': row[4],
                        'fecha_hora_creado': row[5],
                        'modificado_por': row[6],
                        'fecha_hora_modificacion': row[7]
                    }
                    roles.append(rol)

            return JsonResponse({'status': 'success', 'roles': roles})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)




def desactivar_familiar(request):
    try:

        id_familiar = request.POST.get('id_familiar')
        modificado_por = request.session.get('userName', '')

        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_DELETE_EMPLEADOS_FAMILIARES', [id_familiar, modificado_por])

        datos = {'save': 1, 'message': 'Familiar desactivado exitosamente.'}
    except Exception as e:

        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)


def insertar_contacto_familiar(request):
    if request.method == 'POST':
        # Obtener datos del frontend
        id_familiar = request.POST.get('id_familiar')  
        id_empleado = request.POST.get('id_empleado')
        nombre_familiar = request.POST.get('nombre_familiar')
        telefono_familiar = request.POST.get('telefono_familiar')
        parentesco = request.POST.get('parentesco')
        lugar_residencia = request.POST.get('lugar_residencia')
        opcion = request.POST.get('opcion') 

        # Obtener el nombre del usuario desde la sesión
        creado_por = request.session.get('userName', '')

        try:
            # Conexión a la base de datos
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_FAMILIARES', [
                    id_familiar,  # ID del familiar (NULL para inserciones)
                    id_empleado,
                    nombre_familiar,
                    telefono_familiar,
                    parentesco,
                    lugar_residencia,
                    creado_por,
                    opcion
                ])

                # Obtener el estado de la operación
                result = cursor.fetchone()
                existe = result[0] if result else 0  # 0: Sin duplicados, 1: Duplicado

            # Respuesta en caso de éxito
            if existe == 0:
                return JsonResponse({'status': 'success', 'message': 'Operación exitosa'})
            else:
                return JsonResponse({'status': 'fail', 'message': 'Registro duplicado'})

        except Exception as e:
            # Manejo de errores
            return JsonResponse({'status': 'fail', 'error': str(e)})

    # Respuesta para métodos no permitidos
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def actualizar_contacto_familiar(request):
    if request.method == 'POST':
        # Obtener los datos enviados en la solicitud POST
        id_familiar = request.POST.get('id_familiar')
        id_empleado = request.POST.get('id_empleado')
        nombre_familiar = request.POST.get('nombre_familiar')
        telefono_familiar = request.POST.get('telefono_familiar')
        id_parentesco = request.POST.get('parentesco')
        modificado_por = request.POST.get('modificado_por')
        lugar_residencia = request.POST.get('lugar_residencia')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado para actualizar el registro
                cursor.callproc('TH_UPDATE_TH_EMPLEADOS_FAMILIARES', [
                    id_familiar,
                    id_empleado,
                    nombre_familiar,
                    telefono_familiar,
                    id_parentesco,
                    modificado_por,
                    lugar_residencia
                ])

            return JsonResponse({'status': 'success'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'message': 'Método no permitido'}, status=405)


def insertar_seguros(request):
    if request.method == 'POST':
        id_seguro = request.POST.get('id_seguro')  # Para actualización
        id_empleado = request.POST.get('id_empleado')
        nombre_seguro = request.POST.get('nombre_seguro')
        poliza = request.POST.get('poliza')
        valor_mensual = request.POST.get('valor_mensual')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin', None)  # Puede ser opcional
        modificado_por = request.POST.get('creado_por')  # Usuario que modifica

        try:
            with connections['universal'].cursor() as cursor:
                if id_seguro:  # Si existe `id_seguro`, actualizar
                    print(f"Actualizando seguro con id_seguro={id_seguro}")
                    cursor.callproc('TH_UPDATE_TH_EMPLEADOS_SEGUROS', [
                        id_seguro,
                        id_empleado,
                        nombre_seguro,
                        poliza,
                        valor_mensual,
                        fecha_inicio,
                        fecha_fin,
                        modificado_por  # Nota: Ya no se pasa `estado`
                    ])
                else:  # Si no existe `id_seguro`, insertar nuevo
                    print("Insertando nuevo seguro")
                    cursor.callproc('TH_INSERT_TH_EMPLEADOS_SEGUROS', [
                        id_empleado,
                        nombre_seguro,
                        poliza,
                        valor_mensual,
                        fecha_inicio,
                        fecha_fin,
                        modificado_por  # Nota: Ya no se pasa `estado`
                    ])
            print("Operación exitosa")
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error en la operación: {str(e)}")  # Imprimir error
            return JsonResponse({'status': 'fail', 'error': str(e)})
    else:
        print("Método no permitido")
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)



def insertar_beneficios_laborales(request):
    if request.method == 'POST':
        id_beneficio_laboral = request.POST.get('id_beneficio_laboral')  # Para actualización
        id_empleado = request.POST.get('id_empleado')
        valor_beneficio = request.POST.get('valor_beneficio')
        id_laboral = request.POST.get('id_laboral')
        modificado_por = request.POST.get('creado_por')  # Usuario que modifica o crea

        try:
            with connections['universal'].cursor() as cursor:
                if id_beneficio_laboral:  # Si existe `id_beneficio_laboral`, actualizar
                    print(f"Actualizando beneficio laboral con id_beneficio_laboral={id_beneficio_laboral}")
                    cursor.callproc('TH_UPDATE_EMPLEADOS_BENEFICIO_LABORAL', [
                        id_beneficio_laboral,
                        valor_beneficio,
                        id_laboral,
                        modificado_por
                    ])
                else:  # Si no existe `id_beneficio_laboral`, insertar nuevo
                    print("Insertando nuevo beneficio laboral")
                    cursor.callproc('TH_INSERTAR_EMPLEADOS_BENEFICIO_LABORAL', [
                        id_empleado,
                        valor_beneficio,
                        id_laboral,
                        modificado_por
                    ])
            print("Operación exitosa")
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error en la operación: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': str(e)})
    else:
        print("Método no permitido")
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def eliminar_beneficio_laboral(request):
    if request.method == 'POST':
        id_beneficio_laboral = request.POST.get('id_beneficio_laboral')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_DELETE_EMPLEADOS_BENEFICIO_LABORAL', [id_beneficio_laboral])
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error en la eliminación: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': str(e)})
    else:
        return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def insertar_beneficio_adicional(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        id_beneficio_adicional = request.POST.get('id_beneficio_adicionales')  # Para actualización
        id_empleado = request.POST.get('id_empleado')  # ID del empleado
        valor_beneficio = request.POST.get('valor_beneficio')
        id_beneficio = request.POST.get('id_beneficio')
        creado_por = request.POST.get('creado_por')  # Usuario que crea o modifica

        try:
            with connections['universal'].cursor() as cursor:
                # Si se recibe 'id_beneficio_adicional', se realiza la actualización
                if id_beneficio_adicional:
                    print(f"Actualizando beneficio adicional con ID: {id_beneficio_adicional}")
                    cursor.callproc('TH_UPDATE_EMPLEADOA_BENEFICIO_ADICIONAL', [
                        int(id_beneficio_adicional),
                        float(valor_beneficio),
                        int(id_beneficio),
                        creado_por
                    ])
                else:
                    # Si no existe 'id_beneficio_adicional', se realiza la inserción
                    print("Insertando nuevo beneficio adicional")
                    cursor.callproc('TH_INSERTAR_EMPLEADO_BENEFICIO_ADICIONAL', [
                        int(id_empleado),
                        float(valor_beneficio),
                        int(id_beneficio),
                        creado_por
                    ])

            # Si no hay errores, retornar éxito
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error en la operación: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': str(e)})
    else:
        print("Método no permitido")
        return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def eliminar_beneficio_adicional(request):
    if request.method == 'POST':
        id_beneficio_adicional = request.POST.get('id_beneficio_adicionales')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_DELETE_EMPLEADOA_BENEFICIO_ADICIONAL', [id_beneficio_adicional])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error en la eliminación: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': str(e)})
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


@csrf_exempt
def insertar_asociaciones_empleados(request):
    if request.method == 'POST':
        id_empleado = request.POST.get('id_empleado')
        descripcion_asociacion = request.POST.get('descripcion_asociacion')
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_ASOCIACIONES', [
                    id_empleado, 
                    descripcion_asociacion,  
                    creado_por
                ])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def insertar_asociacion(request):
    if request.method == 'POST':
        # Obtén los datos del formulario
        nombre_asociacion = request.POST.get('nombre_asociacion')
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado para insertar la asociación
                cursor.callproc('TH_INSERT_ASOCIACION', [
                    nombre_asociacion,
                    creado_por
                ])
                # Obtener el ID de la asociación recién creada
                resultado = cursor.fetchone()
                nueva_asociacion_id = resultado[0] if resultado else None

            return JsonResponse({'status': 'success', 'id': nueva_asociacion_id})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def insertar_empresa_seguros(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre_empresa = request.POST.get('empresa')
        descripcion_empresa = request.POST.get('descripcion')
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado
                cursor.callproc('TH_INSERT_EMPRESA_SEGURO', [nombre_empresa, descripcion_empresa, creado_por])
                
                # Obtener el ID de la empresa recién creada
                resultado = cursor.fetchone()
                nueva_empresa_id = resultado[0] if resultado else None

            return JsonResponse({'status': 'success', 'id': nueva_empresa_id, 'message': 'Empresa de seguro insertada exitosamente.'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Método no permitido.'})

    

@csrf_exempt
def insertar_contacto_emergencia(request):
    if request.method == 'POST':
        id_empleado = request.POST.get('id_empleado')
        nombre_contacto = request.POST.get('nombre_contacto')
        telefono_contacto = request.POST.get('telefono_contacto')
        parentesco = request.POST.get('parentesco_contacto')
        creado_por = request.POST.get('creado_por')

        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_INSERT_TH_EMPLEADOS_CONTACTOS_EMERGENCIAS', [
                id_empleado,
                nombre_contacto,
                telefono_contacto,
                parentesco,
                creado_por
            ])
        return JsonResponse({'success': True, 'message': 'Contacto de emergencia agregado exitosamente.'})
    else:
        return JsonResponse({'success': False, 'message': 'Método no permitido.'})


def insertar_parentesco(request):
    if request.method == 'POST':
      
        parentesco = request.POST.get('parentesco')
        creado_por = request.POST.get('creado_por')

        # Validación básica
        if not parentesco or not creado_por:
            return JsonResponse({'success': False, 'message': 'Todos los campos son obligatorios.'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado y obtener el ID del último parentesco insertado
                cursor.callproc('TH_INSERT_CAT_PARENTESCOS', [
                    parentesco,      
                    creado_por   
                ])
                # Obtener el ID del último parentesco insertado
                last_id = cursor.fetchone()[0]  # Obtenemos el valor retornado por el procedimiento

            return JsonResponse({
                'success': True, 
                'message': 'Parentesco agregado exitosamente.',
                'id_parentesco': last_id  # Devolver el ID del parentesco insertado
            })
        except Exception as e:
            logger.error(f'Error inserting parentesco: {e}', exc_info=True)
            return JsonResponse({'success': False, 'message': 'Ocurrió un error al insertar el parentesco.'}, status=500)
    else:
        return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)

def insertar_poliza_seguro(request):
    if request.method == 'POST':
        # Verificar los datos recibidos
        print("Datos recibidos:", request.POST)

        # Obtener los valores del POST
        poliza = request.POST.get('nombre_poliza_seguros')
        descripcion = request.POST.get('descripcion_poliza_seguros', '')  # Si no hay descripción, asignar una cadena vacía
        id_empresa_seguros = request.POST.get('id_empresa_seguros')
        creado_por = request.POST.get('creado_por')

        # Validación básica
        if not poliza or not id_empresa_seguros or not creado_por:
            print(f"Error: Campo faltante: poliza={poliza}, id_empresa_seguros={id_empresa_seguros}, creado_por={creado_por}")
            return JsonResponse({'success': False, 'message': 'Los campos póliza, empresa de seguros y creador son obligatorios.'}, status=400)

        try:
            # Llamar al procedimiento almacenado
            with connections['universal'].cursor() as cursor:
                print(f"Llamando a procedimiento con: poliza={poliza}, descripcion={descripcion}, id_empresa_seguros={id_empresa_seguros}, creado_por={creado_por}")
                cursor.callproc('TH_INSERT_POLIZA_SEGUROS', [
                    poliza,  
                    descripcion,  # Enviará una cadena vacía si la descripción no está presente  
                    id_empresa_seguros,     
                    creado_por   
                ])

                # Obtener el ID de la póliza recién creada
                resultado = cursor.fetchone()
                nueva_poliza_id = resultado[0] if resultado else None

            return JsonResponse({'success': True, 'message': 'Póliza de seguro agregada exitosamente.', 'id': nueva_poliza_id})

        except Exception as e:
            # Imprimir el traceback completo para ver detalles del error
            error_message = traceback.format_exc()
            print(f"Error al insertar la póliza de seguro: {error_message}")
            logger.error(f"Error al insertar la póliza de seguro: {e}", exc_info=True)
            return JsonResponse({'success': False, 'message': f"Ocurrió un error: {str(e)}"}, status=500)

    else:
        return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=405)



def crear_certificaciones(request):
    if request.method == 'POST':
        nivel_certificado = request.POST.get('nivel_certificado')
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado para insertar la certificación
                cursor.callproc('TH_INSERT_TH_CAT_NIVEL_CERTIFICADOS', [
                    nivel_certificado,
                    creado_por
                ])
                # Obtener el ID del nivel de certificación recién creado
                resultado = cursor.fetchone()
                nuevo_nivel_certificado_id = resultado[0] if resultado else None

            return JsonResponse({'status': 'success', 'id': nuevo_nivel_certificado_id})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


@csrf_exempt
def crear_contrato(request):
    if request.method == 'POST':
        nombre_tipo_contrato = request.POST.get('tipo_contrato')
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_TH_CAT_TIPO_CONTRATO', [nombre_tipo_contrato, creado_por])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def crear_categoria_retiro(request):
    if request.method == 'POST':
        categoria_retiro = request.POST.get('categoria_retiro')
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_CAT_CATEGORIAS_RETIRO', [categoria_retiro, creado_por])
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def crear_nuevo_beneficio_adicional(request):
    if request.method == 'POST':
        # Obtén los datos del formulario
        beneficio = request.POST.get('beneficio')
        descripcion = request.POST.get('descripcion')
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado para insertar el beneficio adicional
                cursor.callproc('TH_INSERT_BENEFICIO_ADICIONAL', [
                    beneficio,
                    descripcion,
                    creado_por
                ])
                # Obtener el ID del beneficio adicional recién creado
                resultado = cursor.fetchone()
                nuevo_beneficio_id = resultado[0] if resultado else None

            return JsonResponse({'status': 'success', 'id': nuevo_beneficio_id})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def crear_nuevo_tipo_curriculum(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        tipo_curriculum = request.POST.get('nuevo_tipo_curriculum')
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                # Llamar al procedimiento almacenado para insertar el tipo de currículum
                cursor.callproc('TH_INSERT_TH_CAT_TIPOS_CURRICULUM', [
                    tipo_curriculum,
                    creado_por
                ])
                # Obtener el ID del tipo de currículum recién creado
                resultado = cursor.fetchone()
                nuevo_tipo_curriculum_id = resultado[0] if resultado else None

            return JsonResponse({'status': 'success', 'id': nuevo_tipo_curriculum_id})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)



def crear_nuevo_beneficio_laboral(request):
    if request.method == 'POST':
        # Obtén los datos del formularioP
        beneficio_laboral = request.POST.get('beneficio_laboral')
        descripcion = request.POST.get('descripcion')
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_BENEFICIOS_LABORAL', [
                    beneficio_laboral,
                    descripcion,
                    creado_por
                ])
                # Obtén el ID del beneficio laboral recién creado
                resultado = cursor.fetchone()  # Asumiendo que el procedimiento devuelve un valor
                nuevo_beneficio_id = resultado[0] if resultado else None

            return JsonResponse({'status': 'success', 'id': nuevo_beneficio_id})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def crear_nuevo_banco(request):
    if request.method == 'POST':
        nombre_banco = request.POST.get('nombre_banco')
        try:
           
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_BANCO', [nombre_banco])
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def crear_motivo_retiro(request):
    if request.method == 'POST':
        categoria_motivo_retiro = request.POST.get('motivo_retiro')
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_TH_CAT_MOTIVOS_RETIRO', [categoria_motivo_retiro, creado_por])
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def crear_formas_pagos(request):
    if request.method == 'POST':
        formas_pago = request.POST.get('forma_de_pago')
        creado_por = request.POST.get('creado_por')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_CAT_FORMAS_DE_PAGO', [formas_pago, creado_por])
                
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)



@csrf_exempt
def crear_tipo_cuenta(request):
    if request.method == 'POST':
        nombre_tipo_cuenta = request.POST.get('tipo_cuenta')
        creado_por = request.POST.get('creado_por')
        try:
            with connections['universal'].cursor() as cursor:
                # Pasando 0 para p_id_cargo ya que es un campo autoincremental
                cursor.callproc('TH_INSERT_TIPO_CUENTA', [nombre_tipo_cuenta, creado_por])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})
    
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def crear_posicion(request):
    if request.method == 'POST':
        nombre_posicion = request.POST.get('nombre_posicion')
        creado_por = request.POST.get('creado_por')
        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERTAR_CAT_POSICION', [nombre_posicion, creado_por])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)})

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def crear_estado_empleado(request):
    if request.method == 'POST':
        estado_empleado = request.POST.get('estado_empleado')
        creado_por = request.POST.get('creado_por')
        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_TH_CAT_ESTADOS_EMPLEADOS', [estado_empleado, 1, creado_por])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f'Error creating estado empleado: {e}', exc_info=True)
            return JsonResponse({'status': 'fail', 'error': str(e)})

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


@csrf_exempt
def guardar_ficha_empleado(request):
    if request.method == 'POST':
        try:
            data = request.POST
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_UPDATE_TH_EMPLEADOS_FICHAS', [
                    data.get('id_empleado', 0),
                    data.get('gerente', 0),
                    data.get('jefe_inmediato', 0),
                	data.get('jefe_superior', 0),
                    data.get('direccion_laboral', ''),
                    data.get('email_trabajo', ''),
                    data.get('telefono_empresa', ''),
                    data.get('tipo_cuenta', 0),
                    data.get('centro_costo', 0),
                    data.get('cuenta_contable', ''),
                    data.get('tipo_contrato', 0),
                    data.get('fecha_ingreso', '0000-00-00'),
                    data.get('nuevo_categoria-retiros', 0),
                    data.get('nuevo_motivo-retiro', 0),
                    data.get('observaciones_retiro', ''),
                    data.get('fecha_retiro', '0000-00-00'),
                    data.get('salario'),
                    data.get('inicio_contrato', '0000-00-00'),
                    data.get('fin_contrato', '0000-00-00'),
                    data.get('forma_pago', 0),
                    data.get('aplica_seguro', 0),
                    data.get('estado', 1),
                    data.get('creado_por', ''),
                    data.get('observaciones_generales', ''),
                    data.get('usuario', 0),
                    data.get('departamento_empresa', 0),
                    data.get('id_area', 0),
                    data.get('id_cargo', 0),
                    data.get('centro', 0),
                    data.get('sucursal', 0),
                    data.get('usuario_biometrico', 0)
                ])
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    return JsonResponse({'status': 'fail'}, status=400)


@csrf_exempt
def guardar_usuario(request):
    if request.method == 'POST':
        try:
            # Obtener los datos del cuerpo de la solicitud
            data = json.loads(request.body)
            nombre = data.get('nombre')
            usuario = data.get('usuario')
            contrasena = data.get('contrasena')
            
            # Validar que los campos requeridos no estén vacíos
            if not all([nombre, usuario, contrasena]):
                return JsonResponse({'status': 'fail', 'error': 'Todos los campos son obligatorios'}, status=400)

            # Insertar en la base de datos local
            with connections['global_local'].cursor() as cursor_local:
                cursor_local.callproc('TH_INSERT_USUARIOS_GLOBAL', [nombre, usuario, contrasena])

            # Insertar en la base de datos en la nube
            with connections['global_nube'].cursor() as cursor_nube:
                cursor_nube.callproc('TH_INSERT_USUARIOS_GLOBAL', [nombre, usuario, contrasena])

            return JsonResponse({'status': 'success', 'message': 'Usuario creado exitosamente'})
        
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': f'Error inesperado: {str(e)}'}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def guardar_documentos(request):
    if request.method == 'POST':
        try:
            id_empleado = request.POST.get('id_empleado')
            if not id_empleado:
                return JsonResponse({'status': 'fail', 'error': 'id_empleado es requerido'}, status=400)

            archivos = request.FILES.getlist('documentos')
            documentos_guardados = []

            for archivo in archivos:
                # Guardar el archivo en el sistema de archivos
                directorio = os.path.join(settings.MEDIA_ROOT, 'documentos', archivo.name)
                with open(directorio, 'wb+') as destination:
                    for chunk in archivo.chunks():
                        destination.write(chunk)
                
                # Guardar la información del archivo en la base de datos
                with connections['universal'].cursor() as cursor:
                    cursor.callproc('TH_INSERT_TH_EMPLEADOS_DOCUMENTACION', [
                        id_empleado, os.path.join('documentos', archivo.name), 1, 'system'
                    ])
                
                documentos_guardados.append({
                    'nombre': archivo.name,
                    'ruta': os.path.join('documentos', archivo.name),
                })

            return JsonResponse({'status': 'success', 'documentos': documentos_guardados})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

def obtener_documentos_empleado(request):
    id_empleado = request.GET.get('id_empleado')
    if not id_empleado:
        return JsonResponse({'status': 'fail', 'error': 'ID de empleado no proporcionado'}, status=400)

    try:
        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_GET_TH_EMPLEADOS_DOCUMENTACION', [id_empleado])
            documentos = cursor.fetchall()

        documentos_data = [
            {'nombre': documento[1], 'ruta': documento[2]} for documento in documentos
        ]
        return JsonResponse({'status': 'success', 'documentos': documentos_data})

    except Exception as e:
        return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)



logger = logging.getLogger(__name__)

@csrf_exempt
def agregar_habilidad_empleado(request):
    if request.method == 'POST':
        try:
            id_empleado = request.POST.get('id_empleado')
            id_habilidad = request.POST.get('id_habilidad')
            creado_por = request.POST.get('creado_por')

            if not id_empleado or not id_habilidad or not creado_por:
                return JsonResponse({'status': 'fail', 'error': 'Todos los campos son obligatorios'}, status=400)

            logger.debug("ID Empleado: %s, ID Habilidad: %s, Creado por: %s", id_empleado, id_habilidad, creado_por)

            # Llamar al procedimiento almacenado
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_HABILIDADES', [
                    id_empleado,
                    id_habilidad,
                    creado_por
                ])

            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error("Error al agregar habilidad del empleado: %s", str(e))
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)

@csrf_exempt
def guardar_equipos_empleado(request):
    if request.method == 'POST':
        try:
            id_empleado = request.POST.get('id_empleado')
            equipos = json.loads(request.POST.get('equipos', '[]'))

            with connections['universal'].cursor() as cursor:
                for equipo in equipos:
                    cursor.callproc('TH_INSERT_TH_EMPLEADOS_EQUIPO_ASIGNADO', [
                        id_empleado,
                        equipo['nombre_equipo_asignado'],
                        1,  # Estado
                        'system'  # Creado por
                    ])

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'error': 'Invalid request method'}, status=400)

@csrf_exempt
def obtener_habilidades_empleado(request, id_empleado):
    if request.method == 'GET':
        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_UNIQUE_EMPLEADO_HABILIDADES_BY_ID', [id_empleado])
                result = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in result]
                
                if data:
                    return JsonResponse({'status': 'success', 'data': data})
                else:
                    return JsonResponse({'status': 'fail', 'error': 'No se encontraron habilidades para este empleado'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)
    
    return JsonResponse({'status': 'fail'}, status=400)

#tipo de curriculum 
logger = logging.getLogger(__name__)

@csrf_exempt
def crear_tipo_curriculum(request):
    logger.debug("Entrando en la vista crear_tipo_curriculum")

    if request.method == 'POST':
        logger.debug("Método de solicitud: POST")
        try:
            tipo_curriculum = request.POST.get('tipo_curriculum')
            creado_por = request.POST.get('creado_por')
            logger.debug(f"Datos recibidos - tipo_curriculum: {tipo_curriculum}, creado_por: {creado_por}")

            if not tipo_curriculum or not creado_por:
                logger.error("Todos los parámetros son requeridos")
                raise ValueError("Todos los parámetros son requeridos")

            with connections['universal'].cursor() as cursor:
                logger.debug("Llamando al procedimiento almacenado")
                cursor.callproc('TH_INSERT_TH_CAT_TIPOS_CURRICULUM', [
                    tipo_curriculum,
                    creado_por
                ])
                logger.debug("Procedimiento almacenado ejecutado correctamente")
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Error en la vista crear_tipo_curriculum: {e}")
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    logger.warning("Método de solicitud no válido")
    return JsonResponse({'status': 'fail', 'error': 'Invalid request method'}, status=400)


@csrf_exempt
def guardar_curriculum_empleado(request):
    logger.debug("Entrando en la vista guardar_curriculum_empleado")

    if request.method == 'POST':
        logger.debug("Método de solicitud: POST")
        try:
            # Obtener los datos del formulario
            empleado_id = request.POST.get('id_empleado')
            titulo = request.POST.get('titulo')
            tipo_curriculum = request.POST.get('tipo_curriculum')
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_final = request.POST.get('fecha_final', None)  # Si no está presente, asigna None
            descripcion = request.POST.get('descripcion', '')  # Si no está presente, asigna una cadena vacía
            creado_por = request.POST.get('creado_por')
            estado_curriculum = request.POST.get('estado_curriculum')

            logger.debug(f"Datos recibidos - empleado_id: {empleado_id}, titulo: {titulo}, tipo_curriculum: {tipo_curriculum}, fecha_inicio: {fecha_inicio}, fecha_final: {fecha_final}, descripcion: {descripcion}, creado_por: {creado_por}, estado_curriculum: {estado_curriculum}")

            # Validar campos requeridos
            if not (empleado_id and titulo and tipo_curriculum and fecha_inicio and creado_por and estado_curriculum):
                logger.error("Faltan parámetros requeridos")
                raise ValueError("Faltan parámetros requeridos")

            # Llamada al procedimiento almacenado
            with connections['universal'].cursor() as cursor:
                logger.debug("Llamando al procedimiento almacenado")
                cursor.callproc('TH_INSERT_TH_EMPLEADOS_CURRICULUM', [
                    empleado_id,
                    titulo,
                    tipo_curriculum,
                    fecha_inicio,
                    fecha_final,
                    descripcion,
                    creado_por,
                    estado_curriculum
                ])
                logger.debug("Procedimiento almacenado ejecutado correctamente")

            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.error(f"Error en la vista guardar_curriculum_empleado: {e}", exc_info=True)
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    logger.warning("Método de solicitud no válido")
    return JsonResponse({'status': 'fail', 'error': 'Invalid request method'}, status=400)

@csrf_exempt
def actualizar_curriculum_empleado(request):
    if request.method == 'POST':
        try:
            # Obtener los datos del formulario
            id_curriculum = request.POST.get('id_curriculum')
            id_empleado = request.POST.get('empleado_id')
            titulo = request.POST.get('titulo')
            tipo_curriculum = request.POST.get('tipo_curriculum')
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_final = request.POST.get('fecha_final')
            descripcion = request.POST.get('descripcion')
            modificado_por = request.POST.get('creado_por')  # Asumimos que el campo 'creado_por' se reutiliza para 'modificado_por'
            estado = 1  # Asumimos que el estado es activo (1)

            # Validar que todos los campos necesarios están presentes
            if not all([id_curriculum, id_empleado, titulo, tipo_curriculum, fecha_inicio, fecha_final, descripcion, modificado_por]):
                return JsonResponse({'status': 'fail', 'error': 'Todos los campos son obligatorios'}, status=400)

            # Llamar al procedimiento almacenado para actualizar el currículum
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_UPDATE_TH_EMPLEADOS_CURRICULUM', [
                    id_curriculum,
                    id_empleado,
                    titulo,
                    tipo_curriculum,
                    fecha_inicio,
                    fecha_final,
                    descripcion,
                    estado,
                    modificado_por
                ])

            # Si se ejecutó correctamente, devolver un mensaje de éxito
            return JsonResponse({'status': 'success', 'message': 'Currículum actualizado correctamente'})

        except Exception as e:
            # Manejo de excepciones y errores
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    # Si el método de solicitud no es POST, devolver un error
    return JsonResponse({'status': 'fail', 'error': 'Método de solicitud no permitido'}, status=405)

@csrf_exempt
def obtener_curriculums_por_empleado(request):
    id_empleado = request.GET.get('id_empleado')
    logger.debug("Entrando en la vista obtener_curriculums_por_empleado")

    if request.method == 'GET':
        try:
            logger.debug(f"Obteniendo curriculums para el empleado con id: {id_empleado}")

            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_CURRICULUM_BY_EMPLEADO_ID', [id_empleado])
                resultados = cursor.fetchall()
                curriculums = []

                for row in resultados:
                    curriculum = {
                        'id_curriculum': row[0],
                        'id_empleado': row[1],
                        'titulo': row[2],
                        'tipo_curriculum': row[3], 
                        'fecha_inicio': row[4],
                        'fecha_final': row[5],
                        'descripcion': row[6],
                    }
                    curriculums.append(curriculum)
                
                logger.debug("Curriculums obtenidos correctamente")

            return JsonResponse({'status': 'success', 'curriculums': curriculums})
        except Exception as e:
            logger.error(f"Error en la vista obtener_curriculums_por_empleado: {e}")
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    logger.warning("Método de solicitud no válido")
    return JsonResponse({'status': 'fail', 'error': 'Invalid request method'}, status=400)


def obtener_vacaciones(request):
    if request.method == 'GET':
        # Obtener la identidad desde los parámetros GET de la solicitud
        identidad = request.GET.get('identidad')

        # Verificar si se recibió una identidad válida
        if not identidad:
            return JsonResponse({'status': 'fail', 'error': 'Falta la identidad'}, status=400)

        try:
            # Ejecutar el procedimiento almacenado para obtener los datos de vacaciones por identidad
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_GET_VACACIONES', [identidad])
                resultados = cursor.fetchall()

                # Procesar los resultados en un diccionario para enviarlos como JSON
                vacaciones = []
                for row in resultados:
                    vacaciones.append({
                        'id_empleado': row[0],
                        'fecha_inicio': row[1].strftime('%Y-%m-%d') if row[1] else '',
                        'fecha_actual': row[2].strftime('%Y-%m-%d') if row[2] else '',
                        'tiempo_transcurrido': row[3],
                        'dias_proporcionales': row[4],
                        'dias_tomados': row[5],
                        'total': row[6]
                    })

            # Retornar los datos en formato JSON
            return JsonResponse({'data': vacaciones})

        except Exception as e:
            # En caso de error, retornar el error en un JSON
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    # Si el método no es GET, retornar un error 405 (Método no permitido)
    return JsonResponse({'status': 'fail', 'error': 'Método no permitido'}, status=405)


def obtener_vacaciones_por_dni(request):
    # Obtener el valor de identidad enviado por el frontend (puede ser GET o POST)
    identidadEmpleado = request.GET.get('identidad')  # Si es una solicitud GET
    # O usa request.POST.get('identidad') si es una solicitud POST

    if not identidadEmpleado:
        return JsonResponse({'status': 'error', 'message': 'Identidad no proporcionada'}, status=400)

    print(f"Solicitud recibida para el empleado con identidad: {identidadEmpleado}")  # Depuración inicial
    
    try:
        # Ejecutar el procedimiento almacenado para obtener los datos de vacaciones
        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_LIST_EMPLEADOS_VACACIONES_IDENTIDAD', [identidadEmpleado])
            result = cursor.fetchall()
            print(f"Resultado del procedimiento almacenado: {result}")  # Depuración del resultado de MySQL

        # Verificar si se obtuvieron resultados
        vacaciones_data = []
        if result:
            for vacacion in result:
                # Construir el objeto de vacaciones basado en el resultado devuelto por el procedimiento
                vacaciones_data.append({
                    'numero': vacacion[0],  # Índice columna 'numero' (ve.id)
                    'dni': vacacion[1],  # Índice columna 'dni' (e.identidad)
                    'empleado': vacacion[2],  # Índice columna 'empleado' (e.nombre_completo)
                    'fecha_inicio': vacacion[3].strftime('%Y-%m-%d') if vacacion[3] else '',  # Índice columna 'fecha_inicio'
                    'fecha_final': vacacion[4].strftime('%Y-%m-%d') if vacacion[4] else '',  # Índice columna 'fecha_final'
                    'dias_vacaciones': vacacion[8],  # Índice columna 'dias_vacaciones' (días calculados)
                    'comentario': vacacion[5],  # Índice columna 'comentario' (ve.comentario)
                    'ticket': vacacion[6],  # Índice columna 'ticket'
                    'estado': vacacion[7]  # El estado ya viene como texto ("Activo" o "Anulado")
                })
            print(f"Datos de vacaciones a enviar: {vacaciones_data}")  # Depuración antes de enviar la respuesta
        else:
            print("No se encontraron datos para el empleado.")  # Depuración en caso de no encontrar resultados

        # Devolver siempre un status 200 con los datos (vacíos si no se encontraron)
        return JsonResponse({'status': 'success', 'data': vacaciones_data}, status=200)

    except Exception as e:
        print(f"Error en la vista: {str(e)}")  # Depuración del error
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def asignar_ticket_vacaciones(request):
    if request.method == 'POST':
        # Obtén los parámetros enviados en la solicitud POST
        varID = request.POST.get('id_vacaciones')
        ticket = request.POST.get('id_ticket')

        # Verifica que los parámetros sean válidos
        if varID is None or ticket is None:
            return JsonResponse({'status': 'error', 'message': 'Faltan parámetros'})

        # Ejecuta el procedimiento almacenado
        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('EVAC_ASSIGN_TICKET_VACACIONES', [varID, ticket])
                # Fetch the result to check if the ticket was assigned or already exists
                result = cursor.fetchone()
                existe = result[0]  # Asume que la respuesta es un número que indica si ya existe o no

            if existe == 0:
                return JsonResponse({'status': 'success', 'message': 'Ticket asignado correctamente'})
            else:
                return JsonResponse({'status': 'error', 'message': 'El ticket ya está asignado'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
    

def actualizar_contrato(request):
    if request.method == 'POST':
        # Obtener los parámetros enviados en la solicitud POST
        id_contrato = request.POST.get('id_contrato')
        estado = request.POST.get('estado')
        usuario = request.POST.get('usuario')

        # Validar los parámetros
        if not id_contrato or not estado or not usuario:
            return JsonResponse({'status': 'error', 'message': 'Faltan parámetros id_contrato, estado o usuario'})

        # Ejecutar el procedimiento almacenado
        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('EVA_UPDATE_ESTADO_CONTRATO', [id_contrato, estado, usuario])

            # Si el procedimiento se ejecuta correctamente, se responde con éxito
            return JsonResponse({'status': 'success', 'message': 'Contrato actualizado correctamente'})

        except Exception as e:
            # Capturar cualquier error y devolver una respuesta con el mensaje del error
            logger.error(f'Error al actualizar el contrato: {e}', exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)})

    else:
        # Si no es una solicitud POST, devolver error de método no permitido
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
    
