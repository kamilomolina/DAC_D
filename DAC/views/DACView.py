from dbfread import DBF
import pyodbc
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connections
from django.http import JsonResponse
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
import time
import pymysql
from ..utils import get_laravel_content, FoxProConnection
import dbf
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict


LOGIN_URL = 'http://3.230.160.184:81/CWS'

#@xframe_options_exempt
def reporte_negativos_super(request):
    id = request.session.get('user_id', '')
    username = request.session.get('userName', '')

    if id == '':
        return HttpResponseRedirect(LOGIN_URL)
    else:
        try:
            dacConn = connections['super']
            with dacConn.cursor() as cursor:
                cursor.callproc("SZ_GET_BODEGAS_ALL")
                column_names = [desc[0] for desc in cursor.description]
                bodegasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            
            # Cierra la conexión
            dacConn.close()
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            return JsonResponse({'error': str(e)})

        context = {
            'id': id,
            'username': username,
            'date1': datetime.now().replace(day=1).strftime('%Y-%m-%d'),
            'date2': datetime.now().strftime('%Y-%m-%d'),
            "bodegas": bodegasData
        }
        return render(request, 'reporte_negativos_super.html', context)

    


def listNegativosSuperSaldo(request):
    date1 = request.POST.get('date1')
    date2 = request.POST.get('date2')

    try:
        dacConn = connections['dac']
        with dacConn.cursor() as cursor:
            cursor.callproc("DAC_SUPER_LIST_NEGAVITOS", [date1, date2])
            column_names = [desc[0] for desc in cursor.description]
            crudData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        dacConn.close()
        
        # Devuelve los resultados como JSON
        return JsonResponse({'data': crudData})
    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})

def getSaldoActualArticulo(request):
    codigo = request.POST.get('codigo')
    bodega = request.POST.get('bodega')

    try:
        dacConn = connections['super']
        with dacConn.cursor() as cursor:
            cursor.callproc("mySP_Dar_Saldo_DISPONIBLE_ArticuloBodega_All", ['1999-01-01', bodega, codigo])
            column_names = [desc[0] for desc in cursor.description]
            crudData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        dacConn.close()
        
        # Devuelve los resultados como JSON
        return JsonResponse({'data': crudData})
    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})








def empresas_competencias(request):
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
        return render(request, 'empresas_competencias.html', context)

    


def listEmpresasCompetencias(request):
    try:
        dacConn = connections['dac']
        with dacConn.cursor() as cursor:
            cursor.callproc("DAC_VP_LIST_EMPRESAS_COMPETENCIAS", ['0'])
            column_names = [desc[0] for desc in cursor.description]
            empresasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        dacConn.close()
        
        # Devuelve los resultados como JSON
        return JsonResponse({'data': empresasData})
    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})




def saveEditEmpresasCompetencias(request):
    start_time = time.time()

    id_competencia = request.POST.get('id_competencia')
    competencia = request.POST.get('competencia')
    descripcion = request.POST.get('descripcion')
    username = request.POST.get('username')
    opcion = request.POST.get('opcion')

    existe = 0

    try:
        dacConn = connections['dac']
        with dacConn.cursor() as cursor:
            cursor.callproc("DAC_VP_SAVE_EDIT_EMPRESAS_COMPETENCIAS", [id_competencia, competencia, descripcion, username, opcion])
            results = cursor.fetchall()

            if results:
                for result in results:
                    
                    existe = result[0]
            else:
                existe = 0
        
        dacConn.close()

        datos = {'save': 1, 'existe': existe}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    end_time = time.time()
    formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
    print("Tiempo de ejecución:", formatted_elapsed_time)
    
    return JsonResponse(datos)



def updateStatusEmpresasCompetencias(request):
    start_time = time.time()

    id_competencia = request.POST.get('id_competencia')
    value = request.POST.get('value')
    username = request.POST.get('username')

    existe = 0

    try:
        dacConn = connections['dac']
        with dacConn.cursor() as cursor:
            cursor.callproc("DAC_VP_STATUS_EMPRESAS_COMPETENCIAS", [id_competencia, value, username])
        
        dacConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    end_time = time.time()
    formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
    print("Tiempo de ejecución:", formatted_elapsed_time)
    
    return JsonResponse(datos)




def motivos_venta_perdida(request):
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
        return render(request, 'motivos_venta_perdida.html', context)


def listMotivosVentasPerdidas(request):
    try:
        dacConn = connections['dac']
        with dacConn.cursor() as cursor:
            cursor.callproc("DAC_VP_LIST_MOTIVOS", ['0', '0'])
            column_names = [desc[0] for desc in cursor.description]
            motivosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        dacConn.close()
        
        # Devuelve los resultados como JSON
        return JsonResponse({'data': motivosData})
    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})



def saveEditMotivosVP(request):
    start_time = time.time()

    id_motivo = request.POST.get('id_motivo')
    motivo = request.POST.get('motivo')
    descripcion = request.POST.get('descripcion')
    tipo = request.POST.get('tipo')
    username = request.POST.get('username')
    opcion = request.POST.get('opcion')

    existe = 0

    try:
        dacConn = connections['dac']
        with dacConn.cursor() as cursor:
            cursor.callproc("DAC_VP_SAVE_EDIT_MOTIVOS", [id_motivo, motivo, descripcion, tipo, username, opcion])
            results = cursor.fetchall()

            if results:
                for result in results:
                    
                    existe = result[0]
            else:
                existe = 0
        
        dacConn.close()

        datos = {'save': 1, 'existe': existe}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    end_time = time.time()
    formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
    print("Tiempo de ejecución:", formatted_elapsed_time)
    
    return JsonResponse(datos)


def updateStatusMotivos(request):
    start_time = time.time()

    id_motivo = request.POST.get('id_motivo')
    value = request.POST.get('value')
    username = request.POST.get('username')

    existe = 0

    try:
        dacConn = connections['dac']
        with dacConn.cursor() as cursor:
            cursor.callproc("DAC_VP_STATUS_MOTIVOS", [id_motivo, value, username])
        
        dacConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    end_time = time.time()
    formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
    print("Tiempo de ejecución:", formatted_elapsed_time)
    
    return JsonResponse(datos)



def ventas_perdidas(request):
    id = request.session.get('user_id', '')
    username = request.session.get('userName', '')


    if id == '':
        return HttpResponseRedirect(LOGIN_URL)
    else:
        try:
            global_nube = connections['global_nube']
            with global_nube.cursor() as cursor:
                cursor.callproc("GS_ACCESO_SUPER", [username])
                results = cursor.fetchall()

                if results:
                    for result in results:
                        
                        acceso = result[0]
                else:
                    acceso = 1
            
            # Cierra la conexión
            global_nube.close()
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            acceso = 1
            return JsonResponse({'error': str(e)})

        try:
            dacConn = connections['dac']
            with dacConn.cursor() as cursor:
                cursor.callproc("DAC_VP_LIST_MOTIVOS", ['1', '1'])
                column_names = [desc[0] for desc in cursor.description]
                motivosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            
            # Cierra la conexión
            dacConn.close()
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            return JsonResponse({'error': str(e)})

        try:
            dacConn = connections['dac']
            with dacConn.cursor() as cursor:
                cursor.callproc("DAC_VP_LIST_EMPRESAS_COMPETENCIAS", ['1'])
                column_names = [desc[0] for desc in cursor.description]
                empresasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            
            # Cierra la conexión
            dacConn.close()
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            return JsonResponse({'error': str(e)})


        context = {
            'id': id,
            'username': username,
            'date1': datetime.now().replace(day=1).strftime('%Y-%m-%d'),
            'date2': datetime.now().strftime('%Y-%m-%d'),
            'acceso': acceso,
            'motivos': motivosData,
            'empresas': empresasData,
        }
        return render(request, 'ventas_perdidas.html', context)



def productosFormato(request):
    formato = request.POST.get('formato')

    try:
        if formato == '2':
            db_alias = 'super'
            procedure_name = 'DAC_MODULARES_LIST_PRODUCTOS'
        else:
            db_alias = 'control_total'
            procedure_name = 'DAC_LIST_PRODUCTOS'

        with connections[db_alias].cursor() as cursor:
            cursor.callproc(procedure_name)
            column_names = [desc[0] for desc in cursor.description]
            productos_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

        return JsonResponse({'productosData': productos_data})
    except Exception as e:
        return JsonResponse({'error': str(e)})


def presentacionesProductoFormato(request):
    formato = request.POST.get('formato')
    producto = request.POST.get('producto')

    try:
        if formato == '2':
            db_alias = 'super'
            procedure_name = 'DAC_VP_PRESENTACIONES_PRODUCTO'
        else:
            db_alias = 'control_total'
            procedure_name = 'DAC_VP_PRESENTACIONES_PRODUCTO'

        with connections[db_alias].cursor() as cursor:
            cursor.callproc(procedure_name, [producto])
            column_names = [desc[0] for desc in cursor.description]
            presentacionesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

        return JsonResponse({'presentacionesData': presentacionesData})
    except Exception as e:
        return JsonResponse({'error': str(e)})



def getDataPresentacionAlmacen(request):
    start_time = time.time()

    formato = request.POST.get('formato')
    almacen = request.POST.get('almacen')
    presentacion = request.POST.get('presentacion')
    producto = request.POST.get('producto')
    cliente = request.POST.get('cliente')


    try:
        if formato == '2':
            db_alias = 'super'
            procedure_name = 'DAC_VP_DATA_X_PRODUCTO_CLIENTE'
        else:
            db_alias = 'control_total'
            procedure_name = 'DAC_VP_DATA_X_PRODUCTO_CLIENTE'

        with connections[db_alias].cursor() as cursor:
            cursor.callproc(procedure_name, [cliente, almacen, presentacion, producto])
            results = cursor.fetchall()

            if results:
                for result in results:
                    
                    existencia = result[0]
                    precio_max = result[1]
                    precio_min = result[2]
                    subgrupo = result[3]
                    marca = result[4]
                    fecha_llegada = result[5]
            else:
                existencia = 0
                precio_max = 0
                precio_min = 0
                subgrupo = 0
                marca = 0
                fecha_llegada = ''
        
        connections[db_alias].close()

        datos = {'save': 1, 'existencia': existencia, 'precio_max': precio_max, 'precio_min': precio_min, 'subgrupo': subgrupo, 'marca': marca, 'fecha_llegada': fecha_llegada}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    end_time = time.time()
    formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
    print("Tiempo de ejecución:", formatted_elapsed_time)
    
    return JsonResponse(datos)




def saveVentaPerdida(request):
    start_time = time.time()

    id_cliente = request.POST.get('id_cliente')
    nombre_cliente = request.POST.get('nombre_cliente')
    id_equivalencia_x_categoria = request.POST.get('id_equivalencia_x_categoria')
    id_producto = request.POST.get('id_producto')
    nombre_producto = request.POST.get('nombre_producto')
    presentacion = request.POST.get('presentacion')
    id_almacen = request.POST.get('id_almacen')
    almacen = request.POST.get('almacen')
    cantidad = request.POST.get('cantidad')
    existencia = request.POST.get('existencia')
    precio = request.POST.get('precio')
    precio_max = request.POST.get('precio_max')
    precio_min = request.POST.get('precio_min')
    id_motivo = request.POST.get('id_motivo')
    id_competencia = request.POST.get('id_competencia')
    nombre_competencia = request.POST.get('nombre_competencia')
    precio_competencia = request.POST.get('precio_competencia')
    comentario = request.POST.get('comentario')
    id_empresa = request.POST.get('id_empresa')
    sistema = request.POST.get('sistema')
    subgrupo = request.POST.get('subgrupo')
    marca = request.POST.get('marca')

    username = request.POST.get('user_name')

    try:
        dacConn = connections['dac']
        with dacConn.cursor() as cursor:
            cursor.callproc("DAC_VP_INSERT_VENTA_PERDIDA", [
                id_cliente,
                nombre_cliente,
                id_equivalencia_x_categoria,
                nombre_producto,
                presentacion,
                id_almacen,
                almacen,
                cantidad,
                existencia,
                precio,
                precio_max,
                precio_min,
                id_motivo,
                id_competencia,
                nombre_competencia,
                precio_competencia,
                comentario,
                username,
                id_empresa,
                sistema,
                subgrupo,
                marca,
                id_producto
            ])
        
        dacConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    end_time = time.time()
    formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
    print("Tiempo de ejecución:", formatted_elapsed_time)
    
    return JsonResponse(datos)



def reporte_ventas_perdidas(request):
    id = request.session.get('user_id', '')
    username = request.session.get('userName', '')

    if id == '':
        return HttpResponseRedirect(LOGIN_URL)
    else:
        try:
            global_nube = connections['global_nube']
            with global_nube.cursor() as cursor:
                cursor.callproc("GS_ACCESO_SUPER", [username])
                results = cursor.fetchall()

                if results:
                    for result in results:
                        
                        acceso = result[0]
                else:
                    acceso = 1
            
            # Cierra la conexión
            global_nube.close()
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            acceso = 1
            return JsonResponse({'error': str(e)})

        try:
            dacConn = connections['dac']
            with dacConn.cursor() as cursor:
                cursor.callproc("DAC_VP_LIST_MOTIVOS", ['1', '0'])
                column_names = [desc[0] for desc in cursor.description]
                motivosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            
            # Cierra la conexión
            dacConn.close()
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            return JsonResponse({'error': str(e)})

        try:
            dacConn = connections['dac']
            with dacConn.cursor() as cursor:
                cursor.callproc("DAC_VP_LIST_EMPRESAS_COMPETENCIAS", ['1'])
                column_names = [desc[0] for desc in cursor.description]
                empresasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            
            # Cierra la conexión
            dacConn.close()
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            return JsonResponse({'error': str(e)})


        context = {
            'id': id,
            'username': username,
            'date1': datetime.now().replace(day=1).strftime('%Y-%m-%d'),
            'date2': datetime.now().strftime('%Y-%m-%d'),
            'acceso': acceso,
            'motivos': motivosData,
            'empresas': empresasData,
        }
        return render(request, 'reporte_ventas_perdidas.html', context)



def data_reporte_venta_perdida(request):
    formato = request.POST.get('formato')
    date1 = request.POST.get('date1')
    date2 = request.POST.get('date2')

    try:
        dacConn = connections['dac']
        with dacConn.cursor() as cursor:
            cursor.callproc("DAC_VP_REPORTE_VENTAS_PERDIDAS", [date1, date2, formato])
            column_names = [desc[0] for desc in cursor.description]
            vpData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        dacConn.close()


        if formato == '1':
            dacConn = connections['dac']
            with dacConn.cursor() as cursor:
                cursor.callproc("DAC_VP_REPORTE_VENTA_PERDIDA_APP", [date1, date2])
                column_names = [desc[0] for desc in cursor.description]
                vpCTData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            
            # Cierra la conexión
            dacConn.close()

            ventaPerdidaData = vpData + vpCTData
        else:
            ventaPerdidaData = vpData



        return JsonResponse({'data': ventaPerdidaData})
    except Exception as e:
        return JsonResponse({'error': str(e)})


def dashboardTicketit(request):
    url = 'http://localhost/DAC/public/admin/gerencia/indicadores/04/2024'
    #url = 'http://localhost/TICKETIT/public/admin/dashboard'
    laravel_content = get_laravel_content(url)
    return render(request, 'dashboardTicketit.html', {'laravel_content': laravel_content})


@csrf_exempt
def consultar_facturas(request, date1, date2):
    try:
        # Convertir fechas al formato MM/DD/YYYY para FoxPro
        date1 = datetime.strptime(date1, "%Y-%m-%d").strftime("%m/%d/%Y")
        date2 = datetime.strptime(date2, "%Y-%m-%d").strftime("%m/%d/%Y")

        # Crear conexión a FoxPro
        fox_conn = FoxProConnection(db_path=r"C:\\CONTROLTOTAL\\Base")
        fox_conn.connect()

        # Construir y ejecutar el query
        cursor = fox_conn.conn.cursor()
        query = "SELECT * FROM ft_facturas WHERE fecha_ingreso >= CTOD('{}')".format(date1)
        cursor.execute(query)

        # Obtener nombres de las columnas de forma dinámica
        column_names = [desc[0] for desc in cursor.description]

        # Crear la lista de diccionarios con los resultados
        results = cursor.fetchall()
        datos = [dict(zip(column_names, row)) for row in results]

        # Cerrar conexión
        fox_conn.disconnect()

        # Retornar los datos como JSON
        return JsonResponse(datos, safe=False)

    except Exception as e:
        return JsonResponse({"error": "Error al consultar facturas: " + str(e)}, status=500)


@csrf_exempt
def consultar_facturas_prg(request):
    try:
        # Crear conexión
        fox_conn = FoxProConnection(db_path=r"C:\CONTROLTOTAL\Base")
        fox_conn.connect()

        # Ruta del PRG
        prg_path = r"C:\CONTROLTOTAL\Base\sp_facturas.prg"

        # Ejecutar el PRG sin parámetros
        results = fox_conn.execute_procedure2(prg_path)

        # Definir nombres de las columnas manualmente
        column_names = ['id_factura', 'numero_factura', 'fecha_impreso', 'nombre_cliente', 'costo', 'total']
        datos = [dict(zip(column_names, row)) for row in results]

        # Cerrar la conexión
        fox_conn.disconnect()

        return JsonResponse(datos, safe=False)
    except Exception as e:
        return JsonResponse({"error": "Error al consultar facturas: " + str(e)}, status=500)



@csrf_exempt
def actualizar_id_almacen_a(request, id_almacen, nuevo_id_almacen_a):
    try:
        # Convertir los parámetros a enteros antes de pasarlos, si son numéricos
        id_almacen = int(id_almacen)
        nuevo_id_almacen_a = int(nuevo_id_almacen_a)

        # Conectar y ejecutar el PRG
        fox_conn = FoxProConnection(db_path=r"C:\CONTROLTOTAL\Base")
        fox_conn.connect()
        prg_path = r"C:\CONTROLTOTAL\Base\sp_update_almacen.prg"  # Ruta completa del PRG

        # Construir la consulta de manera dinámica
        query = "UPDATE cat_almacenes SET id_almacen_a = {} WHERE id_almacen = {}".format(nuevo_id_almacen_a, id_almacen)
        
        # Ejecutar el comando UPDATE directamente
        cursor = fox_conn.conn.cursor()
        cursor.execute(query)

        # Confirmar (commit) los cambios para asegurar que se guarden
        fox_conn.conn.commit()

        # Desconectar la conexión
        fox_conn.disconnect()

        # Retornar un mensaje de éxito
        return JsonResponse({"status": "Actualización exitosa"}, status=200)

    except Exception as e:
        return JsonResponse({"error": "Error al actualizar id_almacen_a: " + str(e)}, status=500)