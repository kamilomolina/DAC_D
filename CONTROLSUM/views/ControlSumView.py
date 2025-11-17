from django.shortcuts import render
from django.db import connections
from django.http import JsonResponse
import json
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.core.files.storage import default_storage
from urllib.parse import urlparse
import os

# Create your views here.
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from ..models import Suministro, Categoria, Proveedor, Almacen

class SuministroForm(forms.ModelForm):
    class Meta:
        model = Suministro
        fields = [
            'nombre', 
            'descripcion', 
            'categoria', 
            'cantidad_inicial', 
            'cantidad_stock', 
            'precio_unitario', 
            'fecha_adquisicion', 
            'proveedor', 
            'almacen'
        ]
        widgets = {
            'fecha_adquisicion': forms.DateInput(attrs={'type': 'date'}),
        }

# --------------------------------- LOGIN -----------------------------------------------#

def logoutRequest(request):
    request.session.flush()

    token = ''

    return HttpResponseRedirect(reverse('login'))

# --------------------------------- DASHBOARD -----------------------------------------------#

## Panel de Acceso
def panel_controlsuministros(request):
    user_id = request.session.get('user_id', '')

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        #get_accesos_contabilidad(request)
        
        return render(request, 'panel_control_suministros.html')
    
# -------------------------------------------------------------------------------------------- #

def dashboard(request):

    id_usuario = request.session.get('user_id', '')
    
    # Si `varUsuarioGrupo` es `None`, entonces no está llegando bien
    if id_usuario is None:
        return JsonResponse({'error': 'No se recibió el ID del usuario'}, status=400)

    udcConn = connections['ctrlSum']
    with udcConn.cursor() as cursor:
        cursor.callproc('kamilo_testing.SUM_GET_ESTADISTICAS',  [id_usuario])

        # Total de suministros
        total_suministros = cursor.fetchone()[0]
        
        cursor.nextset()  # Pasar al siguiente conjunto de resultados

        # Suministros por categoría
        categorias = []
        for row in cursor.fetchall():
            categorias.append({'categoria': row[0], 'count': row[1]})
        
        cursor.nextset()

        # Suministros por almacén
        almacenes = []
        for row in cursor.fetchall():
            almacenes.append({'almacen': row[0], 'count': row[1]})

        cursor.nextset()

        # Suministros por mes
        suministros_mes = []
        for row in cursor.fetchall():
            suministros_mes.append({'mes': row[0], 'cantidad': row[1]})

        cursor.nextset()

        # Total en Adquisiciones
        # total_costo = cursor.fetchone()[0]


    # Devolver datos en formato JSON
    return JsonResponse({
        #'total_costo': total_costo,
        'total_suministros': total_suministros,
        'categorias': categorias,
        'almacenes': almacenes,
        'suministros_mes': suministros_mes,
    })

# --------------------------------- SECCION DE SUMINISTROS -----------------------------------------------#

def listar_suministros(request):
    suministros = Suministro.objects.all()
    return render(request, 'suministros/listarsum.html', {'suministros': suministros})

# -------------------------- Gestion de Suministros ---------------------------------------#

# LISTADO DE SUMINISTROS 
def listado_suministro_data(request):
    
    suministros_data = ""
    categorias_data = ""
    acreedores_data = ""
    almacenes_data = ""

    try:
        
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_SUMINISTROS", [0, 0])
            column_names = [desc[0] for desc in cursor.description]
            suministros_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        udcConn.close()

        # TOMA LOS DATOS DE LA TABLA CATEGORIAS PARA EL SELECT CATEGORIAS DEL HTML
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_CATEGORIAS", [])
            column_names = [desc[0] for desc in cursor.description]
            categorias_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

        # Cierra la conexión
        udcConn.close()


        # TOMA LOS DATOS DE LA TABLA ALMACEN PARA EL SELECT ALMACEN DEL HTML
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_ALMACENES", [0,0])
            column_names = [desc[0] for desc in cursor.description]
            almacenes_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        udcConn.close()

    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})
    
    context = {
        "suministros": suministros_data,
        "categorias": categorias_data,
        "acreedores": acreedores_data,
        "almacenes": almacenes_data,
        "user_id": request.user.id,  # Pasar el ID del usuario autenticado
    }
    
    return render(request, 'suministros/listarsum.html', context)

# ------------------------------------------------------------------------------------------#

# Función para ejecutar el procedimiento almacenado y obtener el precio unitario
def obtener_precio_unitario_data(request):
    if request.method == "POST":
        id_suministro = request.POST.get('id_suministro')
        
        if not id_suministro:
            return JsonResponse({'error': 'id_suministro no proporcionado'}, status=400)

        try:
            # Ejecutar el procedimiento almacenado
            udcConn = connections['ctrlSum']  # Asegúrate de que esta conexión esté configurada en settings.py
            with udcConn.cursor() as cursor:
                cursor.callproc('SUM_GET_PRECIO_UNITARIO', [id_suministro])
                result = cursor.fetchone()

            if result:
                return JsonResponse({'precio_unitario': result[0]})
            else:
                return JsonResponse({'error': 'No se encontró el suministro.'})
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
# ------------------------------------------------------------------------------------------------------------#



def insertar_actualizar_suministro(request):
    try:
        existe = 0

        # Recibir los datos del formulario
        id_suministros = request.POST.get('id_suministros')
        nombre = request.POST.get('nombre_sum')
        descripcion = request.POST.get('descripcion')
        categoria = request.POST.get('categoria')
        cantidad_inicial = request.POST.get('cantidad_inicial')
        cantidad_stock = request.POST.get('cantidad_stock')
        cantidad_minima = request.POST.get('cantidad_minima')
        precio = request.POST.get('precio_unitario')
        fecha = request.POST.get('fecha_adquisicion')
        almacen = request.POST.get('almacen')
        
        # Obtener archivo e imagen actual
        imagen_suministro = request.FILES.get('imagen_suministro')
        imagen_actual = request.POST.get('imagen_actual')

        # Guardar la imagen si fue subida
        if imagen_suministro:
            # Guardamos la imagen usando el sistema de archivos de Django
            imagen_path = default_storage.save(f'suministros/{imagen_suministro.name}', imagen_suministro)
            imagen_url = default_storage.url(imagen_path)  # La URL de la imagen guardada
        
        elif imagen_actual:
            # Extraer solo la ruta relativa desde /media/
            ruta_media = urlparse(imagen_actual).path  # /media/suministros/nombre.jpg
            imagen_path = os.path.relpath(ruta_media, '/media')  # suministros/nombre.jpg
            imagen_url = default_storage.url(imagen_path)

        # Si la imagen no es proporcionada, no se pasa la URL de la imagen
        else:
            imagen_url = None

        userName = request.session.get('userName', '')
        fkgrupo = request.POST.get('fkgrupo')
        acreedor = request.POST.get('id_proveedor')

        # Conexión a la base de datos
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc('SUM_INSERT_UPDATE_SUMINISTRO', [
                id_suministros,
                nombre,
                descripcion,
                categoria,
                cantidad_inicial,
                cantidad_stock,
                cantidad_minima,
                precio,
                fecha,
                almacen,
                imagen_url,  # Pasar la URL de la imagen al procedimiento almacenado
                0,
                userName,
                fkgrupo,
                acreedor
            ])

            results = cursor.fetchall()

            cursor.execute('SELECT @_SUM_INSERT_UPDATE_SUMINISTRO_12')
            guardado = cursor.fetchone()[0]

            if guardado == 1:
                existe = 0
            else:
                existe = 2
        
        udcConn.close()

        # Retornar respuesta JSON
        datos = {'save': 1, 'existe': existe, 'imagen_url': imagen_url, 'guardado': guardado}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)

#-----------------------------------------------------------------------------------------------------#

def actualizar_estado_sum(request):
    if request.method == "POST":
        suministro_id = request.POST.get('id_suministros')
        estadoS = request.POST.get('estado')  # Obtener el estado nuevo

        # Validación de los parámetros
        if not suministro_id or not estadoS:
            return JsonResponse({'success': False, 'error': 'Faltan parámetros requeridos.'})

        try:
            # Llamamos al procedimiento almacenado para actualizar el estado de la requisición
            udcConn = connections['ctrlSum']  # Usa la conexión correcta para la base de datos
            with udcConn.cursor() as cursor:
                cursor.callproc('ACTUALIZAR_ESTADO_SUMINISTRO', [suministro_id, estadoS])

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
# ------------------------------------------------------------------------------------------------------------ #

# Obtiene los suministros bajos en stock
def obtener_stock_bajo_data(request):
    stock_bajo = []

    try:
        # Establece la conexión con la base de datos
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Llamada al procedimiento almacenado
            cursor.callproc("OBTENER_STOCK_BAJOS", [])
            
            # Obtener los nombres de las columnas
            column_names = [desc[0] for desc in cursor.description]
            
            # Obtener los resultados y convertirlos a un diccionario
            stock_bajo = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            #print(stock_bajo)  # Verifica qué datos están siendo devueltos

        
        # Si no se encontraron resultados, se devuelve un mensaje adecuado
        if not stock_bajo:
            return JsonResponse({'message': 'No se encontraron suministros con stock bajo.'}, status=404)
        
        # Devolver los resultados en formato JSON
        return JsonResponse({'suministros_bajos': stock_bajo}, status=200)
    
    except Exception as e:
        # Manejo de errores y respuesta con código de error 500
        return JsonResponse({'error': str(e)}, status=500)
        
# -------------------------------------------------------------------------------------- #

def obtener_acreedores(request):
    try:
        # Conexión a la base de datos usando el alias 'ctrlSum' (puedes usar el alias que necesites)
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Ejecutamos la consulta SQL para obtener los acreedores
            cursor.execute("""
                SELECT * 
                FROM kamilo_testing.ct_proveedores cp
                WHERE cp.acreedor = 1;
            """)
            
            # Obtener los nombres de las columnas
            column_names = [desc[0] for desc in cursor.description]
            
            # Obtener los resultados y convertirlos a un diccionario
            acreedores_data = [
                dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
            ]
            
            # Si hay datos, devolverlos como un JsonResponse
            return JsonResponse({'acreedores': acreedores_data})
    
    except Exception as e:
        # Manejo de excepciones y errores en la ejecución
        print(f"Error en la ejecución de la consulta o conexión: {str(e)}")
        return JsonResponse({'error': f'Ocurrió un error: {str(e)}'})
    
# -------------------------------------------------------------------------------------- #

# LISTADO DE ASIGNACIONES
def listado_asignaciones_data(request):
    
    asignaciones_data = ""
    categorias_data = ""
    usuarios_data = ""

    try:
        # TOMA LOS LOS DATOS DE LA TABLA SUMINISTROS
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_ASIGNACIONES", [0])
            column_names = [desc[0] for desc in cursor.description]
            asignaciones_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        udcConn.close()

        # TOMA LOS DATOS DE LA TABLA CATEGORIAS PARA EL SELECT CATEGORIAS DEL HTML
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_CATEGORIAS", [])
            column_names = [desc[0] for desc in cursor.description]
            categorias_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

        # Cierra la conexión
        udcConn.close()

        # TOMA LOS DATOS DE LA TABLA USUARIOS PARA EL SELECT USUARIOS DEL HTML
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_USUARIOS", [])
            column_names = [desc[0] for desc in cursor.description]
            usuarios_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

        # Cierra la conexión
        udcConn.close()

    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})
    
    context = {
        "asignaciones": asignaciones_data,
        "categorias": categorias_data,
        "usuarios": usuarios_data
    }
    
    return render(request, 'suministros/listar_asignaciones.html', context)

#--------------------------------------------------------------------------------------------------------------#

# -------------- Insertar y Actualizacion Asignacion ------------------ #
def insertar_actualizar_asignacion(request):
    try:
        existe = 0

        # Recuperar los datos del formulario (o de la solicitud POST)
        id_asignacion = request.POST.get('id_asignacion')  
        usuario = request.POST.get('usuario')
        nombre_completo = request.POST.get('nombre_completo')
        grupos = request.POST.get('grupos')
        categoria = request.POST.get('categoria')
        suministro = request.POST.get('suministro')
        cantidad = request.POST.get('cantidad')
        comentario = request.POST.get('comentario')

        userName = request.session.get('userName', '')

        # Iniciar una conexión a la base de datos
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Llamar al procedimiento almacenado para insertar o actualizar la asignación
            cursor.callproc('SUM_INSERT_UPDATE_ASIGNACION', [
                id_asignacion,
                usuario,
                nombre_completo,
                grupos,
                categoria,
                suministro,
                cantidad,
                comentario,
                0,
                userName
            ])


            cursor.execute('SELECT @_SUM_INSERT_UPDATE_ASIGNACION_8')
            guardado = cursor.fetchone()[0]

            if guardado == 1:
                existe = 0
            else:
                existe = 2

        # Si todo sale bien, devolvemos un mensaje de éxito
        datos = {'save': 1, 'existe': existe}
    
    except Exception as e:
        # En caso de error, se captura y devuelve el error
        datos = {'save': 0, 'error': str(e)}
    
    # Retornar la respuesta JSON
    return JsonResponse(datos)

# ----------------------------------------------------------------------------------------------------- #

# Obtiene los datos de la tabla Suministros
def get_suministros_data (request):
    varEstado = int(request.POST.get('varEstado'))  # Convertir a entero, por defecto es 0
    id_usuario = request.session.get('user_id', '')
    
    # Si `varUsuarioGrupo` es `None`, entonces no está llegando bien
    if id_usuario is None:
        return JsonResponse({'error': 'No se recibió el ID del usuario'}, status=400)

    suministros_data = ''

    try:

        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_SUMINISTROS", [varEstado, id_usuario])
            column_names = [desc[0] for desc in cursor.description]
            suministros_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': suministros_data})
    except Exception as e:
        return JsonResponse({'error': str(e)})

# ----------------------------------------------------------------------------------------------------- #

# Obtiene los grupos depende el usuario
def get_grupos_por_usuario(request):
    # Obtener el id del usuario desde la sesión
    id_usuario = request.session.get('user_id', '')
    
    if not id_usuario:
        return JsonResponse({'error': 'No hay usuario en sesión'}, status=400)

    # Asegurarse de que id_usuario sea un número entero
    try:
        id_usuario = int(id_usuario)  # Convertimos id_usuario a int
    except ValueError:
        return JsonResponse({'error': 'El ID de usuario no es válido'}, status=400)

    grupos_data = []

    try:
        # Establecer la conexión a la base de datos
        udcConn = connections['ctrlSum']
        
        # Asegurarse de que la conexión se haya establecido correctamente
        if not udcConn:
            raise Exception("No se pudo establecer la conexión con la base de datos.")
        
        with udcConn.cursor() as cursor:
            # Consultamos los grupos del usuario en la base de datos
            sql = """
            SELECT 
                ug.fkUsuario,
                u.Nombre AS UsuarioNombre,
                g.PKgrupo,
                g.Nombre AS GrupoNombre
            FROM global_security.usuarios_grupo ug
            INNER JOIN global_security.grupos g
                ON ug.fkGrupo = g.PKgrupo
            INNER JOIN global_security.usuarios u
                ON u.PKUsuario = ug.fkUsuario
            WHERE ug.fkUsuario = %s
            """
            cursor.execute(sql, [id_usuario])  # Usamos %s para evitar inyecciones SQL
            column_names = [desc[0] for desc in cursor.description]
            grupos_data = [dict(zip(column_names, row)) for row in cursor.fetchall()]

        udcConn.close()

        if not grupos_data:
            raise Exception("No se encontraron grupos para el usuario.")

        # Devolver los grupos en formato JSON
        return JsonResponse({'data': grupos_data})
    
    except Exception as e:
        # Capturar cualquier excepción y devolverla como respuesta JSON con estado 500
        print(f"Error en la vista get_grupos_por_usuario: {str(e)}")  # Para depuración
        return JsonResponse({'error': str(e)}, status=500)

# ----------------------------------------------------------------------------------------------------- #

def get_almacenes_por_usuario(request):
    id_usuario = request.session.get('user_id', '')
    
    # Verificar si id_usuario está disponible y es válido
    if not id_usuario:
        return JsonResponse({'error': 'No hay usuario en sesión'}, status=400)

    almacen_data = []

    try:
        # Asegurarse de que id_usuario es un número entero
        id_usuario = int(id_usuario)

        # Establecer la conexión a la base de datos
        udcConn = connections['ctrlSum']
        
        with udcConn.cursor() as cursor:
            # Consulta SQL para obtener los almacenes asociados al usuario
            sql = """
            SELECT 
                ug.fkUsuario,
                u.Nombre AS UsuarioNombre,
                g.PKgrupo,
                g.Nombre AS GrupoNombre,
                a.id_almacen,
                a.nombre_almacen AS NombreAlmacen
            FROM global_security.usuarios_grupo ug
            INNER JOIN global_security.grupos g
                ON ug.fkGrupo = g.PKgrupo
            INNER JOIN kamilo_testing.almacen a
                ON ug.fkGrupo = a.fkgrupo
            INNER JOIN global_security.usuarios u
                ON u.PKUsuario = ug.fkUsuario
            WHERE ug.fkUsuario = %s
            """
            cursor.execute(sql, [id_usuario])  # Usar %s para pasar el parámetro de forma segura
            column_names = [desc[0] for desc in cursor.description]
            almacen_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

        udcConn.close()

        # Devolver la respuesta con los datos de los almacenes
        return JsonResponse({'data': almacen_data})
    
    except Exception as e:
        # Capturar cualquier excepción y devolverla como respuesta JSON con estado 500
        return JsonResponse({'error': str(e)}, status=500)
    
# ----------------------------------------------------------------------------------------------------- #

def obtener_suministros_por_categoria_data(request):
    categoria_id = request.POST.get('categoria_id')
    id_usuario = request.session.get('user_id', '')
    
    # Verificar si id_usuario está disponible y es válido
    if not id_usuario:
        return JsonResponse({'error': 'No hay usuario en sesión'}, status=400)

    if categoria_id:
        try:
            # Conexión a la base de datos
            udcConn = connections['ctrlSum']  # Asegúrate de usar el nombre correcto de la conexión
            with udcConn.cursor() as cursor:
                # Llamar al procedimiento almacenado con el ID de la categoría
                cursor.callproc('SUM_GET_SUMINISTROS_CATEGORIA', [categoria_id, id_usuario])

                # Obtener los resultados de la consulta
                column_names = [desc[0] for desc in cursor.description]
                suministros_data = [
                    dict(zip(column_names, row)) for row in cursor.fetchall()
                ]

            if suministros_data:
                return JsonResponse({'suministros': suministros_data})
            else:
                return JsonResponse({'error': 'No se encontraron suministros para esta categoría.'})

        except Exception as e:
            return JsonResponse({'error': str(e)})

    return JsonResponse({'error': 'No se recibió un id de categoría válido.'})

# ----------------------------------------------------------------------------------------------------- #

def obtener_asignacion_data(request):
    id_asignacion = request.GET.get('id_asignacion')

    if not id_asignacion:
        return JsonResponse({'error': 'ID de asignación no proporcionado'}, status=400)

    try:
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc('SUM_GET_ASIGNACIONES', [0])  # Ajusta el filtro según lo necesario
            resultado = cursor.fetchall()

        # Buscar la asignación específica en los resultados
        asignacion = next(({
            'id_asignacion': row[0],
            'PKUsuario': row[1],
            'Nombre': row[2],
            'Usuario': row[3],
            'PKgrupo': row[4],
            'GrupoNombre': row[5],
            'id_categoria': row[6],
            'nombre_categoria': row[7],
            'id_suministros': row[8],
            'nombre': row[9],
            'cantidad_asignacion': row[10],
            'comentario': row[11],
            'fecha_asignacion': str(row[12]),
            'estado': row[13],
            'fecha_hora_creacion': str(row[14]),
            'fecha_hora_modificado': str(row[15]),
            'creado_por': str(row[16]),
        } for row in resultado if row[0] == int(id_asignacion)), None)

        if asignacion:
            return JsonResponse({'asignacion': asignacion})
        else:
            return JsonResponse({'error': 'No se encontró la asignación'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# -------------------------------------------------------------------------------------- #

# def proveedores_por_categoria_data(request):
#     categoria_id = request.POST.get('id_categoria')
#     #print(f"Categoria ID recibido: {categoria_id}")  //Depuración

#     # Verificar que el id de la categoría no esté vacío
#     if categoria_id:
#         try:
#             # Convertimos el id a entero para evitar posibles problemas de tipo
#             categoria_id = int(categoria_id)
#             # Conexión a la base de datos
#             udcConn = connections['ctrlSum']
#             with udcConn.cursor() as cursor:
#                 # Llamar al procedimiento almacenado con el id de la categoría
#                 cursor.callproc("SUM_GET_PROVEEDORES_CATEGORIAS", [categoria_id])
#                 column_names = [desc[0] for desc in cursor.description]
#                 proveedores_data = [
#                     dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
#                 ]

#             # Cierra la conexión
#             udcConn.close()

#             # Devolver los proveedores en formato JSON
#             return JsonResponse({'proveedores': proveedores_data})

#         except Exception as e:
#             # Manejo de excepciones
#             return JsonResponse({'error': str(e)})

#     # Si no se recibió un ID de categoría válido
#     return JsonResponse({'error': 'No se recibió un id de categoría válido.'})

# ---------------------------------------------------------------------------------------------------------#
# --------------------------------- SECCION DE ASIGNACIONES -----------------------------------------------#

def listar_asignaciones(request):
    asignaciones = asignaciones.objects.all()
    return render(request, 'suministros/listar_asignaciones.html', {'asignaciones': asignaciones})

# --------------------------------- GESTION DE ASIGNACIONES -----------------------------------------------#

# Obtiene los datos de la tabla Asignaciones
def get_asignaciones_data (request):
    varEstado = int(request.POST.get('varEstado'))  # Convertir a entero, por defecto es 0
    asignaciones_data = ''

    try:
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_ASIGNACIONES", [varEstado])
            column_names = [desc[0] for desc in cursor.description]
            asignaciones_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': asignaciones_data})
    except Exception as e:
        return JsonResponse({'error': str(e)})

#----------------------------------------------------------------------------------------------------#

def obtener_usuario_por_nombre_data(request):
    pk_usuario = request.POST.get('PKUsuario')  # Obtener el PKUsuario desde el request
    print(f"PKUsuario recibido en el backend: {pk_usuario}")  # Depuración

    # Verificar si se recibió un PKUsuario válido
    if not pk_usuario or not pk_usuario.isdigit():
        return JsonResponse({'error': 'No se recibió un PKUsuario válido.'})

    try:
        # Convertir pk_usuario a entero
        pk_usuario = int(pk_usuario)

        # Conexión a la base de datos usando el alias 'ctrlSum'
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Llamamos al procedimiento almacenado con el PKUsuario como parámetro
            cursor.callproc("SUM_GET_NOMBREC_USUARIOS", [pk_usuario])

            # Obtener los resultados del procedimiento almacenado
            column_names = [desc[0] for desc in cursor.description]
            usuario_data = [
                dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
            ]

            # Depuración: Ver qué datos se obtienen
            print(f"Datos recibidos del procedimiento almacenado: {usuario_data}")

            # Si hay datos, extraemos el nombre de usuario
            if usuario_data:
                usuario = usuario_data[0].get('Usuario')  # Suponiendo que 'Usuario' es el nombre de la columna
            else:
                usuario = None

        # Si se encontró el usuario, lo devolvemos; si no, retornamos un error
        if usuario:
            return JsonResponse({'usuario': usuario})
        else:
            return JsonResponse({'error': 'Usuario no encontrado.'})

    except Exception as e:
        # Manejo de excepciones y errores en la ejecución
        print(f"Error en la ejecución del procedimiento o conexión: {str(e)}")
        return JsonResponse({'error': f'Ocurrió un error: {str(e)}'})

# ---------------------------------------------------------------------------------------------------- #

def actualizar_estado_asignacion(request):
    if request.method == "POST":
        asignacion_id = request.POST.get('id_asignacion')
        estadoA = request.POST.get('estado')  # Obtener el estado nuevo

        # Validación de los parámetros
        if not asignacion_id or not estadoA:
            return JsonResponse({'success': False, 'error': 'Faltan parámetros requeridos.'})

        try:
            # Llamamos al procedimiento almacenado para actualizar el estado de la requisición
            udcConn = connections['ctrlSum']  # Usa la conexión correcta para la base de datos
            with udcConn.cursor() as cursor:
                cursor.callproc('ACTUALIZAR_ESTADO_ASIGNACION', [asignacion_id, estadoA])

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        

# ------------------------------------- SECCION DE REQUISICIONES --------------------------------------------------- #   

def listado_requisicion_data(request):

    requisicion_data = ""
    categorias_data = ""
    acreedores_data = ""

    try:
        # TOMA LOS LOS DATOS DE LA TABLA REQUISICION
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("GET_REQUISICIONES", [0])
            column_names = [desc[0] for desc in cursor.description]
            requisicion_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        udcConn.close()

        # TOMA LOS DATOS DE LA TABLA CATEGORIAS PARA EL SELECT CATEGORIAS DEL HTML
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_CATEGORIAS", [])
            column_names = [desc[0] for desc in cursor.description]
            categorias_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

        # Cierra la conexión
        udcConn.close()

    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})
    
    context = {
        "requisicion": requisicion_data,
        "categorias": categorias_data,
        "acreedores": acreedores_data
    }
    return render(request, 'suministros/listado_requisiciones.html', context)  

# ----------------------------------------------------------------------------------------------------------------------------- #

def obtener_detalles_requisicion_data(request):
    # Obtener el ID de la requisición desde la solicitud
    id_requisicion = request.GET.get('id_requisicion')

    if not id_requisicion:
        return JsonResponse({'error': 'No se proporcionó un ID de requisición válido.'})

    try:
        # Conectar a la base de datos y ejecutar el procedimiento almacenado
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc('GET_DETALLES_REQUISICION', [id_requisicion])
            
            # Obtener los resultados
            column_names = [desc[0] for desc in cursor.description]
            detalles_requisicion = [
                dict(zip(column_names, row)) for row in cursor.fetchall()
            ]
        
        # Retornar la respuesta en formato JSON
        return JsonResponse({'detalles': detalles_requisicion})

    except Exception as e:
        return JsonResponse({'error': f'Ocurrió un error: {str(e)}'})


# ----------------------------------------------------------------------------------------------------------------------------- #
def obtener_requisicion_y_detalle_data(request):
    # Obtener el ID de la requisición desde la solicitud
    id_requisicion = request.GET.get('id_requisicion')

    if not id_requisicion:
        return JsonResponse({'error': 'No se proporcionó un ID de requisición válido.'})

    try:
        # Conectar a la base de datos y ejecutar el procedimiento almacenado
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Llamar al procedimiento almacenado que obtiene la requisición y los detalles
            cursor.callproc('GET_REQUISICION_Y_DETALLES', [id_requisicion])
            
            # Obtener los resultados de la requisición
            column_names = [desc[0] for desc in cursor.description]
            requisicion_data = dict(zip(column_names, cursor.fetchone()))  # solo un resultado para la requisición

            # Obtener los resultados de los detalles
            cursor.nextset()  # Mover al siguiente conjunto de resultados (detalles)
            column_names = [desc[0] for desc in cursor.description]
            detalles_requisicion = [
                dict(zip(column_names, row)) for row in cursor.fetchall()
            ]
        
        # Retornar la respuesta en formato JSON con los datos de la requisición y los detalles
        return JsonResponse({
            'requisicion': requisicion_data,
            'detalles': detalles_requisicion
        })

    except Exception as e:
        return JsonResponse({'error': f'Ocurrió un error: {str(e)}'})

# ----------------------------------------------------------------------------------------------------------------------------- #

# Obtiene los datos de la tabla requisicion
def get_requisicion_data (request):
    varEstado = int(request.POST.get('varEstado'))  # Convertir a entero, por defecto es 0
    requisicion_data = ''

    try:
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("GET_REQUISICIONES", [varEstado])

            column_names = [desc[0] for desc in cursor.description]
            requisicion_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': requisicion_data})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
# --------------------------------------------------------------------------------------------------------------- #

# Obtiene los datos de la tabla usuarios
def obtener_nombres_usuarios_data (request):
    
    try:
        # Conexión a la base de datos y ejecución del procedimiento almacenado
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Llamar al procedimiento almacenado
            cursor.callproc("GET_NOMBRES", [])
            column_names = [desc[0] for desc in cursor.description]
            usuarios_data = [
                dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
            ]
        
        udcConn.close()
        
        return JsonResponse({'usuarios': usuarios_data})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
# -------------------------------------------------------------------------------------- #

def insertar_actualizar_requisicion_data(request):
    try:
        existe = 0

        # Verificar qué datos están llegando
        print(request.POST)

        id_requisicion = request.POST.get('id_requisicion')
        if not id_requisicion:
            id_requisicion = None  # Esto permitirá al procedimiento almacenado insertar una nueva requisición

        # Recuperar los demás datos del formulario
        PKUsuario = request.POST.get('PKUsuario')
        PKgrupo = request.POST.get('PKgrupo')
        id_proveedor = request.POST.get('id_proveedor')
        fecha_pedido = request.POST.get('fecha_pedido')
        fecha_pago = request.POST.get('fecha_pago')
        costo_total = request.POST.get('costo_total')
        estado_requisicion = request.POST.get('estado_requisicion', 1)
        estado = request.POST.get('estado')

        userName = request.session.get('userName', '')

        # Validar que los valores esenciales no estén vacíos
        if not PKUsuario or not PKgrupo or not id_proveedor or not fecha_pedido or not fecha_pago or not costo_total:
            raise ValueError("Faltan datos requeridos en la requisición.")
        
        # Validar que los valores numéricos sean positivos
        if float(costo_total) <= 0:
            raise ValueError("El costo total debe ser un valor positivo.")

        with transaction.atomic():  # Usar transacción para asegurar que todo sea consistente
            udcConn = connections['ctrlSum']
            with udcConn.cursor() as cursor:
                args = [
                    id_requisicion if id_requisicion else 0,  # Enviar 0 si es nuevo
                    PKUsuario, 
                    PKgrupo,
                    id_proveedor, 
                    fecha_pedido, 
                    fecha_pago, 
                    costo_total, 
                    estado_requisicion,
                    estado, 
                    0,  # OUT parameter inicializado
                    userName
                ]
                cursor.callproc('SUM_INSERT_UPDATE_REQUISICION', args)

                # Recuperar el valor OUT después de la ejecución
                cursor.execute('SELECT @_SUM_INSERT_UPDATE_REQUISICION_9')
                p_result_id_requisicion = cursor.fetchone()[0]

                if p_result_id_requisicion == id_requisicion :
                    existe = 1
                    
        datos = {'save': 1, 'id_requisicion': p_result_id_requisicion, 'existe': existe, 'message': '✅ Requisición procesada correctamente.'}

    except Exception as e:
        print(e)
        datos = {'save': 0, 'error': f'⚠️ Error: {str(e)}'}

    return JsonResponse(datos)

# ---------------------------------------------------------------------------------------------- #

def insertar_actualizar_detalle_requisicion_data(request):
    try:
        id_requisicion = request.POST.get('id_requisicion')
        detalles = json.loads(request.POST.get('detalles'))

        if not detalles:
            raise ValueError("No se han agregado detalles para la requisición.")

        with transaction.atomic():
            udcConn = connections['ctrlSum']
            with udcConn.cursor() as cursor:
                for detalle in detalles:
                    # Validar cada detalle
                    if not detalle.get('id_suministros') or not detalle.get('cantidad') or not detalle.get('precio_unitario') or not detalle.get('justificacion'):
                        raise ValueError("Faltan datos en los detalles de la requisición.")
                    if detalle['cantidad'] <= 0 or detalle['precio_unitario'] <= 0:
                        raise ValueError("La cantidad y el precio unitario deben ser mayores a cero.")
                    if not detalle['justificacion'].strip():
                        raise ValueError("La justificación no puede estar vacía.")

                    # Llamar al procedimiento almacenado incluyendo la justificación
                    cursor.callproc('SUM_INSERT_UPDATE_DETALLE_REQUISICION', [
                        detalle.get('id_detalle_requisicion', 0), 
                        id_requisicion,
                        detalle['id_suministros'],
                        detalle['cantidad'],
                        detalle['precio_unitario'],
                        detalle['justificacion']
                    ])

        datos = {'save': 1, 'message': 'Detalles de requisición guardados correctamente.'}

    except Exception as e:
        datos = {'save': 0, 'error': f'⚠️ Error: {str(e)}'}

    return JsonResponse(datos)


# -------------------------------------------------------------------------------------------------------------------------------------- #

# CAMBIAR EL ESTADO DE REQUISICION

# Función para ejecutar el procedimiento almacenado que cambia el estado
def ejecutar_procedimiento(requisicion_id):
    try:
        # Conexión a la base de datos
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Llamar al procedimiento almacenado 'CAMBIAR_ESTADO_REQUISICION'
            cursor.callproc('kamilo_testing.CAMBIAR_ESTADO_REQUISICION', [requisicion_id])
            # Si deseas capturar el resultado, puedes usar fetchall() o fetchone()
            cursor.fetchall()
    except Exception as e:
        # En caso de error, imprimir y lanzar la excepción
        raise Exception(f"Error al ejecutar el procedimiento almacenado: {str(e)}")


# Vista que se llama desde el frontend para cambiar el estado
def actualizar_estado(request):
    if request.method == "POST":
        # Obtener el id de la requisición desde la solicitud
        id_requisicion = request.POST.get("id_requisicion")

        # Verifica que el id_requisicion sea válido
        if not id_requisicion:
            return JsonResponse({"success": False, "error": "ID de requisición no proporcionado."})

        try:
            # Ejecutar el procedimiento almacenado para cambiar el estado de la requisición
            ejecutar_procedimiento(id_requisicion)

            # Si no hay errores, se confirma el éxito
            return JsonResponse({"success": True})

        except Exception as e:
            # En caso de error, se maneja la excepción
            return JsonResponse({"success": False, "error": f"Error al ejecutar el procedimiento: {str(e)}"})

# --------------------------------------------------------------------------------------- #

def obtener_detalles_data(request):
    # Obtener el ID de la requisición desde la solicitud
    id_requisicion = request.GET.get('id_requisicion')

    if not id_requisicion:
        return JsonResponse({'error': 'No se proporcionó un ID de requisición válido.'})

    try:
        # Conectar a la base de datos y ejecutar el procedimiento almacenado
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Verificar si la requisición existe
            cursor.execute('SELECT COUNT(*) FROM kamilo_testing.requisicion WHERE id_requisicion = %s', [id_requisicion])
            if cursor.fetchone()[0] == 0:
                return JsonResponse({'error': 'No se encontró la requisición con el ID proporcionado.'})

            # Llamar al procedimiento almacenado
            cursor.callproc('GET_DETALLES_REQUISICION', [id_requisicion])

            # Obtener los resultados
            column_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            if not rows:
                return JsonResponse({'error': 'No se encontraron detalles para esta requisición.'})

            detalles_requisicion = []
            articulos = []
            detalle = dict(zip(column_names, rows[0]))

            for row in rows:
                row_dict = dict(zip(column_names, row))
                articulo = {
                    'id_detalle_requisicion': row_dict.get('id_detalle_requisicion'),
                    'id_suministros': row_dict.get('id_suministros'),
                    'nombre_suministro': row_dict.get('nombre', ''),  # Nuevo campo
                    'cantidad': row_dict.get('cantidad', 0),
                    'precio_unitario': row_dict.get('precio_unitario', 0),
                    'precio_total': row_dict.get('precio_total', 0)
                }
                articulos.append(articulo)

            detalle['articulos'] = articulos
            detalles_requisicion.append(detalle)

        return JsonResponse({'detalles': detalles_requisicion})

    except Exception as e:
        return JsonResponse({'error': f'Ocurrió un error: {str(e)}'})

# --------------------------------------------------------------------------------------------------------------------------

def editar_detalle_requisicion_data(request):
    if request.method == 'POST':
        try:
            id_detalle = request.POST.get('id_detalle_requisicion')
            id_suministro = request.POST.get('suministro')
            cantidad = request.POST.get('cantidad')
            justificacion = request.POST.get('justificacion')

            udcConn = connections['ctrlSum']
            with udcConn.cursor() as cursor:
                cursor.callproc('EDITAR_DETALLE_REQUISICION', [id_detalle, id_suministro, cantidad, justificacion])

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
# ---------------------------------------------------------------------------------------------------------------------- #

def grupos_por_usuario_data(request):
    if request.method == "POST":
        usuario_id = request.POST.get('usuario_id')

        try:
            # Establece la conexión a la base de datos
            udcConn = connections['ctrlSum']
            with udcConn.cursor() as cursor:
                cursor.callproc("OBTENER_GRUPOS_POR_USUARIO", [usuario_id])
                resultados = cursor.fetchall()

            if not resultados:
                return JsonResponse({"error": "No se encontraron grupos para este usuario"}, status=404)

            # Formatear los datos de los grupos
            grupos = [{"PKgrupo": row[2], "GrupoNombre": row[3]} for row in resultados]

            return JsonResponse({"grupos": grupos})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Solicitud no válida"}, status=400)


# ---------------------------------------------------------------------------------------------------------------------- #

def verificar_detalles_requisicion_data(request):
    id_requisicion = request.GET.get("id_requisicion")

    if not id_requisicion:
        return JsonResponse({"error": "ID de requisición no proporcionado"}, status=400)

    try:
        # Establece la conexión a la base de datos
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("kamilo_testing.GET_DETALLES_REQUISICION", [id_requisicion])
            detalles = cursor.fetchall()

        tiene_detalles = len(detalles) > 0  # Si hay resultados, la requisición tiene detalles
        return JsonResponse({"tiene_detalles": tiene_detalles})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# ---------------------------------------------------------------------------------------------------------------------- #

def actualizar_estado_requisicion(request):
    if request.method == "POST":
        requisicion_id = request.POST.get('id_requisicion')
        estadoR = request.POST.get('estado')  # Obtener el estado nuevo

        # Validación de los parámetros
        if not requisicion_id or not estadoR:
            return JsonResponse({'success': False, 'error': 'Faltan parámetros requeridos.'})

        try:
            # Llamamos al procedimiento almacenado para actualizar el estado de la requisición
            udcConn = connections['ctrlSum']  # Usa la conexión correcta para la base de datos
            with udcConn.cursor() as cursor:
                cursor.callproc('ACTUALIZAR_ESTADO_REQUISICION', [requisicion_id, estadoR])

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
# -----------------------------------------------------------------------------------------------------------------------------

def actualizar_estado_detalle_requisicion_data(request):
    if request.method == "POST":
        detalle_requisicion_id = request.POST.get('id_detalle_requisicion')
        estadoDR = request.POST.get('estado')  # Obtener el estado nuevo

        # Validación de los parámetros
        if not detalle_requisicion_id or not estadoDR:
            return JsonResponse({'success': False, 'error': 'Faltan parámetros requeridos.'})

        try:
            # Llamamos al procedimiento almacenado para actualizar el estado de la requisición
            udcConn = connections['ctrlSum']  # Usa la conexión correcta para la base de datos
            with udcConn.cursor() as cursor:
                cursor.callproc('ACTUALIZAR_ESTADO_DETALLE_REQUISICION', [detalle_requisicion_id, estadoDR])

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
# -----------------------------------------------------------------------------------------------------------------------------

def actualizar_estado_sum(request):
    if request.method == "POST":
        suministro_id = request.POST.get('id_suministros')
        estadoS = request.POST.get('estado')  # Obtener el estado nuevo

        # Validación de los parámetros
        if not suministro_id or not estadoS:
            return JsonResponse({'success': False, 'error': 'Faltan parámetros requeridos.'})

        try:
            # Llamamos al procedimiento almacenado para actualizar el estado de la requisición
            udcConn = connections['ctrlSum']  # Usa la conexión correcta para la base de datos
            with udcConn.cursor() as cursor:
                cursor.callproc('ACTUALIZAR_ESTADO_SUMINISTRO', [suministro_id, estadoS])

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
# ---------------------------------------- SECCION DE PROVEEDORES POR CATEGORIA -------------------------------------------------

# def listado_proveedores_categorias_data(request):
    
#     categorias_data = ""
#     proveedor_data = ""

#     try:
#         # TOMA LOS DATOS DE LA TABLA CATEGORIAS PARA EL SELECT CATEGORIAS DEL HTML
#         udcConn = connections['ctrlSum']
#         with udcConn.cursor() as cursor:
#             cursor.callproc("SUM_GET_CATEGORIAS", [])
#             column_names = [desc[0] for desc in cursor.description]
#             categorias_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

#         # Cierra la conexión
#         udcConn.close()

#         # TOMA LOS DATOS DE LA TABLA PROVEEDORES PARA EL SELECT PROVEEDORES DEL HTML
#         udcConn = connections['ctrlSum']
#         with udcConn.cursor() as cursor:
#             cursor.callproc("GET_PROVEEDORES", [])
#             column_names = [desc[0] for desc in cursor.description]
#             proveedor_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
#         # Cierra la conexión
#         udcConn.close()


#     except Exception as e:
#         # Manejo de excepciones, puedes personalizar esto según tus necesidades
#         return JsonResponse({'error': str(e)})
    
#     context = {
#         "categorias": categorias_data,
#         "proveedores": proveedor_data
#     }
    
#     return render(request, 'suministros/listado_proveedores_categorias.html', context)

# --------------------------------------------------------------------------------------------------------------------------

# PARA CAMBIAR EL ESTADO DE LA SECCION DE PROVEEDORES POR CATEGORIA
# def get_proveedor_categoria_data (request):
#     varEstado = int(request.POST.get('varEstado'))  # Convertir a entero, por defecto es 0
#     proveedorC_data = ''

#     try:
#         udcConn = connections['ctrlSum']
#         with udcConn.cursor() as cursor:
#             cursor.callproc("GET_PROVEEDORES_CATEGORIAS", [varEstado])
#             column_names = [desc[0] for desc in cursor.description]
#             proveedorC_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
#         udcConn.close()
        
#         return JsonResponse({'data': proveedorC_data})
#     except Exception as e:
#         return JsonResponse({'error': str(e)})

# -------------------------------------------------------------------------------------- #

# def insertar_actualizar_proveedor_categoria(request):
#     try:
#         existe = 0

#         id_categorias_proveedores = request.POST.get('id_categorias_proveedores')  
#         id_proveedor = request.POST.get('id_proveedor')
#         id_categoria = request.POST.get('id_categoria')

#         udcConn = connections['ctrlSum']
#         with udcConn.cursor() as cursor:
#             cursor.callproc('SUM_INSERT_UPDATE_PROVEEDOR_CATEGORIA', [
#                 id_categorias_proveedores,
#                 id_proveedor,
#                 id_categoria,
#                 0
#             ]) 

#             cursor.execute('SELECT @_SUM_INSERT_UPDATE_PROVEEDOR_CATEGORIA_3')
#             guardado = cursor.fetchone()[0]

#             if guardado == 1:
#                 existe = 0  # Indica que se insertó un nuevo registro
#             else:
#                 existe = 2  # Indica que se actualizó un registro existente
        
#         udcConn.close()

#         datos = {'save': 1, 'existe': existe}
#     except Exception as e:
#         datos = {'save': 0, 'error': str(e)}
    
#     return JsonResponse(datos)

# -------------------------------------------------------------------------------------------------------------- #

# def actualizar_estado_proveedor_categoria(request):
#     if request.method == "POST":
#         proveedor_categorias_id = request.POST.get('id_categorias_proveedores')
#         estadoPC = request.POST.get('estado')  # Obtener el estado nuevo

#         # Validación de los parámetros
#         if not proveedor_categorias_id or not estadoPC:
#             return JsonResponse({'success': False, 'error': 'Faltan parámetros requeridos.'})

#         try:
#             # Llamamos al procedimiento almacenado para actualizar el estado de la requisición
#             udcConn = connections['ctrlSum']  # Usa la conexión correcta para la base de datos
#             with udcConn.cursor() as cursor:
#                 cursor.callproc('ACTUALIZAR_ESTADO_PROVEEDORES_CATEGORIAS', [proveedor_categorias_id, estadoPC])

#             return JsonResponse({'success': True})

#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)})

# --------------------------------------- SECCION DE ALMACENES  ------------------------------------------------ #

def listado_almacenes_data(request):
    
    almacenes_data = ""

    try:
        # TOMA LOS DATOS DE LA TABLA ALMACEN
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_ALMACENES", [0,0])
            column_names = [desc[0] for desc in cursor.description]
            almacenes_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        udcConn.close()

    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})
    
    context = {
        "almacenes": almacenes_data
    }
    
    return render(request, 'suministros/listado_almacenes.html', context)

#-----------------------------------------------------------------------------------------------------#

# Obtiene los datos de la tabla Almacen
def get_almacenes_data (request):
    varEstado = int(request.POST.get('varEstado'))  # Convertir a entero, por defecto es 0
    id_usuario = request.session.get('user_id', '')
    
    almacen_data = ''

    try:
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_ALMACENES", [varEstado, id_usuario])
            column_names = [desc[0] for desc in cursor.description]
            almacen_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': almacen_data})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
#-----------------------------------------------------------------------------------------------------#

def insertar_actualizar_almacen_data(request):
    try:
        existe = 0

        # Obtener los valores del POST
        id_almacen = request.POST.get('id_almacen')
        nombre_almacen = request.POST.get('nombre_almacen')
        ubicacion_almacen = request.POST.get('ubicacion_almacen')

        userName = request.session.get('userName', '')

        fkgrupo = request.POST.get('fkgrupo')

        # Conexión a la base de datos
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Llamar al procedimiento almacenado para insertar o actualizar el almacén
            cursor.callproc('SUM_INSERT_UPDATE_ALMACEN', [
                id_almacen,
                nombre_almacen,
                ubicacion_almacen,
                0,  # Este valor se utilizará para el parámetro de salida 'guardado'
                userName,
                fkgrupo
            ]) 

            # Obtener el valor del parámetro de salida 'guardado'
            cursor.execute('SELECT @_SUM_INSERT_UPDATE_ALMACEN_3')
            guardado = cursor.fetchone()[0]

            if guardado == 1:
                existe = 0  # Indica que se insertó un nuevo registro
            else:
                existe = 2  # Indica que se actualizó un registro existente
        
        # Cerrar la conexión
        udcConn.close()

        # Datos para la respuesta
        datos = {'save': 1, 'existe': existe}
    
    except Exception as e:
        # Manejo de errores
        datos = {'save': 0, 'error': str(e)}
    
    # Retornar la respuesta en formato JSON
    return JsonResponse(datos)

# ----------------------------------------------------------------------------------------------------------------- #

def actualizar_estado_almacenes(request):
    if request.method == "POST":
        almacen_id = request.POST.get('id_almacen')
        estadoAlmacen = request.POST.get('estado')  # Obtener el estado nuevo

        # Validación de los parámetros
        if not almacen_id or not estadoAlmacen:
            return JsonResponse({'success': False, 'error': 'Faltan parámetros requeridos.'})

        try:
            # Llamamos al procedimiento almacenado para actualizar el estado de la requisición
            udcConn = connections['ctrlSum']  # Usa la conexión correcta para la base de datos
            with udcConn.cursor() as cursor:
                cursor.callproc('ACTUALIZAR_ESTADO_ALMACEN', [almacen_id, estadoAlmacen])

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
# ----------------------------------------------------------------------------------------------------------------- #

# LISTADO DE SUMINISTROS 
def listado_adquisicion_data(request):
    
    adquisicion_data = ""

    try:
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_ADQUISICION", [0])
            column_names = [desc[0] for desc in cursor.description]
            adquisicion_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        udcConn.close()

    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})
    
    context = {
        "adquisicion": adquisicion_data
    }
    
    return render(request, 'suministros/listado_adquisicion.html', context)



# Obtiene los datos de la tabla Adquisicion
def get_adquisicion_data (request):
    varEstado = int(request.POST.get('varEstado'))  # Convertir a entero, por defecto es 0
    adquisicion_data = ''

    try:
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_ADQUISICION", [varEstado])
            column_names = [desc[0] for desc in cursor.description]
            adquisicion_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': adquisicion_data})
    except Exception as e:
        return JsonResponse({'error': str(e)})

# ----------------------------------------------------------------------------------------------------------------- #


def obtener_requisiciones_usuario(request):
    try:
        # Conexión a la base de datos usando el alias 'ctrlSum'
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Llamamos al procedimiento almacenado que a su vez llama a OBTENER_REQUISICION_USUARIO
            cursor.callproc('OBTENER_REQUISICION_USUARIO')

            # Obtener los resultados del procedimiento almacenado
            column_names = [desc[0] for desc in cursor.description]
            requisiciones_data = [
                dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
            ]

            # Si hay datos, devolverlos como un JsonResponse
            return JsonResponse({'requisiciones': requisiciones_data})

    except Exception as e:
        # Manejo de excepciones y errores en la ejecución
        print(f"Error en la ejecución del procedimiento o conexión: {str(e)}")
        return JsonResponse({'error': f'Ocurrió un error: {str(e)}'})
    
# ----------------------------------------------------------------------------------------------------------------- #

def obtener_requisicion_detalles_usuario(request):
    # Asegúrate de que los parámetros 'pk_usuario' y 'id_requisicion' estén presentes en la solicitud
    pk_usuario = request.GET.get('pk_usuario')
    id_requisicion = request.GET.get('id_requisicion')

    if id_requisicion is not None:
        try:
            # Llamar al procedimiento almacenado con los valores de pk_usuario e id_requisicion
            udcConn = connections['ctrlSum']
            with udcConn.cursor() as cursor:
                # Ejecutamos el procedimiento almacenado
                cursor.callproc('GET_REQUISICIONES_Y_DETALLES_USUARIO', [id_requisicion])
                
                # Obtener los resultados de la requisición
                requisicion_result = cursor.fetchall()

                if requisicion_result:
                    # Obtener los valores del grupo y proveedor de la primera fila de resultados
                    id_requisicion = requisicion_result[0][0]  # 'id_requisicion' está en la columna 0
                    grupo_id = requisicion_result[0][3]  # 'GrupoNombre' está en la columna 4
                    grupo_nombre = requisicion_result[0][4]  # 'GrupoNombre' está en la columna 4
                    id_proveedor = requisicion_result[0][5]  # 'nombre_proveedor' está en la columna 6
                    nombre_proveedor = requisicion_result[0][6]  # 'nombre_proveedor' está en la columna 6
                    
                    # Ahora obtenemos los detalles de la requisición
                    cursor.nextset()  # Mover al siguiente conjunto de resultados (detalles de requisición)
                    detalles_result = cursor.fetchall()

                    detalles = []
                    for detalle in detalles_result:
                        detalles.append({
                            'id_detalle_requisicion': detalle[0],  # 'nombre_suministro' está en la columna 3
                            'id_suministros': detalle[2],
                            'nombre_suministro': detalle[3],  # 'nombre_suministro' está en la columna 3
                            'cantidad': detalle[4],            # 'cantidad' está en la columna 4
                            'precio_unitario': detalle[5],     # 'precio_unitario' está en la columna 5
                            'precio_total': detalle[6]         # 'precio_total' está en la columna 6
                        })
                    
                    # Devolver la respuesta en formato JSON
                    return JsonResponse({
                        'success': True,
                        'data': {
                            'id_requisicion': id_requisicion,
                            'grupo_id': grupo_id,
                            'grupo': grupo_nombre,
                            'id_proveedor': id_proveedor,
                            'proveedor': nombre_proveedor,
                            'detalles': detalles
                        }
                    })
                else:
                    return JsonResponse({'success': False, 'message': 'No se encontraron datos.'})

        except Exception as e:
            # Si ocurre un error durante la ejecución del procedimiento
            return JsonResponse({'success': False, 'message': str(e)})
    
    # Si el parámetro pk_usuario no está presente
    return JsonResponse({'success': False, 'message': 'Falta el parámetro pk_usuario'})

# ----------------------------------------------------------------------------------------------------------------- #

def obtener_metodos_pago(request):
    try:
        # Conexión a la base de datos usando el alias 'ctrlSum' (puedes usar el alias que necesites)
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Llamamos al procedimiento almacenado 'OBTENER_METODOS_PAGO'
            cursor.callproc('OBTENER_METODOS_PAGO')
            
            # Obtener los resultados del procedimiento almacenado
            column_names = [desc[0] for desc in cursor.description]  # Obtener nombres de columnas
            metodos_pago_data = [
                dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
            ]
            
            # Si hay datos, devolverlos como un JsonResponse
            return JsonResponse({'metodos_pago': metodos_pago_data})
    
    except Exception as e:
        # Manejo de excepciones y errores en la ejecución
        print(f"Error en la ejecución del procedimiento o conexión: {str(e)}")
        return JsonResponse({'error': f'Ocurrió un error: {str(e)}'})
    
# ----------------------------------------------------------------------------------------------------------------- #

def insertar_actualizar_adquisicion_data(request):
    try:
        existe = 0

        # Valores obtenidos del formulario o petición POST
        id_adquisicion = request.POST.get('id_adquisicion')
        if not id_adquisicion:
            id_adquisicion = None  # Esto permitirá al procedimiento almacenado insertar una nueva requisición 


        id_requisicion = request.POST.get('id_requisicion')
        PKgrupo = request.POST.get('PKgrupo')
        id_proveedor = request.POST.get('id_proveedor')
        fecha_adquisicion = request.POST.get('fecha_adquisicion')
        id_metodo_pago = request.POST.get('id_metodo_pago')
        costo_total = request.POST.get('costo_total')
        estado = request.POST.get('estado')
        userName = request.session.get('userName', '')

        # Conexión a la base de datos
        with transaction.atomic():
            udcConn = connections['ctrlSum']
            with udcConn.cursor() as cursor:
                args = [
                    id_adquisicion if id_adquisicion else 0,
                    id_requisicion,
                    PKgrupo,
                    id_proveedor,
                    fecha_adquisicion,
                    id_metodo_pago,
                    costo_total,
                    estado,
                    0,         # guardado (valor de salida)
                    userName   # userName (valor adicional)
                ]
                cursor.callproc('kamilo_testing.SUM_INSERT_UPDATE_ADQUISICION', args)

                # Obtener el valor del parámetro de salida (guardado)
                cursor.execute('SELECT @_kamilo_testing.SUM_INSERT_UPDATE_ADQUISICION_8')
                guardado = cursor.fetchone()[0]

                if guardado == id_adquisicion :
                    existe = 1
        
            udcConn.close()

        datos = {'save': 1, 'id_adquisicion': guardado, 'existe': existe, 'message': 'Requisición procesada correctamente.' }
    
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)

# ----------------------------------------------------------------------------------------------------------------- #

def insertar_actualizar_detalle_adquisicion_data(request):
    try:
        # Obtenemos el ID de la adquisición y detalles desde el POST
        id_adquisicion = request.POST.get('id_adquisicion')  # Corregido el nombre del campo a 'id_adquisicion'
        id_requisicion = request.POST.get('id_requisicion')
        detalles = json.loads(request.POST.get('detalles'))  # Los detalles se pasan como un JSON

        # Verificar que los detalles no estén vacíos
        if not detalles:
            raise ValueError("No se han agregado detalles para la adquisición.")

        with transaction.atomic():  # Aseguramos que todos los cambios en la base de datos se realicen correctamente
            udcConn = connections['ctrlSum']  # Conexión a la base de datos
            with udcConn.cursor() as cursor:
                # Iteramos sobre los detalles que hemos recibido
                for detalle in detalles:
                    # Validamos que los datos esenciales estén presentes
                    if not detalle.get('id_detalle_requisicion') or not('id_suministros') or not detalle.get('cantidad') or not detalle.get('precio_unitario'):
                        raise ValueError("Faltan datos en los detalles de la adquisición.")
                    
                    # Validar que cantidad y precio_unitario sean mayores a cero
                    if detalle['cantidad'] <= 0 or detalle['precio_unitario'] <= 0:
                        raise ValueError("La cantidad y el precio unitario deben ser mayores a cero.")

                    # Llamamos al procedimiento almacenado con los parámetros correspondientes
                    cursor.callproc('SUM_INSERT_UPDATE_DETALLE_ADQUISICION', [
                        detalle.get('id_detalle_adquisicion', 0),
                        id_adquisicion,  # El ID de la adquisición
                        id_requisicion,
                        detalle['id_detalle_requisicion'],  # El ID del detalle de requisicion
                        detalle['id_suministros'],  # El ID del suministro
                        detalle['cantidad'],  # La cantidad del suministro
                        detalle['precio_unitario'],  # El precio unitario
                    ])

        # Si todo va bien, retornamos una respuesta de éxito
        datos = {'save': 1, 'message': 'Detalles de adquisición guardados correctamente.'}

    except Exception as e:
        # En caso de error, retornamos el mensaje de error
        datos = {'save': 0, 'error': f'⚠️ Error: {str(e)}'}

    return JsonResponse(datos)

# ----------------------------------------------------------------------------------------------------------------- #

def actualizar_estado_adquisicion(request):
    if request.method == "POST":
        adquisicion_id = request.POST.get('id_adquisicion')
        estadoAd = request.POST.get('estado')  # Obtener el estado nuevo

        # Validación de los parámetros
        if not adquisicion_id or not estadoAd:
            return JsonResponse({'success': False, 'error': 'Faltan parámetros requeridos.'})

        try:
            # Llamamos al procedimiento almacenado para actualizar el estado de la requisición
            udcConn = connections['ctrlSum']  # Usa la conexión correcta para la base de datos
            with udcConn.cursor() as cursor:
                cursor.callproc('ACTUALIZAR_ESTADO_ADQUISICION', [adquisicion_id, estadoAd])

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

# ----------------------------------------------------------------------------------------------------------------- #

def obtener_adquisicion_y_detalle_data(request):
    # Obtener el ID de la adquisición desde la solicitud
    id_adquisicion = request.GET.get('id_adquisicion')

    if not id_adquisicion:
        return JsonResponse({'error': 'No se proporcionó un ID de adquisición válido.'})

    try:
        # Conectar a la base de datos y ejecutar el procedimiento almacenado
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Llamar al procedimiento almacenado que obtiene la adquisición y los detalles
            cursor.callproc('GET_ADQUISICION_Y_DETALLES', [id_adquisicion])
            
            # Obtener los resultados de la adquisición
            column_names = [desc[0] for desc in cursor.description]
            adquisicion_data = dict(zip(column_names, cursor.fetchone()))  # solo un resultado para la adquisición

            # Obtener los resultados de los detalles de la adquisición
            cursor.nextset()  # Mover al siguiente conjunto de resultados (detalles)
            column_names = [desc[0] for desc in cursor.description]
            detalles_adquisicion = [
                dict(zip(column_names, row)) for row in cursor.fetchall()
            ]
        
        # Retornar la respuesta en formato JSON con los datos de la adquisición y los detalles
        return JsonResponse({
            'adquisicion': adquisicion_data,
            'detalles': detalles_adquisicion
        })

    except Exception as e:
        return JsonResponse({'error': f'Ocurrió un error: {str(e)}'})
    
# ----------------------------------------------------------------------------------------------------------------- #

# Obtiene los datos de la tabla Adquisicion
def obtener_detalle_adquisicion(request):
    if request.method == 'POST':
        # Obtener los parámetros del POST
        id_adquisicion = request.POST.get('id_adquisicion')
        id_requisicion = request.POST.get('id_requisicion')

        # Llamada al procedimiento almacenado
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc('kamilo_testing.OBTENER_DETALLE_ADQUISICION', [id_adquisicion, id_requisicion])
            result = cursor.fetchall()

        # Si no se encuentran resultados, devolver un error
        if not result:
            return JsonResponse({'success': False, 'message': 'No se encontraron detalles.'})

        # Si hay resultados, devolverlos como respuesta JSON
        detalles = []
        for row in result:
            detalle = {
                'id_detalle_adquisicion': row[0],
                'id_adquisicion': row[1],
                'id_requisicion': row[2],
                'id_detalle_requisicion': row[3],
                'solicitante': row[4],
                'id_suministros': row[5],
                'nombre_suministro': row[6],
                'cantidad': row[7],
                'precio_unitario': row[8],
                'precio_total': row[9],
                'id_proveedor': row[10],
                'nombre_proveedor': row[11],
                'estado': row[12],
                'creado_por': row[13],
                'fecha_hora_creacion': row[14],
                'modificado_por': row[15],
                'fecha_hora_modificado': row[16],
            }
            detalles.append(detalle)

        return JsonResponse({'success': True, 'data': detalles})
    else:
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

# --------------------------------------- SECCION DE ALMACENES  ------------------------------------------------ #

def listado_devoluciones_data(request):
    
    devoluciones_data = ""

    try:
        # TOMA LOS DATOS DE LA TABLA ALMACEN
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("GET_DEVOLUCIONES", [0])
            column_names = [desc[0] for desc in cursor.description]
            devoluciones_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        # Cierra la conexión
        udcConn.close()

    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})
    
    context = {
        "devoluciones": devoluciones_data,
    }
    
    return render(request, 'suministros/listado_devolucion.html', context)

#-----------------------------------------------------------------------------------------------------#

# Insertar y Actualizar Devolución
def insertar_actualizar_devolucion_data(request):
    try:
        existe = 0

        # Obtener los datos del formulario
        id_devolucion = request.POST.get('id_devolucion')
        if not id_devolucion:
            id_devolucion = None  # Esto permitirá al procedimiento almacenado insertar una nueva requisición 

        IDadquisicion = request.POST.get('id_adquisicion')
        IDDetalleRequisicion = request.POST.get('id_detalle_requisicion')
        IDsuministros = request.POST.get('id_suministros')
        cantidad_devuelta = request.POST.get('cantidad_devuelta')
        precioUnitario = request.POST.get('precio_unitario')
        fecha_devolucion = request.POST.get('fecha_devolucion')
        id_motivo_devolucion = request.POST.get('id_motivo_devolucion')
        motivo_devolucion = request.POST.get('motivo_devolucion')
        IDproveedor = request.POST.get('id_proveedor')
        total_devolucion = request.POST.get('total_devolucion')
        estado = request.POST.get('estado')  # Estado de la devolución (1 = Creado, 2 = Editado, 3 = Anulado)

        # Obtener el nombre del usuario desde la sesión
        userName = request.session.get('userName', '')

        # Conexión a la base de datos
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Llamar al procedimiento almacenado
            cursor.callproc('kamilo_testing.SUM_INSERT_UPDATE_DEVOLUCION', [
                id_devolucion,
                IDadquisicion,
                IDDetalleRequisicion,
                IDsuministros,
                cantidad_devuelta,
                precioUnitario,
                total_devolucion,
                fecha_devolucion,
                id_motivo_devolucion,
                motivo_devolucion,
                IDproveedor,
                estado,
                0,  # Parámetro OUT (guardado)
                userName
            ])

            # Obtener el valor del parámetro OUT (guardado)
            cursor.execute('SELECT @_kamilo_testing.SUM_INSERT_UPDATE_DEVOLUCION_12')
            guardado = cursor.fetchone()[0]

            # Definir el estado de la operación
            if guardado == 1:
                existe = 0  # Indica que se insertó un nuevo registro
            else:
                existe = 2  # Indica que se actualizó un registro existente
        
        # Cerrar la conexión
        udcConn.close()

        # Retornar la respuesta como JSON
        datos = {'save': 1, 'existe': existe}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)

#-----------------------------------------------------------------------------------------------------#

# Obtiene los datos de la tabla devolucion
def get_devoluciones_data (request):
    varEstado = int(request.POST.get('varEstado'))  # Convertir a entero, por defecto es 0
    devoluciones_data = ''

    try:
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("GET_DEVOLUCIONES", [varEstado])
            column_names = [desc[0] for desc in cursor.description]
            devoluciones_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()
        
        return JsonResponse({'data': devoluciones_data})
    except Exception as e:
        return JsonResponse({'error': str(e)})
  
#-----------------------------------------------------------------------------------------------------#  
def actualizar_estado_devolucion(request):
    if request.method == "POST":
        devolucion_id = request.POST.get('id_devolucion')
        estadoDev = request.POST.get('estado')  # Obtener el estado nuevo

        # Validación de los parámetros
        if not devolucion_id or not estadoDev:
            return JsonResponse({'success': False, 'error': 'Faltan parámetros requeridos.'})

        try:
            # Llamamos al procedimiento almacenado para actualizar el estado de la requisición
            udcConn = connections['ctrlSum']  # Usa la conexión correcta para la base de datos
            with udcConn.cursor() as cursor:
                cursor.callproc('ACTUALIZAR_ESTADO_DEVOLUCION', [devolucion_id, estadoDev])

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
#-----------------------------------------------------------------------------------------------------#

def obtener_motivos_devoluciones_data(request):
    try:
        # Conexión a la base de datos usando el alias 'ctrlSum' (puedes usar el alias que necesites)
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            # Llamamos al procedimiento almacenado 'OBTENER_METODOS_PAGO'
            cursor.callproc('OBTENER_MOTIVOS_DEVOLUCIONES')
            
            # Obtener los resultados del procedimiento almacenado
            column_names = [desc[0] for desc in cursor.description]  # Obtener nombres de columnas
            motivoD_data = [
                dict(zip(map(str, column_names), row)) for row in cursor.fetchall()
            ]
            
            # Si hay datos, devolverlos como un JsonResponse
            return JsonResponse({'motivoD': motivoD_data})
    
    except Exception as e:
        # Manejo de excepciones y errores en la ejecución
        print(f"Error en la ejecución del procedimiento o conexión: {str(e)}")
        return JsonResponse({'error': f'Ocurrió un error: {str(e)}'})

#-----------------------------------------------------------------------------------------------------#
def movimientos_suministros_data(request):

    categorias_data = ""

    try:
        # TOMA LOS DATOS DE LA TABLA CATEGORIAS PARA EL SELECT CATEGORIAS DEL HTML
        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc("SUM_GET_CATEGORIAS", [])
            column_names = [desc[0] for desc in cursor.description]
            categorias_data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

        # Cierra la conexión
        udcConn.close()

    except Exception as e:
        # Manejo de excepciones, puedes personalizar esto según tus necesidades
        return JsonResponse({'error': str(e)})
    
    context = {
        "categorias": categorias_data,
    }
    
    return render(request, 'suministros/kardex_suministros.html', context)

#-----------------------------------------------------------------------------------------------------# 

def historial_suministros_data(request):
    try:
        id_categoria = request.POST.get('id_categoria') or None
        id_suministro = request.POST.get('id_suministro') or None
        fecha_desde = request.POST.get('fecha_desde') or None
        fecha_hasta = request.POST.get('fecha_hasta') or None

        # Convertir valores vacíos a None explícitamente
        id_categoria = int(id_categoria) if id_categoria else None
        id_suministro = int(id_suministro) if id_suministro else None

        udcConn = connections['ctrlSum']
        with udcConn.cursor() as cursor:
            cursor.callproc('OBTENER_HISTORIAL_KARDEX', [
                id_categoria,
                id_suministro,
                fecha_desde,
                fecha_hasta
            ])
            result = cursor.fetchall()
            columnas = [col[0] for col in cursor.description]
            data = [dict(zip(columnas, row)) for row in result]

        return JsonResponse({'data': data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

#-----------------------------------------------------------------------------------------------------# 

def obtener_movimientos_x_suministro(request):
    if request.method == 'POST': 

        try:
            # Obtener el ID del suministro
            suministro_id = request.POST.get('suministro_id')

            # Validar que el ID del suministro esté presente
            if not suministro_id:
                return JsonResponse({'success': False, 'message': 'El ID del suministro es requerido.'}, status=400)

            suministro_id = int(suministro_id)

            # Conexión a la base de datos
            udcConn = connections['ctrlSum']
            with udcConn.cursor() as cursor:
                # Llamada al procedimiento almacenado
                cursor.callproc('kamilo_testing.OBTENER_MOVIMIENTO_X_SUMINISTRO', [suministro_id])
                result = cursor.fetchall()

            # Si no hay resultados, devolver mensaje de error
            if not result:
                return JsonResponse({'success': False, 'message': 'No se encontraron movimientos para este suministro.'})

            # Crear la lista de resultados
            movimientos = []
            for row in result:
                movimiento = {
                    'fecha_movimiento': row[0],
                    'tipo_movimiento': row[1],
                    'entrada': row[2],
                    'salida': row[3],
                    'precio_unitario': row[4],
                    'total': row[5],
                    'detalle_movimiento': row[6],
                    'creado_por': row[7],
                }
                movimientos.append(movimiento)

            # Devolver los detalles de los movimientos
            return JsonResponse({'success': True, 'data': movimientos})

        except Exception as e:
            # Manejo de excepciones
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    else:
        # Método no permitido
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)



