from django.http import HttpResponse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
import datetime

LOGIN_URL = 'http://3.230.160.184:81/CWS'

def vista_principal_lobby(request):
    id = request.session.get('user_id', '')
    if id == '':
        return HttpResponseRedirect(LOGIN_URL)
    else:

        return render(request, 'kanban/lobby.html')
    
def vista_principal_kanban(request):
    id = request.session.get('user_id', '')
    if id == '':
        return HttpResponseRedirect(LOGIN_URL)  
    else:
      
        tipo_planes = obtener_tipos_planes()
        grupos = obtener_grupos()
        
        

       
        context = {
            'tipo_planes': tipo_planes,
            'grupos': grupos,
            
        }
        
        
        return render(request, 'kanban/principal.html', context)
    


def obtener_estado_tareas():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('KNB_TASKS_ESTADOS')  
        results = cursor.fetchall()
    return results

def obtener_prioridad():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('KNB_GET_PRIORIDADES')  
        results = cursor.fetchall()
    return results

def obtener_tipos_planes():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('KNB_PLANES_GET_TIPOS')  
        results = cursor.fetchall()
    
    print("Planes obtenidos:", results) 
    return results

def obtener_grupos():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('SDK_GET_ALL_GROUPS')  
        results = cursor.fetchall()
    
    print("Grupos obtenidos:", results)  
    return results

def obtener_usuarios():
    with connections['global_local'].cursor() as cursor:
        cursor.callproc('GS_GET_ALL_USUARIOS')  
        results = cursor.fetchall()
    
    print("Usuarios obtenidos:", results)  
    return results

def obtener_tipos_usuarios():
    with connections['universal'].cursor() as cursor:
        cursor.callproc('KNB_PLANES_GET_TIPOS_USUARIOS')  
        results = cursor.fetchall()
    
    print("Tipos de Usuarios:", results)  
    return results

def obtener_planes_usuario(request):
    user_id = request.session.get('user_id', 428)  

    with connections['universal'].cursor() as cursor:
        cursor.callproc('KNB_PLANES_X_USER', [user_id])
        planes = cursor.fetchall()

    planes_data = []
    for plan in planes:
        planes_data.append({
            'id_plan': plan[0],
            'nombre_plan': plan[1],
            'descripcion_plan': plan[2],
            'id_tipo_plan': plan[3],
            'id_area': plan[4],
            'fecha_inicio': plan[5].strftime('%Y-%m-%d'),
            'fecha_final': plan[6].strftime('%Y-%m-%d'),
            'icono': plan[19] if len(plan) > 19 else '',  
            'estado_plan': plan[20] if len(plan) > 20 else '',  
        })

    return JsonResponse({'success': True, 'data': planes_data})


def gestion_planes(request):
    if request.method == 'POST':
     
        plan = request.POST.get('plan')
        descripcion = request.POST.get('descripcion')
        tipo_plan = request.POST.get('tipo_plan')
        area = request.POST.get('area')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_final = request.POST.get('fecha_final')
        user_name = request.POST.get('creado_por')
        user_id = request.POST.get('user_id')
        opcion = 1  
        var_id = 0  

      
        with connections['universal'].cursor() as cursor:
            cursor.callproc('KNB_PLANES_CREATE_UPDATE', [
                var_id,
                plan,
                descripcion,
                tipo_plan,
                area,
                user_name,
                user_id,
                opcion,
                fecha_inicio,
                fecha_final
            ])

       
            result = cursor.fetchall()

  
        existe = result[0][0]
        var_id = result[0][1]

        if existe == 0:
            return JsonResponse({'status': 'success', 'message': 'Plan creado exitosamente', 'plan_id': var_id})
        else:
            return JsonResponse({'status': 'error', 'message': 'El plan ya existe'})


    planes = [] 
    return render(request, 'kanban/principal.html', {'planes': planes})


def detalle_plan(request, id_plan):
    try:
        with connections['universal'].cursor() as cursor:
            cursor.callproc('KNB_OBTENER_PLAN_POR_ID', [id_plan])
            result = cursor.fetchall()
            print(f"Resultado del plan: {result}")

        with connections['universal'].cursor() as cursor:
            cursor.callproc('KNB_OBTENER_ESTADOS_PLAN')
            estados = cursor.fetchall()
            print(f"Estados del plan: {estados}")
    except Exception as e:
        print(f"Error al obtener los datos: {e}")
        return render(request, '500.html')  # Página de error interno en lugar de 404 si falla el procedimiento

    if not result:
        return render(request, '404.html')  # Si no hay resultados, muestra el 404
    
    # Resto del código
    tareas = obtener_estado_tareas()
    prioridad = obtener_prioridad()
    usuarios = obtener_usuarios()
    tipos_usuarios = obtener_tipos_usuarios()
    tipo_planes = obtener_tipos_planes()
    grupos = obtener_grupos()

    plan = {
        'id': result[0][0],
        'nombre_plan': result[0][1],
        'descripcion_plan': result[0][2],
        'id_tipo_plan': result[0][3],
        'id_area': result[0][4],
        'id_estado_plan': result[0][5],
        'fecha_inicio': result[0][6],
        'fecha_final': result[0][7],
    }

    context = {
        'plan': plan,
        'estados': estados,
        'tareas': tareas,
        'prioridad': prioridad,
        'usuarios': usuarios,
        'tipos_usuarios': tipos_usuarios,
        'tipo_planes': tipo_planes,
        'grupos': grupos,
    }

    return render(request, 'kanban/detalle_plan.html', context)




def obtener_estados_plan(request, id_plan):
    try:
      
        with connections['universal'].cursor() as cursor:
            cursor.callproc('KNB_OBTENER_ESTADOS_PLAN')
            estados = cursor.fetchall()

      
        with connections['universal'].cursor() as cursor:
            cursor.callproc('KNB_OBTENER_PLAN_POR_ID', [id_plan])
            plan_result = cursor.fetchone()

        if not plan_result:
            return JsonResponse({'status': 'error', 'message': 'Plan no encontrado.'}, status=404)

        id_estado_actual = plan_result[5]  

    
        estados_data = []
        for estado in estados:
            estados_data.append({
                'id_estado': estado[0],
                'nombre_estado': estado[1],
                'es_seleccionado': id_estado_actual == estado[0]
            })

        return JsonResponse({'status': 'success', 'estados': estados_data})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
def eliminar_columna(request):
    if request.method == 'POST':
        id_columna = request.POST.get('id_columna')
        eliminado_por = request.POST.get('eliminado_por')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_COLUMNAS_DELETE', [id_columna, eliminado_por])
            
            return JsonResponse({'status': 'success', 'message': 'Columna eliminada correctamente.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

def eliminar_tarea(request):
    if request.method == 'POST':
        id_tarea = request.POST.get('id_tarea')
        eliminado_por = request.POST.get('eliminado_por')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_TASKS_DELETE', [id_tarea, eliminado_por])
            
            return JsonResponse({'status': 'success', 'message': 'Tarea eliminada correctamente.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

def eliminar_plan(request):
    if request.method == 'POST':
        id_plan = request.POST.get('id_plan')
        eliminado_por = request.POST.get('eliminado_por')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_PLANES_DELETE', [id_plan, eliminado_por])
            
            return JsonResponse({'status': 'success', 'message': 'Plan eliminado correctamente.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)



def actualizar_estado_plan(request):
    if request.method == 'POST':
        plan_id = request.POST.get('id_plan')
        nuevo_estado = request.POST.get('nuevo_estado')
        user_name = request.POST.get('user_name')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_PLANES_UPDATE_ESTADO', [plan_id, nuevo_estado, user_name])
            
            return JsonResponse({'status': 'success', 'message': 'Estado actualizado correctamente'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})


def crear_actualizar_columnas(request):
    if request.method == 'POST':
        var_id = request.POST.get('id_columna', 0)  
        var_columna = request.POST.get('columna')
        var_plan = request.POST.get('id_plan')  
        user_name = request.POST.get('creado_por')
        opcion = 1 if int(var_id) == 0 else 2  

        with connections['universal'].cursor() as cursor:
            cursor.callproc('KNB_COLUMNAS_CREATE_UPDATE', [var_id, var_columna, var_plan, user_name, opcion])
            result = cursor.fetchall()

        existe = result[0][0]
        var_id = result[0][1]

        if existe == 0:
            return JsonResponse({'status': 'success', 'message': 'Columna guardada exitosamente', 'id_columna': var_id})
        else:
            return JsonResponse({'status': 'error', 'message': 'Ya existe una columna con ese nombre.'})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'})

def obtener_columnas_plan(request):
    if request.method == 'GET':
        var_plan = request.GET.get('id_plan')

        try:
            with connections['universal'].cursor() as cursor:
               
                cursor.callproc('KNB_COLUMNAS_X_PLAN', [var_plan])
                columnas = cursor.fetchall()

           
            columnas_data = []
            for columna in columnas:
                columnas_data.append({
                    'id_columna': columna[0],
                    'nombre_columna': columna[1],
                    'id_plan': columna[2],
                    'creado_por': columna[3],
                 
                    'fecha_creacion': columna[4].strftime('%Y-%m-%d') if columna[4] and isinstance(columna[4], (datetime.date, datetime.datetime)) else '',
                })

            return JsonResponse({'status': 'success', 'data': columnas_data})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'})
 

def crear_tarea(request):
    if request.method == 'POST':
       
        var_columna = request.POST.get('id_columna')  
        var_task = request.POST.get('nombre_tarea')  
        user_name = request.POST.get('creado_por')    

        
        missing_fields = []
        if not var_columna:
            missing_fields.append('id_columna')
        if not var_task:
            missing_fields.append('nombre_tarea')
        if not user_name:
            missing_fields.append('creado_por')

        if missing_fields:
            return JsonResponse({
                'status': 'error',
                'message': f'Faltan los siguientes campos: {", ".join(missing_fields)}'
            })

        try:
            
            with connections['universal'].cursor() as cursor: 
             
                cursor.callproc('KNB_TASKS_CREATE', [var_columna, var_task, user_name])
             
                result = cursor.fetchall()

            if result:
             
                tarea_creada = result[0] 
                id_tarea = tarea_creada[0] 
                nombre_tarea = tarea_creada[1] 
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Tarea creada exitosamente',
                    'id_tarea': id_tarea,
                    'nombre_tarea': nombre_tarea
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No se pudo crear la tarea'
                })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al ejecutar el procedimiento almacenado: {str(e)}'
            })

    return JsonResponse({
        'status': 'error',
        'message': 'Método no permitido'
    })

def obtener_tareas_por_columna(request, id_columna):
    try:
        with connections['universal'].cursor() as cursor:
            cursor.callproc('KNB_TASKS_X_COLUMNA', [id_columna])
            tareas = cursor.fetchall()

            # Depuración: imprime los resultados de la base de datos
            print(f"Tareas para columna {id_columna}: {tareas}")

            tareas_data = []
            for tarea in tareas:
                tareas_data.append({
                    'id_tarea': tarea[0],
                    'nombre_tarea': tarea[1],
                    'descripcion_tarea': tarea[2],
                    'porcentaje': tarea[3],
                    'id_prioridad': tarea[4],
                    'fecha_inicio': tarea[5],
                    'fecha_final': tarea[6],
                    'fecha_hora_iniciado': tarea[7],
                    'fecha_hora_completado': tarea[8],
                    'id_columna': tarea[9],
                    'estado': tarea[10],
                    'creado_por': tarea[11],
                    'fecha_hora_creado': tarea[12],
                    'modificado_por': tarea[13],
                    'fecha_hora_modificado': tarea[14],
                    'fecha_hora_modificado_text': tarea[15],
                    'orden': tarea[16],
                    'estado_tarea': tarea[17],
                    'icono': tarea[18],
                    'nombre_estado_tarea': tarea[19]
                })

        return JsonResponse({
            'status': 'success',
            'tareas': tareas_data
        })
    except Exception as e:
        print(f"Error al obtener tareas: {str(e)}")  # Depuración del error
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


def knb_tasks_details_create_update(request):
    if request.method == 'POST':
        var_id = request.POST.get('id', None) 
        var_task = request.POST.get('task')   
        var_detalle = request.POST.get('detalle') 
        user_name = request.POST.get('userName')  
        opcion = request.POST.get('opcion')       

        # Validar que todos los datos obligatorios están presentes
        if not var_task or not var_detalle or not user_name or not opcion:
            return JsonResponse({'error': 'Faltan datos obligatorios'}, status=400)

        # Validar tipos de datos
        try:
            var_task = int(var_task)
            opcion = int(opcion)
            var_id = int(var_id) if var_id else 0 
        except ValueError:
            return JsonResponse({'error': 'Datos inválidos en los parámetros'}, status=400)

        # Ejecutar el procedimiento almacenado
        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_TASKS_DETAILS_CREATE_UPDATE', [var_id, var_task, var_detalle, user_name, opcion])

                result = cursor.fetchall()  # Obtener el resultado del procedimiento

                # Si no hay resultados en el fetch, devolver un mensaje apropiado
                if not result:
                    return JsonResponse({'error': 'No se pudo obtener el resultado del procedimiento.'}, status=500)

                columns = [col[0] for col in cursor.description]  # Obtener los nombres de las columnas
                data = [dict(zip(columns, row)) for row in result]  # Convertir resultado a diccionario

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        # Devolver la respuesta correcta con los datos
        return JsonResponse({'status': 'success', 'data': data}, status=200)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

def knb_tasks_update(request):
    # Recoge los parámetros de la solicitud POST
    var_name = request.POST.get('nombre_tarea')
    var_desc = request.POST.get('descripcion_tarea')
    var_prioridad = request.POST.get('prioridad_tarea')
    date1 = request.POST.get('fecha_inicio_tarea')
    date2 = request.POST.get('fecha_final_tarea')
    var_estado = request.POST.get('estado_tarea')
    user_name = request.POST.get('user_name')
    var_id = request.POST.get('tarea_id')
    var_porcentaje = request.POST.get('porcentaje_tarea')


    # Ejecutar el procedimiento almacenado
    try:
        with connections['universal'].cursor() as cursor:
            # Llama al procedimiento almacenado 'KNB_TASKS_UPDATE'
            cursor.callproc('KNB_TASKS_UPDATE', [
                var_name, var_desc, var_prioridad, date1, date2,
                var_estado, user_name, var_id, var_porcentaje
            ])

            # Obtener los resultados devueltos por el procedimiento almacenado
            result = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in result] if result else []

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'success', 'data': data}, status=200)


def knb_tasks_details_create_update(request):
    if request.method == 'POST':
        # Obtener los valores del formulario
        tarea_id = request.POST.get('tarea_id')
        detalle_id = request.POST.get('detalle_id') 
        nombre_item = request.POST.get('nombre_item').strip() if request.POST.get('nombre_item') else None
        opcion = int(request.POST.get('opcion')) if request.POST.get('opcion') else None
        user_name = request.POST.get('creado_por') 

        # Validación de los campos requeridos
        missing_fields = []
        if not tarea_id:
            missing_fields.append('tarea_id')
        if not nombre_item:
            missing_fields.append('nombre_item')
        if opcion is None:
            missing_fields.append('opcion')

        if missing_fields:
            return JsonResponse({'save': 0, 'error': f'Faltan datos requeridos: {", ".join(missing_fields)}'})

        try:
            with connections['universal'].cursor() as cursor:
                # Si no existe detalle_id, es una creación
                detalle_id = detalle_id or 0  # Inicializamos con 0 si no existe

                # Llamar al procedimiento almacenado
                cursor.callproc('KNB_TASKS_DETAILS_CREATE_UPDATE', [detalle_id, tarea_id, nombre_item, user_name, opcion])

                # Ejecutar la consulta para obtener el detalle creado/actualizado
                cursor.execute("SELECT * FROM knb_tasks_details WHERE id_detalle_tarea = LAST_INSERT_ID()")
                item = cursor.fetchone()

                if item:
                    data = {
                        'id_detalle_tarea': item[0],
                        'detalle': item[2]
                    }
                    return JsonResponse({'save': 1, 'data': data})
                else:
                    return JsonResponse({'save': 0, 'error': 'No se pudo obtener el detalle actualizado/creado.'})

        except Exception as e:
            return JsonResponse({'save': 0, 'error': str(e)})
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)
  

def obtener_detalles_tarea(request, tarea_id):
    try:
        with connections['universal'].cursor() as cursor:
          
            cursor.callproc('KNB_TASKS_DETAILS_X_TASK', [tarea_id])
            detalles = cursor.fetchall()

         
            detalle_list = [
                {
                    'id_detalle_tarea': detalle[0],
                    'detalle': detalle[2],  
                    'creado_por': detalle[3],  
                } 
                for detalle in detalles
            ]

        return JsonResponse({'detalles': detalle_list, 'save': 1})
    except Exception as e:
        return JsonResponse({'error': str(e), 'save': 0})


def ver_detalle_tarea(request):
    if request.method == 'GET':
        id_tarea = request.GET.get('id_tarea')

        try:
            # Ejecutar el procedimiento almacenado para obtener el detalle de la tarea
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_TASKS_GET_DETALLE', [id_tarea])
                result = cursor.fetchone()

                if result:
                    detalle_tarea = {
                        'id_tarea': result[0],
                        'nombre_tarea': result[1],
                        'descripcion_tarea': result[2],
                        'id_estado_tarea': result[3],  # Este es el campo que debes verificar
                        'nombre_estado_tarea': result[4],
                        'icono': result[5],
                        'fecha_creacion': result[6],
                        'fecha_modificacion': result[7],
                        'creado_por': result[8],
                        'modificado_por': result[9],
                        'prioridad_tarea': result[10],
                        'fecha_inicio': result[11],
                        'fecha_final': result[12],
                    }
                    return JsonResponse({'status': 'success', 'detalle_tarea': detalle_tarea})
                else:
                    return JsonResponse({'status': 'error', 'message': 'Tarea no encontrada'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def agregar_usuario_a_plan(request):
    if request.method == 'POST':
        # Recoge los parámetros de la solicitud POST
        varPlan = request.POST.get('plan_id')  # ID del plan
        varID = request.POST.get('usuario_id')  # ID del usuario
        varRol = request.POST.get('rol_id')  # ID del rol del usuario
        userName = request.POST.get('creado_por')  # Nombre del usuario que realiza la acción

        if not varPlan or not varID or not varRol or not userName:
            return JsonResponse({'status': 'error', 'message': 'Faltan parámetros'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                # Llama al procedimiento almacenado 'KNB_PLANES_ADD_USER' con los parámetros
                cursor.callproc('KNB_PLANES_ADD_USER', [varPlan, varID, varRol, userName])
                result = cursor.fetchall()

                # Verifica si el usuario ya existía en el plan
                existe = result[0][0] if result else 0  # 0 si no existía, 1 si ya existía

                if existe == 0:
                    return JsonResponse({'status': 'success', 'message': 'Usuario agregado correctamente'}, status=200)
                else:
                    return JsonResponse({'status': 'warning', 'message': 'El usuario ya está asignado a este plan'}, status=200)
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


def obtener_miembros_plan(request, plan_id):
    miembros = []

    try:
        with connections['universal'].cursor() as cursor:
            # Llamamos al procedimiento almacenado con el plan_id como parámetro
            cursor.callproc('KNB_PLANES_GET_MIEMBROS', [plan_id])
            rows = cursor.fetchall()

            # Estructura de los resultados según el procedimiento almacenado
            for row in rows:
                miembros.append({
                    'id_usuario': row[0],         # ID del usuario
                    'nombre_completo': row[1],    # Nombre completo del usuario
                    'id_tipo_usuario': row[2],    # ID del tipo de usuario
                    'nombre_tipo_usuario': row[3],# Nombre del tipo de usuario
                    'creado_por': row[4],         # Usuario que asignó al miembro
                    'fecha_creacion': row[5],     # Fecha de creación del registro
                })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # Devolvemos los miembros en formato JSON
    return JsonResponse({'status': 'success', 'data': miembros}, status=200)

def obtener_datos_plan(request, plan_id):
    if request.method == 'GET':
        try:
            with connections['universal'].cursor() as cursor:
                # Llama al procedimiento almacenado con el plan_id como parámetro
                cursor.callproc('KNB_PLANES_DATA', [plan_id])
                result = cursor.fetchall()

                if not result:
                    return JsonResponse({'status': 'error', 'message': 'No se encontraron datos para el plan'}, status=404)

                # Verifica que los índices en `result` están correctos
                plan_data = {
                    'id_plan': result[0][0],
                    'nombre_plan': result[0][1],
                    'descripcion_plan': result[0][2],
                    'id_tipo_plan': result[0][3],
                    'id_area': result[0][4],
                    'fecha_inicio': result[0][5].strftime('%Y-%m-%d') if result[0][5] else '',
                    'fecha_final': result[0][6].strftime('%Y-%m-%d') if result[0][6] else '',
                    'comentario_pausa': result[0][7],
                    'comentario_final': result[0][8]
                }

            return JsonResponse({'status': 'success', 'data': plan_data}, status=200)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


def get_plant_metrics_percentages(request):
    if request.method == 'POST':  # Cambia 'GET' a 'POST'
        plan_id = request.POST.get('plan_id')  # Obtener el plan_id desde el request POST

        # Ejecutar el procedimiento almacenado para obtener el porcentaje de completitud
        with connections['universal'].cursor() as cursor:
            cursor.callproc('KNB_GET_TASK_COMPLETION_PERCENTAGE', [plan_id])
            completion_result = cursor.fetchall()

        # Ejecutar el procedimiento almacenado para obtener el progreso de tiempo
        with connections['universal'].cursor() as cursor:
            cursor.callproc('KNB_GET_TIME_PROGRESS', [plan_id])
            time_progress_result = cursor.fetchall()

        # Retornar los resultados como JSON
        return JsonResponse({
            'completion_percentage': completion_result[0][0] if completion_result else None,
            'time_progress_percentage': time_progress_result[0][0] if time_progress_result else None
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def actualizar_tarea_columna(request):
    if request.method == 'POST':
        id_tarea = request.POST.get('id_tarea')
        nueva_columna = request.POST.get('nueva_columna')
        modificado_por = request.POST.get('creado_por')

        try:
            # Ejecutar el procedimiento almacenado para cambiar la columna
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_TASKS_CHANGE_COLUMNA', [id_tarea, nueva_columna, modificado_por])

            return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


def validar_plan_completo(request):
    if request.method == 'POST':
        # Obtener el id del plan y la fecha final desde la solicitud POST
        plan_id = request.POST.get('plan_id')
        fecha_final = request.POST.get('fecha_final')  # Recibimos la fecha final

        if not plan_id:
            return JsonResponse({'save': 0, 'error': 'El ID del plan es obligatorio.'})

        try:
            # Llamar al procedimiento almacenado para validar el plan
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_PLANES_VALIDATE_COMPLETE', [plan_id])
                result = cursor.fetchall()  # Obtener todos los resultados

            if result:
                sin_tareas, pendientes = result[-1]  # Última fila contiene los conteos
                detalles_pendientes = result[:-1]  # Todas las filas menos la última

                # Validar si hay tareas incompletas
                if sin_tareas == 0 and pendientes == 0:
                    # Si está completo, registrar la fecha final en tu base de datos
                    try:
                        with connections['universal'].cursor() as cursor:
                            cursor.execute("""
                                UPDATE knb_planes
                                SET estado = 5, fecha_final = %s
                                WHERE id_plan = %s
                            """, [fecha_final, plan_id])

                        return JsonResponse({'save': 1, 'message': 'El plan está completo y la fecha ha sido actualizada.'})
                    except Exception as e:
                        return JsonResponse({'save': 0, 'error': 'Error al actualizar el plan: ' + str(e)})

                else:
                    return JsonResponse({
                        'save': 0,
                        'sinTareas': sin_tareas,
                        'pendientes': pendientes,
                        'detalles_pendientes': detalles_pendientes,  # Devolvemos los detalles de las tareas pendientes
                        'message': 'El plan tiene tareas pendientes o no tiene tareas asignadas.'
                    })
            else:
                return JsonResponse({'save': 0, 'error': 'No se pudo validar el plan.'})

        except Exception as e:
            return JsonResponse({'save': 0, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)



def update_estado_plan(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        estado_plan = request.POST.get('estado_plan')
        user_name = request.user.username  # Se obtiene el nombre de usuario autenticado

        response_data = {}

        try:
            # Ejecuta el procedimiento almacenado
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_PLANES_UPDATE_ESTADO', [plan_id, estado_plan, user_name])

            response_data['success'] = True
            response_data['message'] = 'Estado del plan actualizado correctamente'
        except Exception as e:
            response_data['success'] = False
            response_data['error'] = str(e)

        return JsonResponse(response_data)
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    

def obtener_detalles_tarea(request):
    if request.method == 'GET':
        tarea_id = request.GET.get('tarea_id')

        if not tarea_id:
            return JsonResponse({'status': 'fail', 'message': 'Falta el ID de la tarea'}, status=400)

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_GET_TASK_DETAILS', [tarea_id])
                detalles = cursor.fetchall()

                # Construir una lista con los resultados
                detalle_list = []
                for detalle in detalles:
                    detalle_list.append({
                        'id_detalle_tarea': detalle[0],
                        'id_tarea': detalle[1],
                        'detalle': detalle[2],
                        'completado': detalle[3],
                        'estado': detalle[4],
                        'creado_por': detalle[5],
                        'fecha_hora_creado': detalle[6],
                        'modificado_por': detalle[7],
                        'fecha_hora_modificado': detalle[8],
                    })

            return JsonResponse({'status': 'success', 'detalles': detalle_list}, status=200)

        except Exception as e:
            return JsonResponse({'status': 'fail', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'fail', 'message': 'Método no permitido'}, status=405)


def update_task_completed(request):
    if request.method == 'POST':
        id_detalle_tarea = request.POST.get('id_detalle_tarea')
        completado = request.POST.get('completado')
        user_name = request.POST.get('userName')

        if not id_detalle_tarea or completado is None or not user_name:
            return JsonResponse({'save': 0, 'error': 'Datos incompletos'})

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_UPDATE_TASK_COMPLETED', [id_detalle_tarea, completado, user_name])

                return JsonResponse({'save': 1})

        except Exception as e:
            return JsonResponse({'save': 0, 'error': str(e)})
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)


def desactivar_tarea(request):
    if request.method == 'POST':
        id_detalle_tarea = request.POST.get('id_detalle_tarea')
        user_name = request.POST.get('userName')

        if not id_detalle_tarea or not user_name:
            return JsonResponse({'save': 0, 'error': 'Datos incompletos'})

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_TASKS_DETAILS_DEACTIVATE', [id_detalle_tarea, user_name])

                return JsonResponse({'save': 1})

        except Exception as e:
            return JsonResponse({'save': 0, 'error': str(e)})
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)


def create_update_comentario(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        comentario_id = request.POST.get('id_comentario', 0)  # Por defecto 0 para crear
        tarea_id = request.POST.get('id_tarea')  # ID de la tarea
        comentario_texto = request.POST.get('comentario')  # Texto del comentario
        user_name = request.POST.get('user_name')  # Usuario actual
        opcion = int(request.POST.get('opcion'))  # 1 para crear, 2 para actualizar

        # Validación de campos obligatorios
        if not tarea_id or not comentario_texto or not user_name or opcion not in [1, 2]:
            return JsonResponse({'save': 0, 'error': 'Datos inválidos o incompletos.'})

        try:
            # Llamar al procedimiento almacenado
            with connections['universal'].cursor() as cursor:
                cursor.callproc('KNB_COMENTARIOS_CREATE_UPDATE', [comentario_id, tarea_id, comentario_texto, user_name, opcion])
                result = cursor.fetchone()  # Obtener el ID del comentario

            if result:
                return JsonResponse({'save': 1, 'id_comentario': result[0], 'message': 'Comentario guardado correctamente.'})
            else:
                return JsonResponse({'save': 0, 'error': 'No se pudo guardar el comentario.'})

        except Exception as e:
            return JsonResponse({'save': 0, 'error': str(e)})

    return JsonResponse({'error': 'Método no permitido'}, status=405)