from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json 
from datetime import datetime
from django.db import DatabaseError, connections
from django.utils import timezone
from django.db import connections
from django.views.decorators.clickjacking import xframe_options_exempt


# Create your views here.
def obtener_motivos_ventas_perdidas(request):
    from .models import VentasPerdidasMotivos
    combustibles = VentasPerdidasMotivos.objects.exclude(estado=3).values()
    lista_combustibles = list(combustibles)  # Convertir QuerySet a una lista de diccionarios
    return JsonResponse({"data": lista_combustibles})

def obtener_empresas_competencias(request):
    from .models import EmpresasCompetencias
    combustibles = EmpresasCompetencias.objects.exclude(estado=3).values()
    lista_combustibles = list(combustibles)  # Convertir QuerySet a una lista de diccionarios
    return JsonResponse({"data": lista_combustibles})

def obtener_ventas_perdidas(request):
    try:
        conexion_global_nube = connections['dac']
        with conexion_global_nube.cursor() as cursor:
            cursor.execute("CALL VENTAS_P_OBTENER_VENTAS_PERDIDAS_GSCM()")
            columnas = [col[0] for col in cursor.description]
            almacenes = [
                dict(zip(columnas, ((value.decode('utf-8') if isinstance(value, bytes) else value) for value in row)))
                for row in cursor.fetchall()
            ]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'data': almacenes})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
def vista_ventas_perdidas(request):
    return render(request, 'modal_ventas_perdidas.html')

@csrf_exempt
def vista_ventas_perdidas_all(request):
    return render(request, 'md_ventas_perdidas.html')

@xframe_options_exempt
@csrf_exempt
def vista_agregar_venta_perdida(request):
    return render(request, 'crear_venta_perdida.html')

@xframe_options_exempt
@csrf_exempt
def vista_configuracion_venta_perdida(request):
    return render(request, 'configuracion_venta_perdida.html')

@xframe_options_exempt
@csrf_exempt
def vista_reporte_ventas_perdidas(request):
    return render(request, 'reporte_venta_perdida.html')

@csrf_exempt
def guardar_motivo(request):
    from .models import VentasPerdidasMotivos
  
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))

        nombre_motivo = data.get('nombre_motivo')
        descripcion_motivo = data.get('descripcion_motivo') 
        tipo = data.get('tipo')
        estado = 1

        # Crear un nuevo registro
        motivo = VentasPerdidasMotivos(
            nombre_motivo=nombre_motivo,
            descripcion_motivo=descripcion_motivo,  
            tipo=tipo, 
            estado = estado 
        )
        motivo.save()

        return JsonResponse({'message': 'Creado con éxito'})

    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def editar_motivo(request):
    from .models import VentasPerdidasMotivos
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))

        id_motivo = data.get('id_motivo')
        nombre_motivo = data.get('nombre_motivo')
        descripcion_motivo = data.get('descripcion_motivo')
        tipo = data.get('tipo')
        estado = 2

        try:
            motivo = VentasPerdidasMotivos.objects.get(id_motivo=id_motivo)
            motivo.nombre_motivo = nombre_motivo
            motivo.descripcion_motivo = descripcion_motivo
            motivo.tipo = tipo
            motivo.estado = estado
            motivo.fecha_hora_modificado = timezone.now()  
            motivo.save()

            return JsonResponse({'message': 'Actualizado con éxito'})
        except VentasPerdidasMotivos.DoesNotExist:
            return JsonResponse({'error': 'Motivo no encontrado'}, status=404)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def borrar_motivo(request):
    from .models import VentasPerdidasMotivos
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        
        id_motivo = data.get('id_motivo')
        
        try:
            # Cambiar el estado del registro existente
            motivo = VentasPerdidasMotivos.objects.get(id_motivo=id_motivo)
            motivo.estado = 3  # Cambia el estado a 3
            motivo.fecha_hora_modificado = timezone.now()  # Establece la fecha y hora actual
            motivo.save()

            return JsonResponse({'message': 'Motivo borrado con éxito (estado cambiado a 3)'})
        except VentasPerdidasMotivos.DoesNotExist:
            return JsonResponse({'error': 'Motivo no encontrado'}, status=404)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

#--------------------------------------------VENTAS PERDIDAS ---------------------------------------------

def obtener_almacenes(request):
    try:
        conexion_global_nube = connections['super']
        with conexion_global_nube.cursor() as cursor:
            cursor.execute("CALL DAC_GET_ALL_ALMACENES_VENTA()")
            columnas = [col[0] for col in cursor.description]
            almacenes = [
                dict(zip(columnas, ((value.decode('utf-8') if isinstance(value, bytes) else value) for value in row)))
                for row in cursor.fetchall()
            ]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'almacen': almacenes})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)

def obtener_almacenes_dc(request):
    try:
        ctConn = connections['control_total']
        with ctConn.cursor() as cursor:
            cursor.callproc("DAC_GET_ALL_ALMACENES_VENTA", ['999'])
            column_names = [desc[0] for desc in cursor.description] 
            almacenesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'almacenesData': almacenesData})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)

def obtener_productos_supermercado2(request, idCliente, idAlmacen):
    try:
        conexion_global_nube = connections['control_total']
        with conexion_global_nube.cursor() as cursor:
            cursor.execute("CALL DAC_INFORMACION_PRODUCTOS_PRECIOS_EXISTENCIA_GSCM(%s, %s)", [idCliente, idAlmacen])
            columnas = [col[0] for col in cursor.description]
            productos = [
                dict(zip(columnas, ((value.decode('utf-8') if isinstance(value, bytes) else value) for value in row)))
                for row in cursor.fetchall()
            ]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'productos': productos})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)    
    
def obtener_segmentos(request):
    try:
        conexion_global_nube = connections['control_total']
        with conexion_global_nube.cursor() as cursor:
            cursor.execute("CALL DAC_GET_SEGMENTOS()")
            columnas = [col[0] for col in cursor.description]
            segmentos = [
                dict(zip(columnas, ((value.decode('utf-8') if isinstance(value, bytes) else value) for value in row)))
                for row in cursor.fetchall()
            ]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'data': segmentos})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)

def obtener_grupo(request):
    try:
        conexion_global_nube = connections['control_total']
        with conexion_global_nube.cursor() as cursor:
            cursor.execute("CALL DAC_GET_ALL_GRUPOS()")
            columnas = [col[0] for col in cursor.description]
            segmentos = [
                dict(zip(columnas, ((value.decode('utf-8') if isinstance(value, bytes) else value) for value in row)))
                for row in cursor.fetchall()
            ]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'data': segmentos})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)
    
def obtener_subgrupos(request):
    try:
        conexion_global_nube = connections['control_total']
        with conexion_global_nube.cursor() as cursor:
            cursor.execute("CALL DAC_GET_ALL_SUBGRUPOS()")
            columnas = [col[0] for col in cursor.description]
            segmentos = [
                dict(zip(columnas, ((value.decode('utf-8') if isinstance(value, bytes) else value) for value in row)))
                for row in cursor.fetchall()
            ]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'data': segmentos})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)

def obtener_marcas(request):
    try:
        conexion_global_nube = connections['control_total']
        with conexion_global_nube.cursor() as cursor:
            cursor.execute("CALL DACD_GET_ALL_MARCAS()")
            columnas = [col[0] for col in cursor.description]
            segmentos = [
                dict(zip(columnas, ((value.decode('utf-8') if isinstance(value, bytes) else value) for value in row)))
                for row in cursor.fetchall()
            ]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'data': segmentos})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)

def obtener_categoria(request):
    try:
        conexion_global_nube = connections['control_total']
        with conexion_global_nube.cursor() as cursor:
            cursor.execute("CALL DAC_GET_ALL_CATEGORIAS()")
            columnas = [col[0] for col in cursor.description]
            segmentos = [
                dict(zip(columnas, ((value.decode('utf-8') if isinstance(value, bytes) else value) for value in row)))
                for row in cursor.fetchall()
            ]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'data': segmentos})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)
        
def obtener_clientes(request):
    try:
        conexion_global_nube = connections['control_total']
        with conexion_global_nube.cursor() as cursor:
            cursor.execute("CALL DAC_OBTENER_CLIENTES")
            columnas = [col[0] for col in cursor.description]
            clientes = [
                dict(zip(columnas, ((value.decode('utf-8') if isinstance(value, bytes) else value) for value in row)))
                for row in cursor.fetchall()
            ]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'clientes': clientes})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)
    
def obtener_clientes_supermercado(request):
    try:
        conexion_global_nube = connections['super']
        with conexion_global_nube.cursor() as cursor:
            cursor.execute("CALL DAC_GET_ALL_CLIENTES")
            columnas = [col[0] for col in cursor.description]
            clientes = [
                dict(zip(columnas, ((value.decode('utf-8') if isinstance(value, bytes) else value) for value in row)))
                for row in cursor.fetchall()
            ]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'clientes': clientes})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)
    
def obtener_productos_distribuidora(request, idCliente):
    try:
        conexion_global_nube = connections['control_total']
        with conexion_global_nube.cursor() as cursor:
            cursor.execute("CALL DACD_INFORMACION_PRODUCTOS_PRECIOS_EXISTENCIA(%s)", [idCliente])
            columnas = [col[0] for col in cursor.description]
            productos = [
                dict(zip(columnas, ((value.decode('utf-8') if isinstance(value, bytes) else value) for value in row)))
                for row in cursor.fetchall()
            ]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'productos': productos})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)

def obtener_productos_supermercado(request, idCliente, idAlmacen):
    try:
        conexion_global_nube = connections['super']
        with conexion_global_nube.cursor() as cursor:
            cursor.execute("CALL DAC_INFORMACION_PRODUCTOS_PRECIOS_EXISTENCIA_GSCM(%s, %s)", [idCliente, idAlmacen])
            columnas = [col[0] for col in cursor.description]
            productos = [
                dict(zip(columnas, ((value.decode('utf-8') if isinstance(value, bytes) else value) for value in row)))
                for row in cursor.fetchall()
            ]

        # Devolver un JSON con los datos de los usuarios
        return JsonResponse({'productos': productos})
    except Exception as e:
        # Manejo de la excepción
        return JsonResponse({'error': str(e)}, status=500)    
    
@csrf_exempt
def editar_venta_perdida(request, id_venta_perdida):
    from .models import VentaPerdida
    if request.method == 'POST':
        try:
            # Buscar la venta perdida por ID
            venta_perdida = VentaPerdida.objects.get(pk=id_venta_perdida)
        except VentaPerdida.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Venta perdida no encontrada'}, status=404)
        
        datos = json.loads(request.body.decode('utf-8'))

        # Lógica para convertir valores y manejar fechas, similar a la función de almacenar
        def convertir_a_entero(valor, predeterminado=0):
            try:
                return int(valor) if valor not in ['', None] else predeterminado
            except ValueError:
                return predeterminado
        
        id_empresa = convertir_a_entero(datos.get('id_empresa'))
        if id_empresa == 1:
            id_empresa = 2
        elif id_empresa == 2:
            id_empresa = 1

        fecha_input = datos.get('fecha')
        if not fecha_input:
            fecha = datetime.today().date()
        else:
            try:
                fecha = datetime.strptime(fecha_input, '%Y-%m-%d').date()
            except ValueError:
                fecha = datetime.today().date()

        # Actualizar campos del objeto venta_perdida
        venta_perdida.id_equivalencia_x_categoria = convertir_a_entero(datos.get('presentacion_id'))
        venta_perdida.nombre_producto = datos.get('nombre_producto_id')
        venta_perdida.id_cliente = convertir_a_entero(datos.get('cliente_select_id'))
        venta_perdida.nombre_cliente = datos.get('cliente_select_text', 'NO APLICA')
        venta_perdida.precio = datos.get('precio', '0')
        venta_perdida.precio_min = datos.get('precio_min', '0')
        venta_perdida.id_motivo = convertir_a_entero(datos.get('nombre_motivo_id'))
        venta_perdida.id_competencia = convertir_a_entero(datos.get('select_nombre_competencia_id'))
        venta_perdida.nombre_competencia = datos.get('select_nombre_competencia_text', 'NO APLICA')
        venta_perdida.comentario = datos.get('comentario', 'NO APLICA')
        venta_perdida.fecha = fecha
        venta_perdida.estado = convertir_a_entero(datos.get('estado'), predeterminado=1)
        venta_perdida.creado_por = convertir_a_entero(datos.get('creado_por'), predeterminado=1)
        venta_perdida.cantidad = convertir_a_entero(datos.get('cantidad'))
        venta_perdida.id_ruta = convertir_a_entero(datos.get('id_ruta'))
        venta_perdida.nombre_ruta = datos.get('nombre_ruta', 'NO APLICA')
        venta_perdida.precio_competencia = datos.get('precio_competencia', '0')
        venta_perdida.id_empresa = id_empresa
        venta_perdida.presentacion = datos.get('presentacion_text', 'NO APLICA')

        venta_perdida.save()

        return JsonResponse({'status': 'success', 'message': 'Venta perdida actualizada correctamente'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


@csrf_exempt
def almacenar_venta_perdida(request):
    from .models import VentaPerdida
    if request.method == 'POST':
        datos = json.loads(request.body.decode('utf-8'))

        # Convertir valores vacíos o placeholders a valores predeterminados y asegurar el tipo correcto
        def convertir_a_entero(valor, predeterminado=0):
            try:
                return int(valor) if valor not in ['', None] else predeterminado
            except ValueError:
                return predeterminado
        
        id_empresa = convertir_a_entero(datos.get('id_empresa'))

        # Cambiar el valor de id_empresa
        if id_empresa == 1:
            id_empresa = 2
        elif id_empresa == 2:
            id_empresa = 1

        print(datos)
        # Intenta convertir la fecha, si falla o está vacía, usa la fecha de hoy.
        fecha_input = datos.get('fecha')
        if not fecha_input:  # Checa si la fecha está vacía o es None
            fecha = datetime.today().date()  # Fecha de hoy como objeto date
        else:
            try:
                # Intenta parsear la fecha proporcionada
                fecha = datetime.strptime(fecha_input, '%Y-%m-%d').date()
            except ValueError:
                # Si falla el parseo, usa la fecha de hoy
                fecha = datetime.today().date()
        

        venta_perdida = VentaPerdida(
            id_equivalencia_x_categoria=convertir_a_entero(datos.get('presentacion_id')),
            nombre_producto=datos.get('nombre_producto_id'),
            id_pedido=0,
            id_cliente=convertir_a_entero(datos.get('cliente_select_id')),
            nombre_cliente=datos.get('cliente_select_text', 'NO APLICA'),
            precio=datos.get('precio', '0'),
            precio_min=datos.get('precio_min', '0'),
            id_motivo=convertir_a_entero(datos.get('nombre_motivo_id')),
            id_competencia=convertir_a_entero(datos.get('select_nombre_competencia_id')),
            nombre_competencia=datos.get('select_nombre_competencia_text', 'NO APLICA'),
            comentario=datos.get('comentario', 'NO APLICA'),
            fecha=fecha,  # Asegúrate de manejar adecuadamente las fechas
            estado=convertir_a_entero(datos.get('estado'), predeterminado=1),  # Asumiendo un valor predeterminado
            creado_por=convertir_a_entero(datos.get('creado_por'), predeterminado=1),  # Asumiendo un valor predeterminado
            cantidad=convertir_a_entero(datos.get('cantidad')),
            id_ruta=convertir_a_entero(datos.get('id_ruta')),
            nombre_ruta=datos.get('nombre_ruta', 'NO APLICA'),
            precio_competencia=datos.get('precio_competencia', '0'),
            id_empresa=id_empresa,
            presentacion=datos.get('presentacion_text', 'NO APLICA'),
            grupo=datos.get('grupo', 'NO APLICA'),
            subgrupo=datos.get('subGrupo', 'NO APLICA'),  # Asegúrate de que la clave coincide con la enviada en JSON
            categoria=datos.get('categoria', 'NO APLICA'),
            marca=datos.get('marca', 'NO APLICA'),
        )
        
        venta_perdida.save()
        
        return JsonResponse({'status': 'success', 'message': 'Venta perdida almacenada correctamente'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

@csrf_exempt
def obtener_ventas_perdidas_filtradas(request):
    if request.method == 'POST':
        try:
          
            datos = json.loads(request.body.decode('utf-8'))

            print(datos)
    
            # Asegúrate de que los datos recibidos son correctos y completos
            grupo = datos.get('grupo')
            subgrupo = datos.get('subgrupo')
            categoria = datos.get('categoria')
            marca = datos.get('marca')
            id_empresa = datos.get('empresas')
            # Asumiendo que segmento siempre es -1 para esta operación
            segmento = -1

            conexion_global_nube = connections['dac']
            with conexion_global_nube.cursor() as cursor:
                cursor.callproc('VENTASP_OBTENER_VENTASP_FILTRO', [segmento, categoria, marca, grupo, id_empresa, subgrupo])
                columnas = [col[0] for col in cursor.description]
                resultados = [
                    dict(zip(columnas, (value.decode('utf-8') if isinstance(value, bytes) else value for value in row)))
                    for row in cursor.fetchall()
                ]
            print(resultados) 

            return JsonResponse({'data': resultados})

        except ValueError as e:
            # Error al analizar JSON
            return JsonResponse({'error': 'Error al analizar JSON lvp: ' + str(e)}, status=400)

        except DatabaseError as e:
            # Error de base de datos
            return JsonResponse({'error': 'Error de base de datos lvp: ' + str(e)}, status=500)

        except Exception as e:
            # Otros errores no capturados explícitamente
            return JsonResponse({'error': 'Error no especificado lvp: ' + str(e)}, status=500)

    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
def obtener_ventas_perdidas_filtradas_super(request):
    if request.method == 'POST':
        try:
          
            datos = json.loads(request.body.decode('utf-8'))

            print(datos)
    
            # Asegúrate de que los datos recibidos son correctos y completos
            grupo = datos.get('grupo')
            subgrupo = datos.get('subgrupo')
            categoria = datos.get('categoria')
            marca = datos.get('marca')
            # Asumiendo que segmento siempre es -1 para esta operación

            conexion_global_nube = connections['dac']
            with conexion_global_nube.cursor() as cursor:
                cursor.callproc('VENTAS_P_PRODUCTOS_SUPER', [grupo, subgrupo, categoria, marca])
                columnas = [col[0] for col in cursor.description]
                resultados = [
                    dict(zip(columnas, (value.decode('utf-8') if isinstance(value, bytes) else value for value in row)))
                    for row in cursor.fetchall()
                ]
            print(resultados) 

            return JsonResponse({'data': resultados})

        except ValueError as e:
            # Error al analizar JSON
            return JsonResponse({'error': 'Error al analizar JSON: ' + str(e)}, status=400)

        except DatabaseError as e:
            # Error de base de datos
            return JsonResponse({'error': 'Error de base de datos: ' + str(e)}, status=500)

        except Exception as e:
            # Otros errores no capturados explícitamente
            return JsonResponse({'error': 'Error no especificado: ' + str(e)}, status=500)

    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)


@csrf_exempt
def obtener_ventas_perdidas_filtradas_supermercado(request):
    if request.method == 'POST':
        try:
            datos = json.loads(request.body.decode('utf-8'))

            print(datos)
    
            # Asegúrate de que los datos recibidos son correctos y completos
            grupo = datos.get('grupo')
            subgrupo = datos.get('subgrupo')
            categoria = datos.get('categoria')
            marca = datos.get('marca')
            id_empresa = datos.get('empresas')

            conexion_global_nube = connections['dac']
            with conexion_global_nube.cursor() as cursor:
                cursor.callproc('VENTAS_P_PRODUCTOS_SUPER', [grupo, subgrupo, categoria, marca])
                columnas = [col[0] for col in cursor.description]
                resultados = [
                    dict(zip(columnas, (value.decode('utf-8') if isinstance(value, bytes) else value for value in row)))
                    for row in cursor.fetchall()
                ]
            print(resultados) 

            return JsonResponse({'data': resultados})

        except ValueError as e:
            # Error al analizar JSON
            return JsonResponse({'error': 'Error al analizar JSON: ' + str(e)}, status=400)

        except DatabaseError as e:
            # Error de base de datos
            return JsonResponse({'error': 'Error de base de datos: ' + str(e)}, status=500)

        except Exception as e:
            # Otros errores no capturados explícitamente
            return JsonResponse({'error': 'Error no especificado: ' + str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)


#--------------------------------------------- EMPRESAS COMPETENCIAS ---------------------------------------------------------
@csrf_exempt
def guardar_empresa_competencia(request):
    from .models import EmpresasCompetencias
    try:
        # Decodificar los datos JSON de la solicitud.
        datos = json.loads(request.body.decode('utf-8'))
        print(datos)
        # Crear una nueva instancia del modelo.
        nueva_competencia = EmpresasCompetencias(
            nombre_competencia=datos.get('nombre_competencia'),
            descripcion=datos.get('descripcion'),
            estado=1,
            creado_por=request.user.username if request.user.is_authenticated else 'Anónimo',  # O ajusta según sea necesario.
            fecha_hora_creado=timezone.now()
        )

        # Guardar la instancia en la base de datos.
        nueva_competencia.save()

        # Devolver una respuesta de éxito.
        return JsonResponse({'status': 'success', 'message': 'Empresa competencia guardada correctamente.'})

    except json.JSONDecodeError:
        # Manejar el error de decodificación JSON.
        return JsonResponse({'status': 'error', 'message': 'Datos inválidos.'}, status=400)
    except Exception as e:
        # Manejar cualquier otro error.
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@csrf_exempt    
def editar_empresa_competencia(request, id_competencia):
    from .models import EmpresasCompetencias
    try:
        # Decodificar los datos JSON de la solicitud.
        datos = json.loads(request.body.decode('utf-8'))

        # Buscar la instancia del modelo por su ID.
        competencia = EmpresasCompetencias.objects.get(id_competencia=id_competencia)

        # Actualizar los campos con los nuevos datos.
        competencia.nombre_competencia = datos.get('nombre_competencia', competencia.nombre_competencia)
        competencia.descripcion = datos.get('descripcion', competencia.descripcion)
        competencia.modificado_por = request.user.username if request.user.is_authenticated else 'Anónimo'
        competencia.fecha_hora_modificado = timezone.now()

        # Guardar los cambios en la base de datos.
        competencia.save()

        # Devolver una respuesta de éxito.
        return JsonResponse({'status': 'success', 'message': 'Empresa competencia actualizada correctamente.'})

    except EmpresasCompetencias.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Empresa competencia no encontrada.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Datos inválidos.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@csrf_exempt 
def eliminar_empresa_competencia(request, id_competencia):
    from .models import EmpresasCompetencias
    try:
        # Decodificar los datos JSON de la solicitud.
        datos = json.loads(request.body.decode('utf-8'))
        id_competencia = datos.get('id_competencia')
        # Buscar la instancia del modelo por su ID.
        competencia = EmpresasCompetencias.objects.get(id_competencia=id_competencia)
        competencia.estado = 3  # Cambia el estado a 3
        #competencia.fecha_hora_modificado = timezone.now() 
        competencia.save()

        # Devolver una respuesta de éxito.
        return JsonResponse({'status': 'success', 'message': 'Empresa competencia actualizada correctamente.'})

    except EmpresasCompetencias.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Empresa competencia no encontrada.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Datos inválidos.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
