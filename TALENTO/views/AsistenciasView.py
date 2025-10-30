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



#*************************************** Planilla ********************************
logger = logging.getLogger(__name__)  # Inicializa el logger


#================================= Asistencia =================================


def nueva_asistencia(request):
    user_id = request.session.get('user_id', '')  

    if not user_id:
        return HttpResponseRedirect(reverse('login'))

    usuarios_biometrico = obtener_usuarios_biometrico()
    tipo_registro = obtener_tipo_registro() 
   

    context = {
        'usuarios_biometrico': usuarios_biometrico,
        'tipo_registro': tipo_registro,
        'incidencias':obtener_incidencias()
       
    }

    # Renderizar la página de asistencia con el contexto
    return render(request, 'asistencia/asistencia.html', context)

def horarios(request):
    id = request.session.get('user_id', '')

    if id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        return render(request, 'asistencia/horarios.html')


def incidencias(request):
    id = request.session.get('user_id', '')

    if id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        return render(request, 'asistencia/incidencias.html')



def registro(request):
    id = request.session.get('user_id', '')

    if id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        return render(request, 'asistencia/tipo_registro.html')

def vista_principal_modulos(request):
    id = request.session.get('user_id', '')

    if id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        return render(request, 'lobby.html')


def departamentos_turnos(request):
    id = request.session.get('user_id', '')

    if id == '':
        return HttpResponseRedirect(reverse('login'))
    elif request.session.get('configTurnos') == 1 or request.session.get('talentoHumanoAdminIT') == 1:
        return render(request, 'asistencia/departamentos.html')
    else:
        return HttpResponseRedirect(reverse('vista_principal_modulos'))

def dias_libres_turnos(request):
    id = request.session.get('user_id', '')

    if id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        
        turnos = obtener_todos_turnos()
        print("Turnos pasados al contexto:", turnos)  

        context = {
            'turnos': turnos, 
        }
        return render(request, 'asistencia/dias_libres_turnos.html', context)

def mostrar_departamentos_empresa(request):
    if request.method == 'GET':
        try:
            with connections['global_nube'].cursor() as cursor:
                # Llamar al procedimiento almacenado
                cursor.callproc('TH_GET_GRUPOS_DEPARTAMENTOS')
                resultados = cursor.fetchall()

                # Construir la lista de departamentos
                departamentos = []
                for row in resultados:
                    departamentos.append({
                        'PKgrupo': row[0],
                        'Nombre': row[1],
                        'Descripcion': row[2],
                    })

            return JsonResponse({'status': 'success', 'departamentos': departamentos})

        except Exception as e:
            logger.error(f"Error al mostrar departamentos: {str(e)}")
            return JsonResponse({'status': 'fail', 'error': str(e)}, status=500)

    logger.warning("Método de solicitud no válido")
    return JsonResponse({'status': 'fail', 'error': 'Invalid request method'}, status=400)

def insert_update_turno(request):
    try:
        existe = 0

        turno_id = request.POST.get('turno_id')  
        nombre_turnos = request.POST.get('nombre_turnos')
        hora_entrada = request.POST.get('hora_entrada')
        hora_salida = request.POST.get('hora_salida')
        tolerancia_minutos = request.POST.get('tolerancia_minutos')
        dia_libre_turno = request.POST.get('dia_libre_turno')
        require_marcacion = request.POST.get('require_marcacion')
        id_departamento = request.POST.get('id_departamento')
        opcion = request.POST.get('opcion')

        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('TH_INSERT_UPDATE_TURNO', [
                turno_id,
                id_departamento,
                nombre_turnos,
                hora_entrada,
                hora_salida,
                tolerancia_minutos,
                require_marcacion,
                dia_libre_turno,
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


def insert_update_tipo_incidencia(request):
    try:
     
        # Recibir datos desde el frontend
        incidencia_id = request.POST.get('incidencia_id')  # ID del registro (para actualización)
        tipo_incidencia = request.POST.get('tipo_incidencia')  # Nombre del tipo de incidencia
        descripcion = request.POST.get('descripcion')  # Descripción de la incidencia
        justificado = request.POST.get('justificado')  # Justificado (1: Sí, 0: No)
        opcion = request.POST.get('opcion')  # Operación (1: Insertar, 2: Actualizar)

        # Obtener el nombre de usuario desde la sesión
        userName = request.session.get('userName', '')

        # Conexión a la base de datos
        appConn = connections['universal']
        with appConn.cursor() as cursor:
            # Llamar al procedimiento almacenado
            cursor.callproc('TH_INSERT_UPDATE_TIPO_INCIDENCIA', [
                incidencia_id,
                tipo_incidencia,
                descripcion,
                justificado,
                userName,
                opcion
            ])

            # Obtener los resultados
            results = cursor.fetchall()
            existe = 0
            if results:
                for result in results:
                    existe = result[0]  # Leer el estado de la operación
            
        # Cerrar conexión
        appConn.close()

        # Responder con los resultados
        datos = {'save': 1, 'existe': existe}

    except Exception as e:
        # Manejo de errores
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)


def update_status_turno(request):
    try:
        existe = 0

        turno_id = request.POST.get('turno_id')  
        estado = request.POST.get('estado')

        userName = request.session.get('userName', '')

        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('TH_UPDATE_STATUS_TURNO', [
                turno_id,
                estado,
                userName
            ]) 
        
        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)

def update_status_incidencia(request):
    try:
        userName = request.session.get('userName', '')
        incidencia_id = request.POST.get('incidencia_id')  
        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc('TH_UPDATE_STATUS_INCIDENCIAS', [
                incidencia_id, userName
            ]) 
        
        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)

def insertar_incidencias_registradas(request):
    try:
        # Obtener los datos enviados por AJAX
        arr_incidencias = json.loads(request.POST.get('arrIncidencia', '[]'))
        userName = request.session.get('userName', '')

        for incidencia in arr_incidencias:
            id_detalle_x_empleado = incidencia.get('id_detalle_x_empleado')
            fecha = incidencia.get('fecha')
            descripcion = incidencia.get('descripcion', '')  # Obtener la descripción
            id_tipo_incidencia = incidencia.get('id_tipo_incidencia')  # Obtener el tipo de incidencia

            # Llamar al procedimiento almacenado con los nuevos parámetros
            with connections['universal'].cursor() as cursor:
                cursor.callproc('TH_INSERTAR_INCIDENCIAS_REGISTRADAS', [
                    id_detalle_x_empleado,
                    fecha,
                    descripcion,
                    id_tipo_incidencia,  # Nuevo parámetro
                    userName
                ])

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)

def insertar_registro_incendincias_manual(request):
    try:
        # Obtener los datos de la solicitud POST
        id_empleado = request.POST.get('IdUsuario')  
        fecha_acceso = request.POST.get('FechaHoraAcceso')
        tipo_acceso = request.POST.get('TipoAcceso')
        modificado_por = request.session.get('userName', '')

        # Validar que los parámetros requeridos no sean nulos
        if not id_empleado or not fecha_acceso or not tipo_acceso:
            return JsonResponse({'save': 0, 'error': 'Faltan datos obligatorios para el registro.'})

        with connections['universal'].cursor() as cursor:
            # Llamar al procedimiento almacenado
            cursor.callproc('TH_REGISTRO_ASISTENCIA_MANUAL', [
                id_empleado,
                fecha_acceso,
                tipo_acceso,
                modificado_por
            ])

        # Si todo sale bien, devolver una respuesta exitosa
        datos = {'save': 1}

    except Exception as e:
        # Manejo de excepciones y retorno de error
        error_message = str(e)
        if "Ya existe un registro" in error_message:
            error_message = "Ya existe un registro con esa fecha y tipo de acceso"
        datos = {'save': 0, 'error': error_message}

    return JsonResponse(datos)

def mostrar_turnos(request):
    id_departamento = request.POST.get('id_departamento')

    try:
        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc("TH_MOSTRAR_TURNOS_ASISTENCIA", [id_departamento])
            column_names = [desc[0] for desc in cursor.description]
            turnosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        appConn.close()
        
        # Devuelve los resultados como JSON
        return JsonResponse({'data': turnosData})
    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})



def get_horarios_x_turno(request):
    id_turno = request.POST.get('id_turno')

    try:
        appConn = connections['universal']
        with appConn.cursor() as cursor:
            cursor.callproc("TH_TURNOS_GET_HORARIOS", [id_turno])
            column_names = [desc[0] for desc in cursor.description]
            horariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        appConn.close()
        
        # Devuelve los resultados como JSON
        return JsonResponse({'data': horariosData})
    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})



def update_dia_libre_horarios(request):
    try:
        id_horario = request.POST.get('id_horario', 0)
        dia_libre = request.POST.get('dia_libre', 0)
        userName = request.session.get('userName', '') 

        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_TURNOS_MARCAR_DIA_LIBRE', [id_horario, dia_libre, userName])

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def update_horas_x_dia_x_horario(request):
    try:
        id_horario = request.POST.get('id_horario', 0)
        hora_entrada = request.POST.get('hora_entrada', 0)
        hora_salida = request.POST.get('hora_salida', 0) 
        userName = request.session.get('userName', '') 

        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_TURNOS_UPDATE_HORARIOS', [id_horario, hora_entrada, hora_salida, userName])

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)



def obtener_empleado_departamento(request):
    try:

        id_departamento = request.GET.get('id_departamento')
        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_OBTENER_EMPLEADOS_DEPARTAMENTO', [int(id_departamento)])
            resultados = cursor.fetchall()
        empleados = []
        for row in resultados:
            empleados.append({
                'id_empleado': row[0],
                'nombre_completo': row[1],
            })

        return JsonResponse({'empleados': empleados}, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



#================================= conexion sqlserver y mysql ====================================

def export_and_import_data(request):
    try:
        # Configuración de la conexión a SQL Server
        sql_server_connection_params = {
            "server": "190.4.11.58:1433",
            "user": "csolano",
            "password": "Qaz*123",
            "database": "biometricos",
        }

        # Definir ruta para el archivo CSV
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_file_path = os.path.join(BASE_DIR, 'media', 'documentos', 'data.csv')
        os.makedirs(os.path.join(BASE_DIR, 'media', 'documentos'), exist_ok=True)

        # Obtener última fecha y último Userid desde MySQL
        with connections['universal'].cursor() as mysql_cursor:
            mysql_cursor.execute("CALL TH_OBTENER_ULTIMO_REGISTRO_BIOMETRICO(@ultima_fecha_hora, @ultimo_userid)")
            mysql_cursor.execute("SELECT @ultima_fecha_hora, @ultimo_userid")
            result = mysql_cursor.fetchone()
            if result:
                ultima_fecha_hora, ultimo_userid = result
            else:
                ultima_fecha_hora, ultimo_userid = "0000-00-00 00:00:00", 0

        # Conexión a SQL Server para obtener empleados y registros de accesos
        with pymssql.connect(**sql_server_connection_params) as sqlserver_conn:
            with sqlserver_conn.cursor(as_dict=True) as sqlserver_cursor:
                # Obtener empleados
                employee_query = """
                    SELECT 
                        [Userid],
                        [Name],
                        [Deptid]
                    FROM [biometricos].[dbo].[Userinfo]
                    WHERE [Userid] > %s
                """
                sqlserver_cursor.execute(employee_query, (ultimo_userid,))
                employees = sqlserver_cursor.fetchall()

                # Obtener registros de accesos
                access_query = """
                    SELECT 
                        [Logid],
                        [Userid],
                        [CheckTime],
                        [CheckType],
                        [Sensorid]
                    FROM [biometricos].[dbo].[Checkinout]
                    WHERE [CheckTime] > %s
                """
                sqlserver_cursor.execute(access_query, (ultima_fecha_hora,))
                access_logs = sqlserver_cursor.fetchall()

        # Escribir registros de accesos en un archivo CSV
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Logid", "IdUsuario", "FechaHoraAcceso", "TipoAcceso", "IdSensor"])
            for row in access_logs:
                writer.writerow([
                    row['Logid'],
                    row['Userid'],  # Ajusta al nombre real si es diferente
                    row['CheckTime'],
                    row['CheckType'],
                    row['Sensorid']
                ])

        # Importar datos en MySQL
        with transaction.atomic(using='universal'):
            with connections['universal'].cursor() as mysql_cursor:
                # Insertar empleados en la tabla temporal
                employee_batch = []
                for employee in employees:
                    employee_batch.append((
                        employee['Userid'],
                        employee['Name'],
                        employee['Deptid']
                    ))

                if employee_batch:
                    mysql_cursor.executemany("""
                        INSERT INTO th_info_empleado_biometrico_temporal (
                            Userid, Name, Deptid
                        )
                        VALUES (%s, %s, %s)
                    """, employee_batch)

                # Importar registros de accesos desde el archivo CSV
                csv_file_path_for_mysql = csv_file_path.replace("\\", "/")
                load_query = f"""
                    LOAD DATA LOCAL INFILE '{csv_file_path_for_mysql}'
                    INTO TABLE th_registrosAcceso_biometrico_temporal
                    FIELDS TERMINATED BY ',' ENCLOSED BY '"'
                    LINES TERMINATED BY '\n'
                    IGNORE 1 ROWS
                    (Logid, IdUsuario, FechaHoraAcceso, TipoAcceso, IdSensor)
                """
                mysql_cursor.execute(load_query)

        return JsonResponse({
            "message": "Datos exportados e importados exitosamente.",
            "employees_count": len(employees),
            "access_logs_count": len(access_logs)
        }, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def actualizar_empleado_departamento(request):
    try:
        id_empleado = request.POST.get('id_empleado')
        opcion = int(request.POST.get('opcion'))  
        id_turno = request.POST.get('id_turno') 
        modificado_por = request.session.get('userName', '') 

        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_ACTUALIZAR_EMPLEADO_DEPARTAMENTO', [id_empleado, opcion, id_turno, modificado_por])

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)



def mostrar_turnos_empleados(request):
    try:
        id_turno = request.GET.get('id_turno')

        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_MOSTRAR_TURNOS_EMPLEADOS', [int(id_turno)])
            resultados = cursor.fetchall()

        # Procesa los resultados
        turnos_empleados = []
        for row in resultados:
            turnos_empleados.append({
                'id_turno_empleados': row[0],
                'id_empleado': row[1],
                'nombre_empleado': row[2],
            })

        return JsonResponse({'turnos_empleados': turnos_empleados}, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def mostrar_asistencia_marcados(request):
    try:
        user_id = request.session.get('user_id', 0)

        varAcceso = 1
        verAsistenciasMisColaboradores = request.session.get('verAsistenciasMisColaboradores')
        verTodasLasAsistencias = request.session.get('verTodasLasAsistencias')
        adminIT = request.session.get('talentoHumanoAdminIT')

        print(verAsistenciasMisColaboradores)
        print(verTodasLasAsistencias)
        print(adminIT)

        if adminIT == 1:
            varAcceso = 0
        if verAsistenciasMisColaboradores == 1:
            varAcceso = 1
        if verTodasLasAsistencias == 1:
            varAcceso = 0
        
        
        fecha_inicio = request.POST.get('date1')
        fecha_fin = request.POST.get('date2')

        with connections['universal'].cursor() as cursor:
            cursor.callproc("TH_ASISTENCIA_VISUALIZAR_MARCACIONES_v2", [fecha_inicio, fecha_fin, user_id, varAcceso])
            column_names = [desc[0] for desc in cursor.description]
            crudMarcaciones = [dict(zip(column_names, row)) for row in cursor.fetchall()]
        return JsonResponse({'data': crudMarcaciones}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def obtener_usuarios_biometrico():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_ASOCIAR_EMPLEADOS_BIOMETRICOS_FICHA_EMPLEADO')  
        results = cursor.fetchall()

    return results

def obtener_incidencias():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_TIPO_INCIDENCIAS')  
        results = cursor.fetchall()

    return results


def obtener_tipo_registro():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_TIPO_REGISTRO')  
        results = cursor.fetchall()

    return results
def obtener_todos_turnos():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('TH_MOSTRAR_TODOS_TURNOS')  
        results = cursor.fetchall()
    
    # Imprimir los resultados obtenidos del procedimiento almacenado
    print("Resultados obtenidos desde 'TH_MOSTRAR_TODOS_TURNOS':", results)
    return results


def mostrar_dias_libres(request):
    try:
        fecha_inicio = request.POST.get('date1')
        fecha_fin = request.POST.get('date2')

        with connections['universal'].cursor() as cursor:
            cursor.callproc("TH_OBTENER_DIAS_LIBRES", [fecha_inicio, fecha_fin])
            column_names = [desc[0] for desc in cursor.description]
            crudDiasLibres = [dict(zip(column_names, row)) for row in cursor.fetchall()]
        return JsonResponse({'data': crudDiasLibres}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def mostrar_todos_turnos(request):
    try:
  
        # Conexión y llamada al procedimiento
        with connections['universal'].cursor() as cursor:
            cursor.callproc("TH_MOSTRAR_TODOS_TURNOS")
            column_names = [desc[0] for desc in cursor.description]
            crudTurnos = [dict(zip(column_names, row)) for row in cursor.fetchall()]
        
        return JsonResponse({'turnos': crudTurnos}, safe=False)

    except Exception as e:
        print(f"Error en mostrar_todos_turnos: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def mostrar_todas_incidencias(request):
    try:
  
        # Conexión y llamada al procedimiento
        with connections['universal'].cursor() as cursor:
            cursor.callproc("TH_TIPO_INCIDENCIAS")
            column_names = [desc[0] for desc in cursor.description]
            crudIncidencias = [dict(zip(column_names, row)) for row in cursor.fetchall()]
        
        return JsonResponse({'turnos': crudIncidencias}, safe=False)

    except Exception as e:
        print(f"Error en mostrar_todos_turnos: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def insertar_dias_libres_turnos(request):
    try:
 
        id_dia_libre = int(request.POST.get('id_dia_libre', 0))  
        fecha = request.POST.get('fecha')  
        comentarios = request.POST.get('comentarios', '')
        turnos_json = request.POST.get('turnos') 
        creado_por = request.session.get('userName')
        opc = int(request.POST.get('opc', 1))

 
        turnos = json.loads(turnos_json) if turnos_json else []

  
        turnos = [int(turno) for turno in turnos]


        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_INSERTAR_DIAS_LIBRES_TURNOS', [
                id_dia_libre,
                fecha,
                comentarios,
                creado_por,
                json.dumps(turnos), 
                opc
            ])

  
        return JsonResponse({'save': 1})
    except Exception as e:
        return JsonResponse({'save': 0, 'error': str(e)})

def actualizar_dias_libres_turnos(request):
    try:
        id_dia_libre = int(request.POST.get('id_dia_libre', 0))  
        fecha = request.POST.get('fecha')  
        comentarios = request.POST.get('comentarios', '')
        turnos = request.POST.get('turnos')  
        creado_por = request.session.get('userName')

        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_ACTUALIZAR_DIAS_LIBRES', [
                id_dia_libre,
                turnos,
                fecha,     
                comentarios,
                creado_por
            ])


        return JsonResponse({'save': 1})
    except Exception as e:
        print(f"Error al procesar: {str(e)}")
        return JsonResponse({'save': 0, 'error': str(e)})


def eliminar_dia_libre(request):
    try:

        id_dia_libre = request.POST.get('id_dia_libre')  
        userName = request.session.get('userName', '')  

        with connections['universal'].cursor() as cursor:
            cursor.callproc('TH_ELIMINAR_DIA_LIBRE_TURNO', [id_dia_libre, userName])

        datos = {'save': 1, 'message': 'Día libre eliminado correctamente.'}
    except Exception as e:

        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)


