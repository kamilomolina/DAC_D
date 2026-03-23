import decimal
from datetime import date, datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connections

# Create your views here.

def panel_activo(request):
    """
    Main dashboard view for the ACTIVO FIJO application.
    """
    return render(request, 'activo_panel.html')

def gestion_activos(request):
    return render(request, 'control_gestion/gestion_activos.html')


def fill_categorias_activos(request):
    try:
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_FILL_CATEGORIAS', [])
            column_names = [desc[0] for desc in cursor.description]
            data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        return JsonResponse({'data': data})
    except Exception as e:
        return JsonResponse({'data': [], 'error': str(e)})

def fill_proveedores_activos(request):
    try:
        fkEmpresa = request.GET.get('fkEmpresa')
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_FILL_PROVEEDORES', [fkEmpresa])
            column_names = [desc[0] for desc in cursor.description]
            data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        return JsonResponse({'data': data})
    except Exception as e:
        return JsonResponse({'data': [], 'error': str(e)})

def fill_ubicaciones_activos(request):
    try:
        fkEmpresa = request.GET.get('fkEmpresa')
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_FILL_UBICACIONES', [fkEmpresa])
            column_names = [desc[0] for desc in cursor.description]
            data = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        return JsonResponse({'data': data})
    except Exception as e:
        return JsonResponse({'data': [], 'error': str(e)})

def get_activos(request):
    try:
        fkEmpresa = request.GET.get('fkEmpresa')
        estado = request.GET.get('estado')
        textoBusqueda = request.GET.get('textoBusqueda')
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_GET_ACTIVOS', [fkEmpresa, estado, textoBusqueda])
            column_names = [desc[0] for desc in cursor.description]
            data = []
            for row in cursor.fetchall():
                row_dict = {}
                for col, val in zip(column_names, row):
                    if isinstance(val, (date, datetime)):
                        row_dict[str(col)] = val.strftime('%Y-%m-%d')
                    elif isinstance(val, decimal.Decimal):
                        row_dict[str(col)] = float(val)
                    else:
                        row_dict[str(col)] = val if val is not None else ""
                data.append(row_dict)
        return JsonResponse({'data': data})
    except Exception as e:
        return JsonResponse({'data': [], 'error': str(e)})

def get_activo_x_id(request):
    try:
        pkActivo = request.GET.get('pkActivo')
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_GET_ACTIVO_X_ID', [pkActivo])
            column_names = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            if not row:
                return JsonResponse({'success': False, 'mensaje': 'No se encontró el activo.'})
            
            data = {}
            for col, val in zip(column_names, row):
                if isinstance(val, (date, datetime)):
                    data[str(col)] = val.strftime('%Y-%m-%d')
                elif isinstance(val, decimal.Decimal):
                    data[str(col)] = float(val)
                else:
                    data[str(col)] = val if val is not None else ""
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)})


def insert_activo(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
        
        userName = request.session.get('userName')
        p = request.POST
        
        params = [
            p.get('codigoActivo'), p.get('nombreActivo'), p.get('descripcion'), p.get('fkCategoria'),
            p.get('fkProveedor'), p.get('fkUbicacionActual'), p.get('marca'), p.get('modelo'),
            p.get('serie'), p.get('fechaCompra'), p.get('numeroFactura'), p.get('valorCompra'),
            p.get('observaciones'), p.get('fkEmpresa'), userName
        ]
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_INSERT_ACTIVO', params)
            row = cursor.fetchone()
            
        return JsonResponse({
            'save': row[0],
            'existe': row[1],
            'lastID': row[2],
            'mensaje': row[3]
        })
    except Exception as e:
        return JsonResponse({'save': 0, 'mensaje': str(e)})

def update_activo(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
            
        userName = request.session.get('userName')
        p = request.POST
        
        params = [
            p.get('pkActivo'), p.get('codigoActivo'), p.get('nombreActivo'), p.get('descripcion'),
            p.get('fkCategoria'), p.get('fkProveedor'), p.get('fkUbicacionActual'), p.get('marca'),
            p.get('modelo'), p.get('serie'), p.get('fechaCompra'), p.get('numeroFactura'),
            p.get('valorCompra'), 0, 'BUENO',
            'ACTIVO', None, p.get('observaciones'),
            p.get('fkEmpresa'), userName
        ]
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_UPD_ACTIVO', params)
            row = cursor.fetchone()
            
        return JsonResponse({
            'save': row[0],
            'existe': row[1],
            'mensaje': row[2]
        })
    except Exception as e:
        return JsonResponse({'save': 0, 'mensaje': str(e)})

def delete_activo(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
            
        userName = request.session.get('userName')
        pkActivo = request.POST.get('pkActivo')
        estado = request.POST.get('estado', 3)
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_DEL_ACTIVO', [pkActivo, estado, userName])
            row = cursor.fetchone()
            
        return JsonResponse({
            'save': row[0],
            'mensaje': row[1]
        })
    except Exception as e:
        return JsonResponse({'save': 0, 'mensaje': str(e)})

def gestion_categorias_activos(request):
    return render(request, 'control_gestion/gestion_categorias_activos.html')


def get_categorias_activos(request):
    try:
        fkEmpresa = request.GET.get('fkEmpresa')
        estado = request.GET.get('estado')
        textoBusqueda = request.GET.get('textoBusqueda')
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_GET_CATEGORIAS', [estado, textoBusqueda])
            column_names = [desc[0] for desc in cursor.description]
            data = []
            for row in cursor.fetchall():
                row_dict = {}
                for col, val in zip(column_names, row):
                    if isinstance(val, (date, datetime)):
                        row_dict[str(col)] = val.strftime('%Y-%m-%d %H:%M:%S')
                    elif isinstance(val, decimal.Decimal):
                        row_dict[str(col)] = float(val)
                    else:
                        row_dict[str(col)] = val if val is not None else ""
                data.append(row_dict)
        return JsonResponse({'data': data})
    except Exception as e:
        return JsonResponse({'data': [], 'error': str(e)})

def get_categoria_activo_x_id(request):
    try:
        pkCategoria = request.GET.get('pkCategoria')
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_GET_CATEGORIA_X_ID', [pkCategoria])
            column_names = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            if not row:
                return JsonResponse({'success': False, 'mensaje': 'No se encontró la categoría.'})
            
            data = {}
            for col, val in zip(column_names, row):
                if isinstance(val, (date, datetime)):
                    data[str(col)] = val.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(val, decimal.Decimal):
                    data[str(col)] = float(val)
                else:
                    data[str(col)] = val if val is not None else ""
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)})

def insert_categoria_activo(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
            
        userName = request.session.get('userName')
        p = request.POST
        
        params = [
            p.get('nombreCategoria'), p.get('descripcion'), userName
        ]
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_INSERT_CATEGORIA', params)
            row = cursor.fetchone()
            
        return JsonResponse({
            'save': row[0],
            'existe': row[1],
            'lastID': row[2],
            'mensaje': row[3]
        })
    except Exception as e:
        return JsonResponse({'save': 0, 'mensaje': str(e)})

def update_categoria_activo(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
            
        userName = request.session.get('userName')
        p = request.POST
        
        params = [
            p.get('pkCategoria'), p.get('nombreCategoria'), p.get('descripcion'), userName
        ]
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_UPDATE_CATEGORIA', params)
            row = cursor.fetchone()
            
        return JsonResponse({
            'save': row[0],
            'existe': row[1],
            'mensaje': row[2]
        })
    except Exception as e:
        return JsonResponse({'save': 0, 'mensaje': str(e)})

def delete_categoria_activo(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
            
        userName = request.session.get('userName')
        pkCategoria = request.POST.get('pkCategoria')
        estado = request.POST.get('estado', 3)
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_DEL_CATEGORIA', [pkCategoria, estado, userName])
            row = cursor.fetchone()
            
        return JsonResponse({
            'save': row[0],
            'mensaje': row[1]
        })
    except Exception as e:
        return JsonResponse({'save': 0, 'mensaje': str(e)})

# ==========================================
# RUTAS BASE NUEVAS - REESTRUCTURACIÓN
# ==========================================

# Catálogos
def gestion_proveedores(request):
    return render(request, 'catalogos/gestion_proveedores.html')

def gestion_ubicaciones(request):
    return render(request, 'catalogos/gestion_ubicaciones.html')

def gestion_motivos_salida(request):
    return render(request, 'catalogos/gestion_motivos_salida.html')

# Activos
def sacar_equipo(request):
    return render(request, 'activos/sacar_equipo.html')

# Depreciación
def depreciaciones_aplicadas(request):
    return render(request, 'depreciacion/depreciaciones_aplicadas.html')

def historial_depreciacion(request):
    return render(request, 'depreciacion/historial_depreciacion.html')

def depreciacion_anual(request):
    return render(request, 'depreciacion/depreciacion_anual.html')

# Consultas
def consulta_estado_actual(request):
    return render(request, 'consultas/estado_actual.html')

def consulta_estado_mes(request):
    return render(request, 'consultas/estado_mes.html')

# Reportes
def reporte_general(request):
    return render(request, 'reportes/reporte_general.html')

def reporte_bajas(request):
    return render(request, 'reportes/reporte_bajas.html')

def reporte_depreciacion(request):
    return render(request, 'reportes/reporte_depreciacion.html')

