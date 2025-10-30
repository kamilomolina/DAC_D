from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from seguridad.views import obtener_permisos_desde_sp, obtener_adminIT
from django.http import JsonResponse
from django.contrib import messages
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError
import json 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connections
from django.http import QueryDict
import time
import pandas as pd
import calendar
import datetime
from celery import shared_task
from pandas.tseries.offsets import MonthEnd
from decimal import Decimal  # Asegúrate de importar Decimal
import numpy as np



def vista_principal(request):
    usuario_id = 141  # o cualquier método que uses para obtener el ID del usuario
    permisos_usuario = construir_diccionario_permisos(usuario_id)
    return render(request, 'plantilla.html', {'permisos': permisos_usuario})

def construir_diccionario_permisos(usuario_id):
    permisos_dict = {}
    resultados = obtener_permisos_desde_sp(usuario_id)

    for resultado in resultados:
        posicion_menu = resultado['Posicion']  # Cambiar índice según la estructura del resultado
        tiene_acceso = resultado['tiene_acceso'] == '1'  # Cambiar índice y lógica según el resultado
        permisos_dict[posicion_menu] = tiene_acceso

    return permisos_dict

def vista_telefonos(request):
    return render(request, 'prueba.html')
    
def obtener_telefonos(request):
    from .models import Telefonos, Supervisor, Vendedor
    telefonos = Telefonos.objects.all().values()
    lista_telefonos = []

    for telefono in telefonos:
        telefono_dict = dict(telefono)

        # Buscar el nombre del vendedor basado en id_vendedor
        vendedor = Vendedor.objects.filter(codigo_vendedor=telefono_dict.get('id_vendedor')).first()
        telefono_dict['nombre_vendedor'] = vendedor.nombre_vendedor if vendedor else 'Vendedor'

        # Buscar el nombre del supervisor basado en id_supervisor
        supervisor = Supervisor.objects.filter(id=telefono_dict.get('id_supervisor')).first() # Asegúrate de que la relación sea correcta
        telefono_dict['nombre_supervisor'] = supervisor.nombre if supervisor else 'Supervisor'

        # Convertir valores binarios a booleanos y manejar None
        for campo in ['registrado', 'activo', 'venta_pma', 'venta_carbajal', 'acceso_total']:
            if campo in telefono_dict:
                valor = telefono_dict[campo]
                telefono_dict[campo] = bool(valor and ord(valor)) if valor is not None else None

        # Eliminar claves con valores None (opcional)
        telefono_dict = {k: v for k, v in telefono_dict.items() if v is not None}

        lista_telefonos.append(telefono_dict)

    return JsonResponse({"data": lista_telefonos})

def obtener_telefonos2(request):
    from .models import Telefonos
    telefonos = Telefonos.objects.all().values()
    lista_telefonos = []

    for telefono in telefonos:
        telefono_dict = dict(telefono)

        # Convierte los valores binarios a booleanos y maneja None
        for campo in ['registrado', 'activo', 'venta_pma', 'venta_carbajal', 'acceso_total']:
            if campo in telefono_dict:
                valor = telefono_dict[campo]
                telefono_dict[campo] = bool(valor and ord(valor)) if valor is not None else None

        # Elimina claves con valores None (opcional, si deseas quitarlas)
        telefono_dict = {k: v for k, v in telefono_dict.items() if v is not None}

        lista_telefonos.append(telefono_dict)
       
    return JsonResponse({"data": lista_telefonos})
    
def favicon(request):
    return HttpResponse(status=204)

@csrf_exempt
def editar_telefono(request, telefono_id):
    from .models import Telefonos, TelefonoAccesoRuta, Vendedor

    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    try:
        telefono = get_object_or_404(Telefonos, pk=telefono_id)
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Error al decodificar JSON: {}'.format(str(e))}, status=400)

        # Asignar valores a los campos del modelo Telefonos
        telefono.codigo_verificacion = data.get('codigo_verificacion')
        telefono.nombre_empleado = data.get('usuario')
        telefono.mac_address = data.get('mac_address')
        telefono.imei_1 = data.get('imei_1')
        telefono.id_telegram = data.get('id_telegram')
        telefono.numero_telefono = data.get('numero_telefono')
        telefono.observaciones = data.get('observaciones')
        telefono.id_vendedor = data.get('id_vendedor')
        telefono.id_supervisor = data.get('id_supervisor')
        telefono.perfil_empleado = data.get('perfil_empleado')
        telefono.usuario = data.get('usuario')
        telefono.registrado = data.get('registrado', False)
        telefono.activo = data.get('activo', False)
        telefono.venta_pma = data.get('venta_pma', False)
        telefono.venta_carbajal = data.get('venta_carbajal', False)
        telefono.acceso_total = True
        print(data)

        nuevos_codigos = data.get('seleccionados', [])
        print(nuevos_codigos)

        # Obtener la lista actual de códigos de vendedores
        codigos_actuales = list(TelefonoAccesoRuta.objects.filter(nombre_empleado=telefono.nombre_empleado).values_list('codigo_vendedor', flat=True))

   
        telefono.save()

        # Agregar nuevos códigos de vendedores
        for codigo in nuevos_codigos:
            if codigo not in codigos_actuales:
                vendedor = Vendedor.objects.filter(codigo_vendedor=codigo).first()
                observaciones = vendedor.nombre_vendedor if vendedor else 'Nombre no encontrado'
                
                TelefonoAccesoRuta.objects.create(
                    nombre_empleado=telefono.nombre_empleado,
                    codigo_verificacion = telefono.codigo_verificacion,
                    codigo_vendedor=codigo,
                    mac_address= telefono.mac_address,
                    observaciones= observaciones
                )

        # Eliminar códigos de vendedores que ya no están en la lista
        for codigo in codigos_actuales:
            if codigo not in nuevos_codigos:
                TelefonoAccesoRuta.objects.filter(nombre_empleado=telefono.nombre_empleado, codigo_vendedor=codigo).delete()

        return JsonResponse({'message': 'Teléfono editado con éxito.'})

    except json.JSONDecodeError as e:
        return JsonResponse({'error': 'Formato de JSON inválido: {}'.format(e)}, status=400)

    except Telefonos.DoesNotExist:
        return JsonResponse({'error': 'Teléfono no encontrado'}, status=404)

    except ValidationError as e:
        return JsonResponse({'error': 'Error de validación: {}'.format(e)}, status=400)

    except Exception as e:
        return JsonResponse({'error': 'Error interno del servidor: {}'.format(str(e))}, status=500)

def index(request):
    return render(request, 'plantilla.html')

def obtener_datos_telefono(request, telefono_id):
    from .models import Telefonos
    telefono = get_object_or_404(Telefonos, pk=telefono_id)
    # Convierte los datos del teléfono en un diccionario
    data = {
        'codigo_verificacion': telefono.codigo_verificacion,
        'nombre_empleado': telefono.nombre_empleado,
        'mac_addess': telefono.mac_address,
        'imei_1': telefono.imei_1,
        'numero_telefono': telefono.numero_telefono,
        'observaciones': telefono.observaciones, 
        'id_vendedor': telefono.id_vendedor, 
        'id_supervisor': telefono.id_supervisor, 
        'usuario': telefono.usuario, 
        'perfil_empleado': telefono.perfil_empleado,
    }
    return JsonResponse(data)


def agregar_telefono(request):
    from .models import Telefonos, TelefonoAccesoRuta, Vendedor
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        nuevo_telefono = Telefonos()

        # Asignar los valores a los campos del modelo Telefonos
        nuevo_telefono.codigo_verificacion = data.get('codigo_verificacion')
        nuevo_telefono.nombre_empleado = data.get('usuario')
        nuevo_telefono.mac_address = data.get('mac_address')
        nuevo_telefono.id_telegram = data.get('id_telegram')
        nuevo_telefono.imei_1 = data.get('imei_1')
        nuevo_telefono.numero_telefono = data.get('numero_telefono')
        nuevo_telefono.observaciones = data.get('observaciones')
        nuevo_telefono.id_vendedor = data.get('id_vendedor')
        nuevo_telefono.id_supervisor = data.get('id_supervisor')
        nuevo_telefono.usuario = data.get('usuario')
        nuevo_telefono.perfil_empleado = data.get('perfil_empleado')

        # Para campos booleanos, asegúrate de convertirlos correctamente
        nuevo_telefono.registrado = data.get('registrado') == 'on'
        nuevo_telefono.activo = data.get('activo') == 'on'
        nuevo_telefono.venta_pma = data.get('venta_pma') == 'on'
        nuevo_telefono.venta_carbajal = data.get('venta_carbajal') == 'on'
        nuevo_telefono.acceso_total = True 
        codigos_vendedores = data.get('seleccionados', [])
       
        try:
            nuevo_telefono.save()

            if codigos_vendedores:
                for codigo_vendedor in codigos_vendedores:
                    # Realizar inserción solo si el codigo_vendedor es diferente al id_vendedor del nuevo_telefono
                    if codigo_vendedor != nuevo_telefono.id_vendedor:
                        vendedor = Vendedor.objects.filter(codigo_vendedor=codigo_vendedor).first()
                        observaciones = vendedor.nombre_vendedor if vendedor else 'Nombre no encontrado'
                        try:
                            TelefonoAccesoRuta.objects.create(
                                nombre_empleado=nuevo_telefono.nombre_empleado,
                                codigo_verificacion=nuevo_telefono.codigo_verificacion,
                                mac_address=nuevo_telefono.mac_address,
                                observaciones=observaciones,
                                codigo_vendedor=codigo_vendedor,
                            )
                        except Exception as e:
                            print('Error al crear TelefonoAccesoRuta: {}'.format(e))
            return JsonResponse({'message': 'Teléfono agregado con éxito.'})
        except Exception as e:
            return JsonResponse({'error': 'Error al agregar teléfono: {}'.format(str(e))})

        
        return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
@permission_classes([AllowAny])
def eliminar_telefono(request, telefono_id):
    from .models import Telefonos
    try:
        if request.method == 'POST':
            telefono = get_object_or_404(Telefonos, pk=telefono_id)
            telefono.delete()
            response_data = {'message': 'Teléfono eliminado exitosamente.'}
            return JsonResponse(response_data)
        else:
            response_data = {'message': 'Error al eliminar el teléfono.'}
            return JsonResponse(response_data)
    except Exception as e:
        logging.exception(e)  # Registra la excepción en los registros
        return HttpResponseServerError('Error interno del servidor')

def obtener_codigo(request):
    conexion_global_nube = connections['default']
    with conexion_global_nube.cursor() as cursor:
        cursor.execute("CALL SP_Get_CodigoVerificacionUnico()")
        codigo_verificacion = cursor.fetchone()[0] 
        
    return JsonResponse({'codigo_verificacion': codigo_verificacion})

#--------------------------------------------------------RUTAS--------------------------------------------------------------------
def obtener_rutas(request):
    from .models import MgRuta
    rutas = MgRuta.objects.all().values('id_ruta', 'ruta', 'nombre_vendedor')
    lista_rutas = [
        {
            'id_ruta': ruta['id_ruta'],
            'descripcion': "{} - {}".format(ruta['ruta'], ruta['nombre_vendedor'])
        }
        for ruta in rutas
    ]

    return JsonResponse({"data": lista_rutas})

def rutas_por_vendedor (id_vendedor):
    conexion_global_nube = connections['default']
    with conexion_global_nube.cursor() as cursor:
        parametros = (id_vendedor,)
        cursor.callproc('CALL SP_GetRutas2ByVendedor(%s)', parametros)
        usuarios_data = [dict(zip(cursor.description, row)) for row in cursor.fetchall()]

    return JsonResponse({'rutas': usuarios_data})
#------------------------------------------------------SUPERVISORES------------------------------------------------------------------

def obtener_supervisores(request):
    from .models import Supervisor
    supervisores = Supervisor.objects.all().values('id_supervisor', 'nombre')  # Filtra solo los campos 'id' y 'nombre'
    lista_supervisores = list(supervisores) 

    return JsonResponse({"data": lista_supervisores})


#-------------------------------------------------------VENDEDORES-------------------------------------------------------------------


def obtener_vendedores(request):
    from .models import Vendedor
    vendedores = Vendedor.objects.all().values('codigo_vendedor', 'nombre_vendedor')  # Filtra solo los campos 'id' y 'nombre'
    lista_vendedores = list(vendedores)  # Convierte el queryset en una lista de diccionarios

    return JsonResponse({"data": lista_vendedores})

def obtener_vendedores_modal(request, nombre_vendedor):
    from .models import Vendedor, Supervisor
    vendedores_query = Vendedor.objects.filter(nombre_vendedor__icontains=nombre_vendedor)
    lista_vendedores = []

    for vendedor in vendedores_query:
        # Convertir el objeto Vendedor en un diccionario
        vendedor_dict = {
            'id_vendedor': vendedor.id_vendedor,
            'codigo_vendedor': vendedor.codigo_vendedor,
            'nombre_vendedor': vendedor.nombre_vendedor,
            # Aquí se personaliza el valor de id_sucursal
            'id_sucursal': "DC2" if vendedor.id_sucursal == 8 else "DC1" if vendedor.id_sucursal == 10 else vendedor.id_sucursal,
            # Inicializamos 'nombre_supervisor' con un valor por defecto
            'nombre_supervisor': "No disponible",
        }

        # Verifica si el valor de 'activo' es un objeto de tipo bytes y conviértelo a booleano
        valor_activo = vendedor.activo
        if isinstance(valor_activo, bytes):
            vendedor_dict['activo'] = bool(int.from_bytes(valor_activo, byteorder='big'))
        else:
            vendedor_dict['activo'] = valor_activo

        # Buscar el nombre del supervisor basado en id_supervisor si existe
        if vendedor.id_supervisor:
            supervisor = Supervisor.objects.filter(id=vendedor.id_supervisor).first()
            if supervisor:
                vendedor_dict['nombre_supervisor'] = supervisor.nombre

        lista_vendedores.append(vendedor_dict)

    return JsonResponse({"data": lista_vendedores})

#---------------------------------------------------------USUARIOS-------------------------------------------------------------------

def obtener_usuarios(usuario_id):
    conexion_global_nube = connections['global_nube']
    with conexion_global_nube.cursor() as cursor:
        cursor.execute("CALL SP_D_Obtener_Usuarios()")
        columnas = [col[0] for col in cursor.description]
        usuarios_data = [
            dict(zip(columnas, row)) for row in cursor.fetchall()
        ]
        
    # Devolver un JSON con los datos de los usuarios
    return JsonResponse({'usuarios': usuarios_data})

#----------------------------------------------------Telefono Acceso Rutas ----------------------------------------------------------

def obtener_rutas_v(request, nombre_empleado):
    from .models import TelefonoAccesoRuta, Vendedor
    try:
        # Buscar todos los registros en TelefonoAccesoRuta que coincidan con el nombre_empleado
        telefonos = TelefonoAccesoRuta.objects.filter(nombre_empleado=nombre_empleado)

        vendedores_info = []
        for telefono in telefonos:
            # Buscar la información del vendedor correspondiente
            vendedor = Vendedor.objects.filter(codigo_vendedor=telefono.codigo_vendedor).first()
            if vendedor:
                vendedores_info.append({
                    'codigo_vendedor': vendedor.codigo_vendedor,
                    'nombre_vendedor': vendedor.nombre_vendedor
                })

        return JsonResponse({'data': vendedores_info})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def obtener_vendedores_no_asociados(request, nombre_empleado):
    from .models import TelefonoAccesoRuta, Vendedor
    try:
        # Obtener los códigos de vendedor asociados al nombre_empleado
        telefonos = TelefonoAccesoRuta.objects.filter(nombre_empleado=nombre_empleado)
        codigos_asociados = [telefono.codigo_vendedor for telefono in telefonos]

        # Buscar vendedores que no estén en la lista de códigos asociados
        vendedores_no_asociados = Vendedor.objects.exclude(codigo_vendedor__in=codigos_asociados)

        vendedores_info = []
        for vendedor in vendedores_no_asociados:
            vendedores_info.append({
                'codigo_vendedor': vendedor.codigo_vendedor,
                'nombre_vendedor': vendedor.nombre_vendedor
            })

        return JsonResponse({'data': vendedores_info})
    except Exception as e:
        return JsonResponse({'error': str(e)})

#-----------------------------------------------DATA SCIENCE----------------------------------------------------------

def obtener_fechas_del_mes(mes, anio):
    # Convertir mes y anio a enteros para evitar problemas de formato
    mes = int(mes)
    anio = int(anio)
    
    fecha_inicio_str = "01/{:02d}/{}".format(mes, anio)
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    fecha_final_str = "{}/{:02d}/{}".format(ultimo_dia, mes, anio)
    
    fecha_inicio = datetime.datetime.strptime(fecha_inicio_str, "%d/%m/%Y").date()
    fecha_final = datetime.datetime.strptime(fecha_final_str, "%d/%m/%Y").date()
    
    return fecha_inicio, fecha_final

def obtener_mes_anterior(mes, anio):
    if mes == 1:
        return 12, anio - 1
    else:
        return mes - 1, anio

def obtener_datos_sp(conexion, nombre_sp, parametros):
    with conexion.cursor() as cursor:
        cursor.callproc(nombre_sp, parametros)
        columns = [col[0] for col in cursor.description]
        datos = cursor.fetchall()
        if not datos:
            print("No se obtuvieron datos del Stored Procedure {}.".format(nombre_sp))
            return pd.DataFrame()  # Retorna un DataFrame vacío
        return pd.DataFrame(datos, columns=columns)

def calcular_inventario(dataframe, mes, anio):
    try:
        existencia = dataframe[(dataframe['mes'] == mes) & (dataframe['anio'] == anio)]['existencia'].iloc[0]
        costo = dataframe[(dataframe['mes'] == mes) & (dataframe['anio'] == anio)]['costo'].iloc[0]
        saldo = existencia * costo
        return saldo
    except Exception as e:
        print("Error al calcular inventario para mes {}, año {}: {}".format(mes, anio, e))
        return None

def obtener_rotacion_producto(mes, mes2, anio):
    mes_inicial = int(mes)
    mes_final = int(mes2)
    anio = int(anio)

    try:
        start_time = time.time()
        conexion_ct = connections['control_total_test']
        dataframe1 = obtener_datos_sp(conexion_ct, 'SP_DAC_D_GET_HISTORIAL_ROTACION', [])
        
        fecha_inicio_inicial, _ = obtener_fechas_del_mes(mes_inicial, anio)
        _, fecha_final_final = obtener_fechas_del_mes(mes_final, anio)
        
        # Obtener el mes y año anterior al mes inicial
        mes_anterior, anio_anterior = obtener_mes_anterior(mes_inicial, anio)
        fecha_inicio_anterior, _ = obtener_fechas_del_mes(mes_anterior, anio_anterior)
        registros_mes_final = dataframe1[(dataframe1['mes'] == mes_final) & (dataframe1['anio'] == anio)]
        # Filtrar dataframe1 para obtener solo los registros entre los meses y año especificados
        registros_mes_inicial_final = dataframe1[(dataframe1['mes'] >= mes_inicial) & (dataframe1['mes'] <= mes_final) & (dataframe1['anio'] == anio)]
        
        # Agrupar por 'id_equivalencia_x_categoria' para consolidar registros
        registros_agrupados = registros_mes_final.groupby('id_equivalencia_x_categoria').agg({
            'existencia': 'first',
            'costo': 'first',
            'descripcion_producto': 'first' 
        }).reset_index()
    
        
        registros = []
        for _, registro_agrupado in registros_agrupados.iterrows():
            # Convertir a Decimal para operaciones matemáticas
            existencia = Decimal(registro_agrupado['existencia'])
            costo = Decimal(registro_agrupado['costo'])
            print("prueba", "= ", existencia, "*", costo)

            # Obtener el registro del mes anterior para el mismo producto
            registro_anterior = dataframe1[
                (dataframe1['mes'] == mes_anterior) &
                (dataframe1['anio'] == anio_anterior) &
                (dataframe1['id_equivalencia_x_categoria'] == registro_agrupado['id_equivalencia_x_categoria'])
            ]

            if not registro_anterior.empty:
                existencia_anterior = Decimal(registro_anterior['existencia'].iloc[0])
                costo_anterior = Decimal(registro_anterior['costo'].iloc[0])
                saldo_mes_anterior = existencia_anterior * costo_anterior
                print(saldo_mes_anterior, "= ", existencia_anterior,"*", costo_anterior)
            else:
                saldo_mes_anterior = Decimal(0)
            
           # La existencia y costo se toman del mes final
            existencia_mes_actual = Decimal(registro_agrupado['existencia'])
            costo_mes_actual = Decimal(registro_agrupado['costo'])
            saldo_mes_actual = existencia_mes_actual * costo_mes_actual
            
            nuevo_registro = {
                'descripcion_producto': registro_agrupado['descripcion_producto'],
                'id_equivalencia_x_categoria': registro_agrupado['id_equivalencia_x_categoria'],
                'saldo_mes_actual': saldo_mes_actual,  # Saldo al final del periodo
                'saldo_mes_anterior': saldo_mes_anterior
            }
            registros.append(nuevo_registro)
          

        resultados = pd.DataFrame(registros)
        conexion_ct2 = connections['control_total']
        dataframe2 = obtener_datos_sp(conexion_ct2, 'DAC_D_SP_GetFacturasDetalles', [fecha_inicio_inicial, fecha_final_final])
        suma_total_producto = dataframe2.groupby('id_equivalencia_x_categoria')['total_producto'].sum().reset_index()

        resultados_final = pd.merge(resultados, suma_total_producto, on='id_equivalencia_x_categoria', how='left').fillna(0)
        dataframe2['total_producto'] = pd.to_numeric(dataframe2['total_producto'], errors='coerce')
        dataframe2['total_producto'] = dataframe2['total_producto'].fillna(0)  # Rellenar NaN con 0
        dataframe2['precio_unitario'] = pd.to_numeric(dataframe2['precio_unitario'], errors='coerce')
        dataframe2['impuesto'] = pd.to_numeric(dataframe2['impuesto'], errors='coerce')
        dataframe2['cantidad'] = pd.to_numeric(dataframe2['cantidad'], errors='coerce')
        dataframe2['fecha_ingreso'] = pd.to_datetime(dataframe2['fecha_ingreso'])

        # Convertir 'fecha_ingreso' a datetime si no está en ese formato
        dataframe2['fecha_ingreso'] = pd.to_datetime(dataframe2['fecha_ingreso'])

        # Ordenar dataframe2 por 'id_equivalencia_x_categoria' y 'fecha_ingreso'
        dataframe2 = dataframe2.sort_values(by=['id_equivalencia_x_categoria', 'fecha_ingreso'])

        # Calcular la diferencia en días entre cada compra
        diferencia_tiempo = dataframe2.groupby('id_equivalencia_x_categoria')['fecha_ingreso'].diff().shift(-1)
        if diferencia_tiempo.dtype == 'timedelta64[ns]':
            dataframe2['dias_hasta_siguiente_compra'] = diferencia_tiempo.dt.days
        else:
            dataframe2['dias_hasta_siguiente_compra'] = 0  # En caso de tipo incorrecto, asignar 0

        # Identificar la primera compra de cada categoría en el periodo seleccionado
        primera_compra_indices = dataframe2.groupby('id_equivalencia_x_categoria')['fecha_ingreso'].idxmin()

        # Calcular los días desde el inicio del periodo hasta la primera compra
        dataframe2.loc[primera_compra_indices, 'dias_desde_inicio_periodo'] = (dataframe2.loc[primera_compra_indices, 'fecha_ingreso'] - pd.to_datetime(fecha_inicio_inicial)).dt.days + 1
        
        dataframe2 = dataframe2.join(resultados_final.set_index('id_equivalencia_x_categoria')['saldo_mes_anterior'], on='id_equivalencia_x_categoria')

        # Asegurar que la columna 'dias_desde_inicio_periodo' es numérica y rellenar valores faltantes con 0
        dataframe2['dias_ajustados'] = dataframe2['dias_desde_inicio_periodo'].replace(0, 1)
        dataframe2.loc[primera_compra_indices, 'total_producto_ponderado'] = dataframe2.loc[primera_compra_indices, 'total_producto'] * dataframe2['dias_ajustados'] + dataframe2.loc[primera_compra_indices, 'saldo_mes_anterior'] * dataframe2['dias_ajustados']

        # Asegurarnos de que los demás 'total_producto_ponderado' se calculan correctamente
        indices_despues_primera_compra = dataframe2.index.difference(primera_compra_indices)
        dataframe2.loc[indices_despues_primera_compra, 'total_producto_ponderado'] = dataframe2.loc[indices_despues_primera_compra, 'total_producto'] * dataframe2.loc[indices_despues_primera_compra, 'dias_hasta_siguiente_compra']

        # Para la última compra de cada categoría, calcular los días hasta el final del mes (incluido)
        ultimo_dia_del_mes = pd.to_datetime(fecha_final_final) + MonthEnd(0)
        ultima_compra_indices = dataframe2.groupby('id_equivalencia_x_categoria')['fecha_ingreso'].idxmax()

        # Asegurarse de que 'fecha_ingreso' es de tipo datetime64 antes de hacer la resta
        if dataframe2['fecha_ingreso'].dtype == 'datetime64[ns]':
            dataframe2.loc[ultima_compra_indices, 'dias_hasta_siguiente_compra'] = (ultimo_dia_del_mes - dataframe2.loc[ultima_compra_indices, 'fecha_ingreso']).dt.days
            dataframe2.loc[ultima_compra_indices, 'dias_hasta_siguiente_compra'] += 1  # Incluir el último día del mes
        else:
            dataframe2.loc[ultima_compra_indices, 'dias_hasta_siguiente_compra'] = 0  # En caso de tipo incorrecto, asignar 0

        # Asegurarse de que todos los valores de 'dias_hasta_siguiente_compra' son numéricos
        dataframe2['dias_hasta_siguiente_compra'] = pd.to_numeric(dataframe2['dias_hasta_siguiente_compra'], errors='coerce').fillna(0)

        # Realizar la multiplicación para calcular 'total_producto_ponderado'
        dataframe2['total_producto_ponderado'] = (dataframe2['total_producto'] ) * dataframe2['dias_hasta_siguiente_compra']

        # Resto del código para sumar y unir con resultados_final
        suma_total_producto_ponderado = dataframe2.groupby('id_equivalencia_x_categoria')['total_producto_ponderado'].sum().reset_index()
        suma_total_producto_ponderado.rename(columns={'total_producto_ponderado': 'suma_total_producto_ponderado'}, inplace=True)
        resultados_final = pd.merge(resultados_final, suma_total_producto_ponderado, on='id_equivalencia_x_categoria', how='left').fillna(0)

        # Seleccionar y filtrar columnas deseadas para dataframe2_resumido
        categorias_unicas_df1 = set(dataframe1['id_equivalencia_x_categoria'].unique())
        dataframe2_filtrado = dataframe2[dataframe2['id_equivalencia_x_categoria'].isin(categorias_unicas_df1)]
        columnas_seleccionadas = ['id_equivalencia_x_categoria', 'dias_hasta_siguiente_compra', 'total_producto', 'total_producto_ponderado', 'fecha_ingreso']
        dataframe2_resumido = dataframe2_filtrado[columnas_seleccionadas]

        resultados_final['saldo_mes_actual'] = resultados_final['saldo_mes_actual'].apply(Decimal)
        resultados_final['saldo_mes_anterior'] = resultados_final['saldo_mes_anterior'].apply(Decimal)
        resultados_final['suma_total_producto_ponderado'] = resultados_final['suma_total_producto_ponderado'].apply(Decimal)
        resultados_final['total_producto'] = resultados_final['total_producto'].apply(Decimal)
        
        # Calcular el número total de días en el mes
        numero_dias_mes = Decimal((fecha_final_final - fecha_inicio_inicial).days + 1)  # +1 para incluir el último día
        print("de octubre a dic hay", numero_dias_mes)

        # Calcular el inventario promedio
        resultados_final['inventario_promedio'] = (resultados_final['saldo_mes_actual'] + resultados_final['saldo_mes_anterior'] + resultados_final['suma_total_producto_ponderado']) / numero_dias_mes
        # Calcular COGS
        resultados_final['COGS'] = resultados_final['total_producto'] + (resultados_final['saldo_mes_actual'] - resultados_final['saldo_mes_anterior'])

        # Calcular la rotación de inventario promedio
        # Prevenir la división por cero usando np.where
        resultados_final['rotacion_de_inventario_promedio'] = np.where(
            resultados_final['inventario_promedio'] != 0,
            resultados_final['COGS'] / resultados_final['inventario_promedio'],
            0
        )

        end_time = time.time()
        formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
        print("Tiempo de ejecución:", formatted_elapsed_time)
        print(dataframe2_resumido)
        print(resultados_final)

        return resultados_final

    except Exception as e:
        print("Ocurrió un error al obtener los datos:", e)
        return pd.DataFrame()  

    return resultados_final

def vista_rotacion_producto(request, mes, mes2, anio):
    df = obtener_rotacion_producto(int(mes), int(mes2), int(anio))
    
    df_json = df.to_json(orient='records', force_ascii=False)

    df_data = json.loads(df_json)

    return JsonResponse(df_data, safe=False)