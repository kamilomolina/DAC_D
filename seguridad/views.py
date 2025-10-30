from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.db import connections
from .models import Permiso
from .models import Usuario

def obtener_permisos_desde_sp(usuario_id):
    conexion_global_nube = connections['global_nube']
    with conexion_global_nube.cursor() as cursor:
        cursor.execute("CALL WEB_GET_MENUS_GRUPO_USUARIO(%s, %s)", [usuario_id, 13])
        columnas = [col[0] for col in cursor.description]
        resultados = [dict(zip(columnas, row)) for row in cursor.fetchall()]
    return resultados


def obtener_adminIT(usuario_id):
    conexion_global_nube = connections['global_nube']
    resultados = []  # Inicializar resultados como una lista vacía

    with conexion_global_nube.cursor() as cursor:
        cursor.execute("CALL CRM_GET_ADMIN_IT(%s)", [usuario_id])
        adminIT = cursor.fetchone()  # Utiliza fetchone para obtener una fila

        if adminIT:  # Comprueba si se encontró el adminIT
            resultados.append({'adminIT': True})
        else:
            resultados.append({'adminIT': False})

    return resultados

def obtener_diccionario_permisos(usuario_id):
    from .models import Permiso
    permisos = Permiso.objects.filter(permiso_usuario__usuario_vendedor=usuario_id)
    diccionario_permisos = {}
    adminIT = obtener_adminIT(usuario_id) 
    for permiso in permisos:
        diccionario_permisos[permiso.posicionMenu] = permiso.tiene_acceso
    return render({'diccionario_permisos': diccionario_permisos, 'adminIt': adminIT})

def obtener_usuario_vendedor(usuario):
    with connections['global_security'].cursor() as cursor:
        cursor.callproc('DAC_USUARIO_VENDEDOR_GET', [usuario])
        userVendedor = cursor.fetchall()

    if userVendedor:
        # Asumiendo que el Stored Procedure devuelve al menos un resultado
        userName = userVendedor[0][0]  # Ajusta el índice según la estructura de tus datos
        return userName
    return None



#------------------------------------------------------------USUARIOS--------------------------------------------------------------

def obtener_usuarios(request):
    from .models import Usuario
    usuarios = Usuario.objects.all().values()
    lista_usuarios = []

    for usuario in usuarios:
        usuario_dict = dict(usuario)

        # Convierte los valores de bit a booleanos explícitamente si es necesario
        for campo in ['is_built_in', 'ventas', 'comisiones']:
            if campo in usuario_dict:
                # En Django, los BooleanFields ya son True o False,
                # la siguiente línea es innecesaria, pero se incluye por petición.
                usuario_dict[campo] = bool(usuario_dict[campo])

        # Elimina claves con valores None (opcional, si deseas quitarlas)
        usuario_dict = {k: v for k, v in usuario_dict.items() if v is not None}

        lista_usuarios.append(usuario_dict)

    return JsonResponse({"data": lista_usuarios})