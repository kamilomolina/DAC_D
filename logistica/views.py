from django.shortcuts import render
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from seguridad.views import obtener_permisos_desde_sp, obtener_adminIT
from django.http import JsonResponse
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError
import json 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connections
import pandas as pd
import calendar
import numpy as np
from datetime import datetime
from decimal import Decimal
from decimal import Decimal, InvalidOperation
import numpy as np
from datetime import datetime
from decimal import Decimal
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils import timezone
import pytz
from django.db.models import Sum

from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils import timezone
import pytz


# En DAC saldra como entrega, pero aqui en codigo se le conocera como programación
@xframe_options_exempt
@xframe_options_exempt
def vista_crear_programacion(request):
    return render(request, 'modal_crear_programacion.html')

#-------------------------------------------------CONSOLIDADOS------------------------------------------------------
#-------------------------------------------------CONSOLIDADOS------------------------------------------------------
def obtener_consolidados():
    conexion_control_total_t = connections['control_total_test']
    with conexion_control_total_t.cursor() as cursor:
        cursor.callproc('SP_DAC_D_Obtener_consolidados')
        columnas = [col[0] for col in cursor.description]
        filas = cursor.fetchall()
        # Convertir cada fila de tupla a lista
        filas_lista = [list(fila) for fila in filas]
        # Crear el DataFrame con las filas convertidas a listas
        consolidados = pd.DataFrame(filas_lista, columns=columnas)

    return consolidados
    with conexion_control_total_t.cursor() as cursor:
        cursor.callproc('SP_DAC_D_Obtener_consolidados')
        columnas = [col[0] for col in cursor.description]
        filas = cursor.fetchall()
        # Convertir cada fila de tupla a lista
        filas_lista = [list(fila) for fila in filas]
        # Crear el DataFrame con las filas convertidas a listas
        consolidados = pd.DataFrame(filas_lista, columns=columnas)

    return consolidados


def procesar_consolidados(request):
    # Obtener los datos
    df = obtener_consolidados()
    from .models import DistribucionProgramacionDetalle
    # Obtener lista de id_consolidado ya presentes en DistribucionProgramacionDetalle
    programaciones_detalle = DistribucionProgramacionDetalle.objects.exclude(estado=3).values_list('id_consolidado', flat=True)
    id_consolidado_excluidos = set(programaciones_detalle)

    # Filtrar el DataFrame para excluir esos id_consolidado
    df = df[~df['id_consolidado'].isin(id_consolidado_excluidos)]
    print(df)

    # Renombrar las columnas para reflejar los nombres que se usaban previamente
    df = df.rename(columns={
        'total_consolidado': 'total_suma',
        'costo_consolidado': 'costo_suma',
        'cantidad_vendida_peso_consolidado': 'cantidad_vendida_peso_suma',
        'cantidad_total_productos_consolidado': 'cantidad_total_productos_suma',
        'cantidad_clientes': 'cantidad_clientes',  
        'cantidad_facturas': 'cantidad_facturas',
        'utilidad_consolidado': 'utilidad',
        'rentabilidad_consolidado': 'rentabilidad'
    })

    # Añadir cualquier cálculo adicional si es necesario
    # Por ejemplo, si 'utilidad_porcentaje' no se calcula en el SP y se necesita aquí.
    df['utilidad_porcentaje'] = (df['utilidad'] / df['total_suma']) * 100

    # Reemplazar NaN por 0 y asegurarse de que no hay divisiones por cero
    df.replace([float('inf'), -float('inf'), np.nan], 0, inplace=True)

    # Convertir el resultado a una lista de diccionarios
    resultado_dict = df.to_dict(orient='records')

    # Enviar la respuesta JSON
    return JsonResponse({'data': resultado_dict})

#------------------------------------------------------------VEHICULOS------------------------------------------------------------

def obtener_vehiculos(request):
    from .models import DistribucionVehiculos
    vehiculos = DistribucionVehiculos.objects.all().values()
    peso_total_actual = request.GET.get('peso_total', None)
    print(peso_total_actual)
    if peso_total_actual:

        try:
            peso_total_actual = Decimal(peso_total_actual)
        except InvalidOperation:
            peso_total_actual = None

    if peso_total_actual is not None:
        vehiculos_disponibles = vehiculos.filter(capacidad_lbs__gte=peso_total_actual)
    else: 
        vehiculos_disponibles = vehiculos
    lista_vehiculos = list(vehiculos_disponibles)  
    return JsonResponse({"data": lista_vehiculos})


def sumar_valor_flete_vehiculo(id_vehiculo):
    from .models import DistribucionVehiculosDetalleFlete
    from django.db.models import Sum
   
    try:
        suma = DistribucionVehiculosDetalleFlete.objects.exclude(
            estado=3
        ).filter(
            id_vehiculo=id_vehiculo
        ).aggregate(suma_valor_flete=Sum('valor_flete'))

        print("Hola desde vehiculos")
        suma_valor_flete = suma['suma_valor_flete']

        if suma_valor_flete is None:
            suma_valor_flete = 0

        return suma_valor_flete

    except Exception as e:
        print("Error en la función sumar_valor_flete_vehiculo: {}".format(e))
        return 0


#-----------------------------------------------------------COMBUSTIBLES-----------------------------------------------------------

def obtener_combustibles(request):
    from .models import DistribucionCombustibles
    combustibles = DistribucionCombustibles.objects.all().values()
    lista_combustibles = list(combustibles)  # Convertir QuerySet a una lista de diccionarios
    return JsonResponse({"data": lista_combustibles})

#--------------------------------------------------------------DESTINOS-----------------------------------------------------------

def obtener_destinos(request):
    from .models import DistribucionDestinos
    destinos = DistribucionDestinos.objects.all().values()
    lista_destinos = list(destinos)  # Convertir QuerySet a una lista de diccionarios
    return JsonResponse({"data": lista_destinos})

def obtener_suma_fletes_destinos(listado_destino):
    destinos_data = []
    print("si sirve")
    for id_destino in listado_destino:
        data = sumar_valor_flete_destino(id_destino)
        print(data)
        if data:
            destinos_data.append(data)

    return destinos_data

def sumar_valor_flete_destino(id_destino):
    from .models import DistribucionDestinosDetalleFlete
    from django.db.models import Sum
    try:
        suma = DistribucionDestinosDetalleFlete.objects.exclude(
            estado=3
        ).filter(
            id_destino=id_destino
        ).aggregate(suma_valor_flete=Sum('valor_flete'))

        suma_valor_flete = suma['suma_valor_flete']

        if suma_valor_flete is None:
            suma_valor_flete = 0

        return suma_valor_flete

    except Exception as e:
        print("Error en la función sumar_valor_flete_destino: {}".format(e))
        return 0
#--------------------------------------------------------------TRIPULANTES---------------------------------------------------------


def obtener_tripulantes(request):
    # Obtener todos los tripulantes cuyo estado no es 3
    tripulantes = DistribucionTripulantes.objects.exclude(estado=3).values()
    lista_tripulantes = list(tripulantes)  # Convertir QuerySet a una lista de diccionarios

    return JsonResponse({"data": lista_tripulantes})
    
def obtener_tripulantes(request):
    from .models import DistribucionTripulantes
    fecha_viaje_str = request.GET.get('fecha_viaje', None)
    
    # Convertir la cadena de fecha en formato 'dd/mm/YYYY' a un objeto date de Python si no es None
    fecha_viaje = datetime.strptime(fecha_viaje_str, '%d/%m/%Y').date() if fecha_viaje_str else None

    if fecha_viaje:
        tripulantes_disponibles = DistribucionTripulantes.objects.filter(
            licencia_vencimiento__gt=fecha_viaje,
        ).values()
    else:
        tripulantes_disponibles = DistribucionTripulantes.objects.all().values()

    lista_tripulantes = list(tripulantes_disponibles)
    return JsonResponse({"data": lista_tripulantes})

def get_tripulante_data(id_tripulante):
    from .models import DistribucionTripulantes
    try:
        tripulante = DistribucionTripulantes.objects.filter(id_tripulante=id_tripulante).values(
            'id_tripulante', 'identidad_tripulante', 'nombre_tripulante',
            'numero_licencia', 'id_tipo_tripulante', 'disponibilidad', 'estado'
        ).first()

        
        if tripulante:
            return tripulante
        else:
            return None

    except Exception as e:
        print(e)
        return None

def sumar_valor_flete_tripulante(id_tripulante):
    from .models import DistribucionTripulantesDetalleFlete
    from django.db.models import Sum
    try:
        suma = DistribucionTripulantesDetalleFlete.objects.exclude(
            estado=3
        ).filter(
            id_tripulante=id_tripulante
        ).aggregate(suma_valor_flete=Sum('valor_flete'))

        suma_valor_flete = suma['suma_valor_flete']

        if suma_valor_flete is None:
            suma_valor_flete = 0

        return suma_valor_flete

    except Exception as e:
        print("Error en la función sumar_valor_flete_tripulante: {}".format(e))
        return 0

def obtener_datos_tripulantes(listadoTripulantes):
    tripulantes_data = []

    for id_tripulante in listadoTripulantes:
        data = get_tripulante_data(id_tripulante)
        if data:
            tripulantes_data.append(data)

    return tripulantes_data

def obtener_suma_fletes_tripulantes(listadoTripulantes):
    tripulantes_data = []

    print("si sirve")
    for id_tripulante in listadoTripulantes:
        data = sumar_valor_flete_tripulante(id_tripulante)
        print(data)
        if data:
            tripulantes_data.append(data)

    return tripulantes_data

#------------------------------------------------------------PROCESO PROGRAMACION--------------------------------------------------

@xframe_options_exempt
def vista_proceso_programacion(request):
    return render(request, 'modal_proceso.html')


@xframe_options_exempt
def vista_programacion_all(request):
    return render(request, 'distribuciones_programaciones.html')

#---------------------------------------------------------------PROGRAMACIÓN-------------------------------------------------------
@xframe_options_exempt
def vista_tabla_programaciones(request):
    return render(request, 'tabla_programaciones.html')

@csrf_exempt
def insertar_programacion(request):
    from .models import DistribucionProgramacion, DistribucionProgramacionDestino, DistribucionProgramacionTripulantes, DistribucionProgramacionDetalle
    try:
        data = json.loads(request.body.decode('utf-8'))

        fecha_str = data.get('fecha', None)
        if fecha_str:
            # Convert string to datetime object
            naive_datetime = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
            # Make it timezone-aware (assuming UTC, change as needed)
            aware_datetime = pytz.utc.localize(naive_datetime)
            _fecha = aware_datetime
        else:
            _fecha = None
        _id_vehiculo = data.get('id_vehiculo', None)
        _utilidad_operativa = data.get('utilidad_operativa', None)
        _utilidad_total = data.get('utilidad_total', None)
        _volumen = data.get('volumen', None)
        _peso_total = data.get('peso_total', None)
        _cantidad_facturas = data.get('cantidad_facturas', None)
        _cantidad_clientes = data.get('cantidad_clientes', None)
        _rentabilidad = data.get('rentabilidad', None)
        _cantidad_productos = data.get('cantidad_productos', None)
        _estado = data.get('estado', None)
        _creado_por = data.get('creado_por', None)
        _fecha_hora_creado = data.get('fecha_hora_creado', None)
        listado_destinos = data.get('listaSeleccionados', None)
        listado_tripulantes = data.get('listaTripulantesSeleccionados', None)
        listado_consolidados = data.get('listaConsolidados', None)
        print(listado_destinos,"Destinos")
        print(listado_consolidados, "Consolidados")
        print(listado_tripulantes, "tripulantes")

        #datos_tripulantes= obtener_datos_tripulantes(listado_tripulantes)
        fletes_tripulantes = obtener_suma_fletes_tripulantes(listado_tripulantes)
        fletes_destinos = obtener_suma_fletes_destinos(listado_destinos)
        fletes_vehiculos = sumar_valor_flete_vehiculo(_id_vehiculo)
        #prueba = fletes_tripulantes + fletes_destinos + fletes_vehiculos
        #print(fletes_vehiculos)

        #print(datos_tripulantes, "datos")
        #print(fletes_vehiculos)
   
        programacion = DistribucionProgramacion(
            fecha=_fecha,
            id_vehiculo=_id_vehiculo,
            utilidad_operativa=_utilidad_operativa,
            utilidad_total=_utilidad_total,
            volumen=_volumen,
            peso_total=_peso_total,
            cantidad_facturas=_cantidad_facturas,
            cantidad_clientes=_cantidad_clientes,
            rentabilidad=_rentabilidad,
            cantidad_productos=_cantidad_productos,
            estado= 1,
            creado_por=_creado_por,
            fecha_hora_creado=_fecha_hora_creado
        )
        programacion.save()

        errores_destinos = []
        for id_destino in listado_destinos:
            try:
                destino = DistribucionProgramacionDestino(
                    id_programacion=programacion.id_programacion,
                    id_destino=id_destino,
                    estado= 1,
                )
                destino.save()
            except Exception as e:
                errores_destinos.append(str(e))

        # Inserción para tripulantes
        errores_tripulantes = []
        for id_tripulante in listado_tripulantes:
            try:
                tripulante = DistribucionProgramacionTripulantes(
                    id_programacion=programacion.id_programacion,
                    id_tripulante=id_tripulante,
                    estado= 1,
                )
                tripulante.save()
            except Exception as e:
                errores_tripulantes.append(str(e))
        
        errores_detalles = []
        for id_consolidado in listado_consolidados:
            try:
                detalle = DistribucionProgramacionDetalle(
                    id_programacion=programacion.id_programacion,
                    id_consolidado=id_consolidado,
                    estado= 1,
                )
                detalle.save()
            except Exception as e:
                errores_detalles.append(str(e))

        # Comprueba si hubo errores y decide qué hacer
        if errores_destinos or errores_tripulantes:
            # Aquí puedes decidir si quieres devolver un error o no
            print("Errores en destinos:", errores_destinos)
            print("Errores en tripulantes:", errores_tripulantes)
            print("Errores en detalles:", errores_detalles)

        # Devuelve una respuesta JSON de éxito
        return JsonResponse({'message': 'Registro insertado correctamente'})
    
    except Exception as e:
        # Manejo de excepciones y respuesta de error
        return JsonResponse({'error': str(e)}, status=500)

def obtener_programaciones_data(request):
    conexion_dac = connections['dac']
    with conexion_dac.cursor() as cursor:
        cursor.execute("CALL DISTRIBUCION_OBTENER_PROGRAMACION")
        column_names = [col[0] for col in cursor.description]
        rows = [list(row) for row in cursor.fetchall()]

    df = pd.DataFrame(rows, columns=column_names)

    # Reemplazar NaN con None
    df = df.where(pd.notnull(df), None)

    # Excluir 'id_programacion_detalle'
    df = df.drop(columns=['id_programacion_detalle'])

    # Agrupar y combinar registros
    programaciones_agrupadas = df.groupby('id_programacion').first().reset_index()
    df = obtener_consolidados()
    from .models import DistribucionProgramacionDetalle
    # Obtener lista de id_consolidado ya presentes en DistribucionProgramacionDetalle
    programaciones_detalle = DistribucionProgramacionDetalle.objects.exclude(estado=3).values_list('id_consolidado', flat=True)
    id_consolidado_excluidos = set(programaciones_detalle)
    # Filtrar el DataFrame para excluir esos id_consolidado
    df = df[~df['id_consolidado'].isin(id_consolidado_excluidos)]

    # Renombrar las columnas para reflejar los nombres que se usaban previamente
    df = df.rename(columns={
        'total_consolidado': 'total_suma',
        'costo_consolidado': 'costo_suma',
        'cantidad_vendida_peso_consolidado': 'cantidad_vendida_peso_suma',
        'cantidad_total_productos_consolidado': 'cantidad_total_productos_suma',
        'cantidad_clientes': 'cantidad_clientes',  
        'cantidad_facturas': 'cantidad_facturas',
        'utilidad_consolidado': 'utilidad',
        'rentabilidad_consolidado': 'rentabilidad'
    })

    # Añadir cualquier cálculo adicional si es necesario
    # Por ejemplo, si 'utilidad_porcentaje' no se calcula en el SP y se necesita aquí.
    df['utilidad_porcentaje'] = (df['utilidad'] / df['total_suma']) * 100

    # Reemplazar NaN por 0 y asegurarse de que no hay divisiones por cero
    df.replace([float('inf'), -float('inf'), np.nan], 0, inplace=True)

    # Convertir el resultado a una lista de diccionarios
    resultado_dict = df.to_dict(orient='records')

    # Enviar la respuesta JSON
    return JsonResponse({'data': resultado_dict})

#------------------------------------------------------------VEHICULOS------------------------------------------------------------

def obtener_vehiculos(request):
    from .models import DistribucionVehiculos
    vehiculos = DistribucionVehiculos.objects.all().values()
    peso_total_actual = request.GET.get('peso_total', None)
    print(peso_total_actual)
    if peso_total_actual:

        try:
            peso_total_actual = Decimal(peso_total_actual)
        except InvalidOperation:
            peso_total_actual = None

    if peso_total_actual is not None:
        vehiculos_disponibles = vehiculos.filter(capacidad_lbs__gte=peso_total_actual)
    else: 
        vehiculos_disponibles = vehiculos
    lista_vehiculos = list(vehiculos_disponibles)  
    return JsonResponse({"data": lista_vehiculos})


def sumar_valor_flete_vehiculo(id_vehiculo):
    from .models import DistribucionVehiculosDetalleFlete
    from django.db.models import Sum
   
    try:
        suma = DistribucionVehiculosDetalleFlete.objects.exclude(
            estado=3
        ).filter(
            id_vehiculo=id_vehiculo
        ).aggregate(suma_valor_flete=Sum('valor_flete'))

        print("Hola desde vehiculos")
        suma_valor_flete = suma['suma_valor_flete']

        if suma_valor_flete is None:
            suma_valor_flete = 0

        return suma_valor_flete

    except Exception as e:
        print("Error en la función sumar_valor_flete_vehiculo: {}".format(e))
        return 0


#-----------------------------------------------------------COMBUSTIBLES-----------------------------------------------------------

def obtener_combustibles(request):
    from .models import DistribucionCombustibles
    combustibles = DistribucionCombustibles.objects.all().values()
    lista_combustibles = list(combustibles)  # Convertir QuerySet a una lista de diccionarios
    return JsonResponse({"data": lista_combustibles})

#--------------------------------------------------------------DESTINOS-----------------------------------------------------------

def obtener_destinos(request):
    from .models import DistribucionDestinos
    destinos = DistribucionDestinos.objects.all().values()
    lista_destinos = list(destinos)  # Convertir QuerySet a una lista de diccionarios
    return JsonResponse({"data": lista_destinos})

def obtener_suma_fletes_destinos(listado_destino):
    destinos_data = []
    print("si sirve")
    for id_destino in listado_destino:
        data = sumar_valor_flete_destino(id_destino)
        print(data)
        if data:
            destinos_data.append(data)

    return destinos_data

def sumar_valor_flete_destino(id_destino):
    from .models import DistribucionDestinosDetalleFlete
    from django.db.models import Sum
    try:
        suma = DistribucionDestinosDetalleFlete.objects.exclude(
            estado=3
        ).filter(
            id_destino=id_destino
        ).aggregate(suma_valor_flete=Sum('valor_flete'))

        suma_valor_flete = suma['suma_valor_flete']

        if suma_valor_flete is None:
            suma_valor_flete = 0

        return suma_valor_flete

    except Exception as e:
        print("Error en la función sumar_valor_flete_destino: {}".format(e))
        return 0
#---------------------------------------------------------------ORIGEN---------------------------------------------------------
def obtener_almacenes(request):
    conexion_global_nube = connections['control_total']
    with conexion_global_nube.cursor() as cursor:
        cursor.execute("CALL SP_GET_ALMACENES()")
        columnas = [col[0] for col in cursor.description]
        almacenes = [
            dict(zip(columnas, row)) for row in cursor.fetchall()
        ]
        
    # Devolver un JSON con los datos de los usuarios
    return JsonResponse({'usuarios': almacenes})
#--------------------------------------------------------------TRIPULANTES---------------------------------------------------------

def obtener_tripulantes(request):
    from .models import DistribucionTripulantes
    # Obtener todos los tripulantes cuyo estado no es 3
    tripulantes = DistribucionTripulantes.objects.exclude(estado=3).values()
    lista_tripulantes = list(tripulantes)  # Convertir QuerySet a una lista de diccionarios

    return JsonResponse({"data": lista_tripulantes})
    
def obtener_tripulantes(request):
    from .models import DistribucionTripulantes
    fecha_viaje_str = request.GET.get('fecha_viaje', None)
    
    # Convertir la cadena de fecha en formato 'dd/mm/YYYY' a un objeto date de Python si no es None
    fecha_viaje = datetime.strptime(fecha_viaje_str, '%d/%m/%Y').date() if fecha_viaje_str else None

    if fecha_viaje:
        tripulantes_disponibles = DistribucionTripulantes.objects.filter(
            licencia_vencimiento__gt=fecha_viaje,
        ).values()
    else:
        tripulantes_disponibles = DistribucionTripulantes.objects.all().values()

    lista_tripulantes = list(tripulantes_disponibles)
    return JsonResponse({"data": lista_tripulantes})

def get_tripulante_data(id_tripulante):
    from .models import DistribucionTripulantes
    try:
        tripulante = DistribucionTripulantes.objects.filter(id_tripulante=id_tripulante).values(
            'id_tripulante', 'identidad_tripulante', 'nombre_tripulante',
            'numero_licencia', 'id_tipo_tripulante', 'disponibilidad', 'estado'
        ).first()

        
        if tripulante:
            return tripulante
        else:
            return None

    except Exception as e:
        print(e)
        return None

def sumar_valor_flete_tripulante(id_tripulante):
    from .models import DistribucionTripulantesDetalleFlete
    from django.db.models import Sum
    try:
        suma = DistribucionTripulantesDetalleFlete.objects.exclude(
            estado=3
        ).filter(
            id_tripulante=id_tripulante
        ).aggregate(suma_valor_flete=Sum('valor_flete'))

        suma_valor_flete = suma['suma_valor_flete']

        if suma_valor_flete is None:
            suma_valor_flete = 0

        return suma_valor_flete

    except Exception as e:
        print("Error en la función sumar_valor_flete_tripulante: {}".format(e))
        return 0

def obtener_datos_tripulantes(listadoTripulantes):
    tripulantes_data = []

    for id_tripulante in listadoTripulantes:
        data = get_tripulante_data(id_tripulante)
        if data:
            tripulantes_data.append(data)

    return tripulantes_data

def obtener_suma_fletes_tripulantes(listadoTripulantes):
    tripulantes_data = []

    print("si sirve")
    for id_tripulante in listadoTripulantes:
        data = sumar_valor_flete_tripulante(id_tripulante)
        print(data)
        if data:
            tripulantes_data.append(data)

    return tripulantes_data

#------------------------------------------------------------PROCESO PROGRAMACION--------------------------------------------------

@xframe_options_exempt
def vista_modulo_programacion(request):
    return render(request, 'programacion_modal.html')


@xframe_options_exempt
def vista_programacion_all(request):
    return render(request, 'distribuciones_programaciones.html')

#---------------------------------------------------------------PROGRAMACIÓN-------------------------------------------------------
@xframe_options_exempt
def vista_tabla_programaciones(request):
    return render(request, 'tabla_programaciones.html')

def rutas_por_vendedor(request):
    conexion_control_total = connections['control_total_test']
    with conexion_control_total.cursor() as cursor:
        cursor.callproc('CALL SP_GetRutas2ByVendedor()')
        usuarios_data = [dict(zip(cursor.description, row)) for row in cursor.fetchall()]

    return JsonResponse({'rutas': usuarios_data})



@csrf_exempt
def insertar_programacion(request):
    from .models import DistribucionProgramacion, DistribucionProgramacionDestino, DistribucionProgramacionTripulantes, DistribucionProgramacionDetalle
    try:
        data = json.loads(request.body.decode('utf-8'))

        fecha_str = data.get('fecha', None)
        if fecha_str:
            # Convert string to datetime object
            naive_datetime = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
            # Make it timezone-aware (assuming UTC, change as needed)
            aware_datetime = pytz.utc.localize(naive_datetime)
            _fecha = aware_datetime
        else:
            _fecha = None
        _id_vehiculo = data.get('id_vehiculo', None)
        _utilidad_operativa = data.get('utilidad_operativa', None)
        _utilidad_total = data.get('utilidad_total', None)
        _volumen = data.get('volumen', None)
        _peso_total = data.get('peso_total', None)
        _cantidad_facturas = data.get('cantidad_facturas', None)
        _cantidad_clientes = data.get('cantidad_clientes', None)
        _rentabilidad = data.get('rentabilidad', None)
        _cantidad_productos = data.get('cantidad_productos', None)
        _estado = data.get('estado', None)
        _creado_por = data.get('creado_por', None)
        _fecha_hora_creado = data.get('fecha_hora_creado', None)
        listado_destinos = data.get('listaSeleccionados', None)
        listado_tripulantes = data.get('listaTripulantesSeleccionados', None)
        listado_consolidados = data.get('listaConsolidados', None)
        print(listado_destinos,"Destinos")
        print(listado_consolidados, "Consolidados")
        print(listado_tripulantes, "tripulantes")

        #datos_tripulantes= obtener_datos_tripulantes(listado_tripulantes)
        fletes_tripulantes = obtener_suma_fletes_tripulantes(listado_tripulantes)
        fletes_destinos = obtener_suma_fletes_destinos(listado_destinos)
        fletes_vehiculos = sumar_valor_flete_vehiculo(_id_vehiculo)
        #prueba = fletes_tripulantes + fletes_destinos + fletes_vehiculos
        #print(fletes_vehiculos)

        #print(datos_tripulantes, "datos")
        #print(fletes_vehiculos)
   
        programacion = DistribucionProgramacion(
            fecha=_fecha,
            id_vehiculo=_id_vehiculo,
            utilidad_operativa=_utilidad_operativa,
            utilidad_total=_utilidad_total,
            volumen=_volumen,
            peso_total=_peso_total,
            cantidad_facturas=_cantidad_facturas,
            cantidad_clientes=_cantidad_clientes,
            rentabilidad=_rentabilidad,
            cantidad_productos=_cantidad_productos,
            estado= 1,
            creado_por=_creado_por,
            fecha_hora_creado=_fecha_hora_creado
        )
        programacion.save()

        errores_destinos = []
        for id_destino in listado_destinos:
            try:
                destino = DistribucionProgramacionDestino(
                    id_programacion=programacion.id_programacion,
                    id_destino=id_destino,
                    estado= 1,
                )
                destino.save()
            except Exception as e:
                errores_destinos.append(str(e))

        # Inserción para tripulantes
        errores_tripulantes = []
        for id_tripulante in listado_tripulantes:
            try:
                tripulante = DistribucionProgramacionTripulantes(
                    id_programacion=programacion.id_programacion,
                    id_tripulante=id_tripulante,
                    estado= 1,
                )
                tripulante.save()
            except Exception as e:
                errores_tripulantes.append(str(e))
        
        errores_detalles = []
        for id_consolidado in listado_consolidados:
            try:
                detalle = DistribucionProgramacionDetalle(
                    id_programacion=programacion.id_programacion,
                    id_consolidado=id_consolidado,
                    estado= 1,
                )
                detalle.save()
            except Exception as e:
                errores_detalles.append(str(e))

        # Comprueba si hubo errores y decide qué hacer
        if errores_destinos or errores_tripulantes:
            # Aquí puedes decidir si quieres devolver un error o no
            print("Errores en destinos:", errores_destinos)
            print("Errores en tripulantes:", errores_tripulantes)
            print("Errores en detalles:", errores_detalles)

        # Devuelve una respuesta JSON de éxito
        return JsonResponse({'message': 'Registro insertado correctamente'})
    
    except Exception as e:
        # Manejo de excepciones y respuesta de error
        return JsonResponse({'error': str(e)}, status=500)


def obtener_programaciones_data(request):
    conexion_dac = connections['dac']
    with conexion_dac.cursor() as cursor:
        cursor.execute("CALL DISTRIBUCION_OBTENER_PROGRAMACION")
        column_names = [col[0] for col in cursor.description]
        rows = [list(row) for row in cursor.fetchall()]

    df = pd.DataFrame(rows, columns=column_names)

    # Reemplazar NaN con None
    df = df.where(pd.notnull(df), None)

    # Excluir 'id_programacion_detalle'
    df = df.drop(columns=['id_programacion_detalle'])

    # Convertir y formatear columnas de fecha y hora
    format = '%Y-%m-%d %H:%M:%S' # El formato deseado
    for column in ['fecha']:
        df[column] = pd.to_datetime(df[column]).dt.strftime(format)

    # Agrupar y combinar registros
    programaciones_agrupadas = df.groupby('id_programacion').first().reset_index()

    # Convertir el resultado a JSON
    result = programaciones_agrupadas.to_dict(orient='records')

    return JsonResponse({'programaciones': result})


#--------------------------------------------------------------PROCESOS------------------------------------------------------------


def obtener_datos_programacion(request, id_programacion):
    from .models import DistribucionProgramacionHistorial
    # Obtener el historial asociado a esta ID de programación
    programacion_historial = get_object_or_404(DistribucionProgramacionHistorial, id_programacion=id_programacion)

    def format_datetime(dt):
        return format(dt, 'Y-m-d H:i') if dt else ''

    data = {
        'id_programacion': programacion_historial.id_programacion,
        'hora_carga_inicio': format_datetime(programacion_historial.hora_carga_inicio),
        'hora_carga_fin': format_datetime(programacion_historial.hora_carga_fin),
        'hora_entrega': format_datetime(programacion_historial.hora_entrega),
        'hora_regreso_esperado': format_datetime(programacion_historial.hora_fecha_esperado),
        'hora_regreso': format_datetime(programacion_historial.hora_regreso),
        # Incluye aquí los demás campos si es necesario
    }

    return JsonResponse(data)

from django.utils.dateparse import parse_datetime

def parse_fecha(fecha_str):
    if fecha_str:
        # Intenta parsear la fecha; ajusta el formato si es necesario
        return parse_datetime(fecha_str) or datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
    return None

@csrf_exempt
def actualizar_programacion_historial(request, id_programacion):
    from .models import DistribucionProgramacionHistorial
    if request.method == 'POST':
        programacion_historial = get_object_or_404(DistribucionProgramacionHistorial, id_programacion_historial=id_programacion)
        print(request.body)
        # Parsea y actualiza las fechas si es necesario
        programacion_historial.hora_fecha_carga_inicio = parse_fecha(request.POST.get('hora_inicio_carga')) or programacion_historial.hora_fecha_carga_inicio
        programacion_historial.hora_fecha_carga_fin = parse_fecha(request.POST.get('hora_fin_carga')) or programacion_historial.hora_fecha_carga_fin
        programacion_historial.hora_fecha_entrega = parse_fecha(request.POST.get('hora_entrega')) or programacion_historial.hora_fecha_entrega
        programacion_historial.hora_fecha_esperado = parse_fecha(request.POST.get('hora_regreso_esperado')) or programacion_historial.hora_fecha_esperado
        programacion_historial.hora_fecha_regreso = parse_fecha(request.POST.get('hora_regreso')) or programacion_historial.hora_fecha_regreso

        programacion_historial.hora_fecha_modificacion = timezone.now()

        # Guardar cambios
        programacion_historial.save()

        # Devolver una respuesta
        return JsonResponse({'status': 'success', 'message': 'Programación actualizada correctamente'})

    else:
        # Si no es POST, devolver un error
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)