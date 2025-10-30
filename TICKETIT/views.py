from django.shortcuts import render
from django.http import HttpResponse
from django.db import connections
from django.http import JsonResponse
from datetime import datetime
import time

LOGIN_URL = 'http://3.230.160.184:81/CWS'

#@xframe_options_exempt
def notificacion_correos_reportes(request):    
    id = request.session.get('user_id', '')
    username = request.session.get('userName', '')

    if id == '':
        return HttpResponseRedirect(LOGIN_URL)
    else:
        try:
            global_nube = connections['global_nube']
            with global_nube.cursor() as cursor:
                cursor.callproc("GS_LIST_MODULOS")
                column_names = [desc[0] for desc in cursor.description]
                modulosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            
            # Cierra la conexión
            global_nube.close()
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            return JsonResponse({'error': str(e)})

        context = {
            'id': id,
            'username': username,
            'date1': datetime.now().replace(day=1).strftime('%Y-%m-%d'),
            'date2': datetime.now().strftime('%Y-%m-%d'),
            'modulos': modulosData
        }
        return render(request, 'notificacionCorreos.html', context)



def menus_x_modulo(request):
    modulo = request.POST.get('modulo')

    try:
        global_nube = connections['global_nube']
        with global_nube.cursor() as cursor:
            cursor.callproc("GS_LIST_MENUS_X_MODULO", [modulo])
            column_names = [desc[0] for desc in cursor.description]
            accesosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        global_nube.close()

        return JsonResponse({'accesosData': accesosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})



def correos_x_acceso(request):
    modulo = request.POST.get('modulo')
    acceso = request.POST.get('acceso')

    try:
        sdkConn = connections['sdkConn']
        with sdkConn.cursor() as cursor:
            cursor.callproc("SDK_CORREOS_X_REPORTE", [acceso, modulo])
            column_names = [desc[0] for desc in cursor.description]
            correosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        sdkConn.close()
        
        # Devuelve los resultados como JSON
        return JsonResponse({'data': correosData})
    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})



def correos_not_acceso(request):
    modulo = request.POST.get('modulo')
    acceso = request.POST.get('acceso')

    try:
        sdkConn = connections['sdkConn']
        with sdkConn.cursor() as cursor:
            cursor.callproc("SDK_CORREOS_NOT_REPORTE", [acceso, modulo])
            column_names = [desc[0] for desc in cursor.description]
            correosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        sdkConn.close()
        
        # Devuelve los resultados como JSON
        return JsonResponse({'data': correosData})
    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})



def add_delete_correo(request):
    start_time = time.time()

    registro_id = request.POST.get('id')
    modulo = request.POST.get('modulo')
    acceso = request.POST.get('acceso')
    username = request.POST.get('user_name')
    opcion = request.POST.get('opcion')

    try:
        sdkConn = connections['sdkConn']
        with sdkConn.cursor() as cursor:
            cursor.callproc("SDK_CORREOS_ADD_DELETE", [registro_id, modulo, acceso, username, opcion])
        
        sdkConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    end_time = time.time()
    formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
    print("Tiempo de ejecución:", formatted_elapsed_time)
    
    return JsonResponse(datos)


#@xframe_options_exempt
def environments_sistemas(request):    
    id = request.session.get('user_id', '')
    username = request.session.get('userName', '')

    if id == '':
        return HttpResponseRedirect(LOGIN_URL)
    else:
        context = {
            'id': id,
            'username': username,
            'date1': datetime.now().replace(day=1).strftime('%Y-%m-%d'),
            'date2': datetime.now().strftime('%Y-%m-%d')
        }
        return render(request, 'environments_sistemas.html', context)


def sistemas_urls(request):
    try:
        globalConn = connections['global_nube']
        with globalConn.cursor() as cursor:
            cursor.callproc("GS_LIST_SISTEMAS_URL")
            column_names = [desc[0] for desc in cursor.description]
            sistemasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        globalConn.close()
        
        # Devuelve los resultados como JSON
        return JsonResponse({'data': sistemasData})
    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})