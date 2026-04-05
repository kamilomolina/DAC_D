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
    return render(request, 'control_gestion/gestion_activos.html', {'empresas': get_empresas_activas()})


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
        with connections['activo'].cursor() as cursor:
            # Usando AF_GET_PROVEEDORES que sí existe en lugar de AF_FILL_PROVEEDORES
            cursor.callproc('AF_GET_PROVEEDORES', [])
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
    return render(request, 'control_gestion/gestion_categorias_activos.html', {'empresas': get_empresas_activas()})


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
    return render(request, 'catalogos/gestion_proveedores.html', {'empresas': get_empresas_activas()})

def get_proveedores(request):
    try:
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_GET_PROVEEDORES', [])
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

def get_proveedor_x_id(request):
    try:
        pkProveedor = request.GET.get('pkProveedor')
        if not pkProveedor:
             return JsonResponse({'success': False, 'mensaje': 'ID requerido'})
             
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_GET_PROVEEDORES', [])
            column_names = [desc[0] for desc in cursor.description]
            
            # Filtramos en python ya que el SP trae todos:
            found_data = None
            for row in cursor.fetchall():
                if str(row[0]) == str(pkProveedor):
                    found_data = {}
                    for col, val in zip(column_names, row):
                        if isinstance(val, (date, datetime)):
                            found_data[str(col)] = val.strftime('%Y-%m-%d %H:%M:%S')
                        elif isinstance(val, decimal.Decimal):
                            found_data[str(col)] = float(val)
                        else:
                            found_data[str(col)] = val if val is not None else ""
                    break
                    
            if not found_data:
                return JsonResponse({'success': False, 'mensaje': 'No se encontró el proveedor.'})
                
        return JsonResponse({'success': True, 'data': found_data})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)})

def insert_proveedor(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
            
        userName = request.session.get('userName', 'admin') # Falta userName en request? Agregamos 'admin' por si no hay session de pruebas.
        if not request.session.get('userName'):
            # Si el proyecto usa userInfo o similar, lo extraemos, usamos get() normal para evitar error de session no iniciada
            userName = request.session.get('userName', 'admin') 
            
        p = request.POST
        pkProveedor = p.get('pkProveedor')
        if not pkProveedor or str(pkProveedor) == "":
            pkProveedor = 0
            
        params = [
            pkProveedor, 
            p.get('nombreProveedor'), 
            p.get('rtn'), 
            p.get('telefono'), 
            p.get('email'), 
            p.get('direccion'), 
            userName
        ]
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_INSERT_PROVEEDOR', params)
            row = cursor.fetchone()
            
        return JsonResponse({
            'save': row[0],
            'existe': row[1],
            'lastID': row[2],
            'mensaje': row[3] if len(row) > 3 else 'Operación realizada correctamente'
        })
    except Exception as e:
        return JsonResponse({'save': 0, 'mensaje': str(e)})

def update_estado_proveedor(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
            
        userName = request.session.get('userName')
        p = request.POST
        
        pkProveedor = p.get('pkProveedor')
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_UPDATE_ESTADO_PROVEEDOR', [pkProveedor, userName])
            row = cursor.fetchone()
            
        return JsonResponse({'save': row[0], 'mensaje': row[1]})
    except Exception as e:
        return JsonResponse({'save': 0, 'mensaje': str(e)})

def delete_proveedor(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
            
        pkProveedor = request.POST.get('pkProveedor')
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_DELETE_PROVEEDOR', [pkProveedor])
            row = cursor.fetchone()
            
        return JsonResponse({
            'save': row[0] if row else 1,
            'mensaje': 'Proveedor eliminado correctamente'
        })
    except Exception as e:
        return JsonResponse({'save': 0, 'mensaje': str(e)})

def gestion_ubicaciones(request):
    return render(request, 'catalogos/gestion_ubicaciones.html', {'empresas': get_empresas_activas()})

def get_ubicaciones(request):
    try:
        fkEmpresa = request.GET.get('fkEmpresa', 0)
        if not fkEmpresa or str(fkEmpresa) == "":
            fkEmpresa = 0
            
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_FILL_UBICACIONES', [fkEmpresa])
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

def get_ubicacion_x_id(request):
    try:
        pkUbicacion = request.GET.get('pkUbicacion')
        if not pkUbicacion:
             return JsonResponse({'success': False, 'mensaje': 'ID requerido'})
             
        fkEmpresa = request.GET.get('fkEmpresa', 0)
        if not fkEmpresa or str(fkEmpresa) == "":
            fkEmpresa = 0
            
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_FILL_UBICACIONES', [fkEmpresa])
            column_names = [desc[0] for desc in cursor.description]
            
            found_data = None
            for row in cursor.fetchall():
                if str(row[0]) == str(pkUbicacion):
                    found_data = {}
                    for col, val in zip(column_names, row):
                        if isinstance(val, (date, datetime)):
                            found_data[str(col)] = val.strftime('%Y-%m-%d %H:%M:%S')
                        elif isinstance(val, decimal.Decimal):
                            found_data[str(col)] = float(val)
                        else:
                            found_data[str(col)] = val if val is not None else ""
                    break
                    
            if not found_data:
                return JsonResponse({'success': False, 'mensaje': 'No se encontró la ubicación.'})
                
        return JsonResponse({'success': True, 'data': found_data})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)})

def insert_ubicacion(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
            
        userName = request.session.get('userName', 'admin')
        if not request.session.get('userName'):
            userName = request.session.get('userName', 'admin') 
            
        p = request.POST
        pkUbicacion = p.get('pkUbicacion')
        if not pkUbicacion or str(pkUbicacion) == "":
            pkUbicacion = 0
            
        fkEmpresa = p.get('fkEmpresa')
        if not fkEmpresa or str(fkEmpresa) == "":
            fkEmpresa = 0
            
        params = [
            pkUbicacion, 
            p.get('codigoUbicacion'), 
            p.get('nombreUbicacion'), 
            p.get('tipoUbicacion'), 
            p.get('descripcion'), 
            fkEmpresa,
            userName
        ]
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_INSERT_UBICACION', params)
            row = cursor.fetchone()
            
        return JsonResponse({
            'save': row[0],
            'lastID': row[1] if len(row) > 1 else pkUbicacion,
            'mensaje': row[2] if len(row) > 2 else 'Operación realizada correctamente'
        })
    except Exception as e:
        return JsonResponse({'save': 0, 'mensaje': str(e)})

def delete_ubicacion(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
            
        userName = request.session.get('userName', 'admin')
        pkUbicacion = request.POST.get('pkUbicacion')
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_DELETE_UBICACION', [pkUbicacion, userName])
            row = cursor.fetchone()
            
        return JsonResponse({
            'deleted': row[0] if row else 1,
            'save': row[0] if row else 1,
            'mensaje': 'Ubicación eliminada correctamente'
        })
    except Exception as e:
        return JsonResponse({'deleted': 0, 'save': 0, 'mensaje': str(e)})

def gestion_motivos_salida(request):
    return render(request, 'catalogos/gestion_motivos_salida.html')

def get_motivos_salida(request):
    try:
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_FILL_MOTIVOS_SALIDA', [])
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

def get_motivo_salida_x_id(request):
    try:
        pkMotivoSalida = request.GET.get('pkMotivoSalida')
        if not pkMotivoSalida:
             return JsonResponse({'success': False, 'mensaje': 'ID requerido'})
             
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_FILL_MOTIVOS_SALIDA', [])
            column_names = [desc[0] for desc in cursor.description]
            
            found_data = None
            for row in cursor.fetchall():
                if str(row[0]) == str(pkMotivoSalida):
                    found_data = {}
                    for col, val in zip(column_names, row):
                        if isinstance(val, (date, datetime)):
                            found_data[str(col)] = val.strftime('%Y-%m-%d %H:%M:%S')
                        elif isinstance(val, decimal.Decimal):
                            found_data[str(col)] = float(val)
                        else:
                            found_data[str(col)] = val if val is not None else ""
                    break
                    
            if not found_data:
                return JsonResponse({'success': False, 'mensaje': 'No se encontró el motivo de salida.'})
                
        return JsonResponse({'success': True, 'data': found_data})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)})

def insert_motivo_salida(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
            
        userName = request.session.get('userName', 'admin')
        if not request.session.get('userName'):
            userName = request.session.get('userName', 'admin') 
            
        p = request.POST
        pkMotivoSalida = p.get('pkMotivoSalida')
        if not pkMotivoSalida or str(pkMotivoSalida) == "":
            pkMotivoSalida = 0
            
        params = [
            pkMotivoSalida, 
            p.get('descripcionMotivo'),
            userName
        ]
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_INSERT_MOTIVO_SALIDA', params)
            row = cursor.fetchone()
            
        return JsonResponse({
            'save': row[0],
            'lastID': row[1] if len(row) > 1 else pkMotivoSalida,
            'mensaje': row[2] if len(row) > 2 else 'Operación realizada correctamente'
        })
    except Exception as e:
        return JsonResponse({'save': 0, 'mensaje': str(e)})

def delete_motivo_salida(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'save': 0, 'mensaje': 'Método no permitido.'})
            
        userName = request.session.get('userName', 'admin')
        pkMotivoSalida = request.POST.get('pkMotivoSalida')
        
        with connections['activo'].cursor() as cursor:
            cursor.callproc('AF_DELETE_MOTIVO_SALIDA', [pkMotivoSalida, userName])
            row = cursor.fetchone()
            
        return JsonResponse({
            'deleted': row[0] if row else 1,
            'save': row[0] if row else 1,
            'mensaje': 'Motivo eliminado correctamente'
        })
    except Exception as e:
        return JsonResponse({'deleted': 0, 'save': 0, 'mensaje': str(e)})



def get_empresas_activas():
    empresas = []
    try:
        with connections['activo'].cursor() as cursor:
            cursor.execute("SELECT PkEmpresa, NombreEmpresa, Empresa, Estado FROM global_security.empresas WHERE Estado = 1")
            column_names = [desc[0] for desc in cursor.description]
            empresas = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
    except Exception as e:
        empresas.append({'PkEmpresa': '', 'NombreEmpresa': f"ERROR BD: {str(e)}", 'Empresa': 'Err'})
    return empresas

def get_categorias_todas():
    cats = []
    try:
        with connections['activo'].cursor() as cursor:
            cursor.execute("SELECT PkCategoria, NombreCategoria FROM af_categorias WHERE estado = 1")
            column_names = [desc[0] for desc in cursor.description]
            cats = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
    except Exception as e: 
        cats.append({'PkCategoria': '', 'NombreCategoria': f"ERROR BD: {str(e)}"})
    return cats

def get_ubicaciones_todas():
    ubis = []
    try:
        with connections['activo'].cursor() as cursor:
            cursor.execute("SELECT PkUbicacion, NombreUbicacion FROM af_ubicaciones WHERE estado = 1")
            column_names = [desc[0] for desc in cursor.description]
            ubis = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
    except Exception as e: 
        ubis.append({'PkUbicacion': '', 'NombreUbicacion': f"ERROR BD: {str(e)}"})
    return ubis

# Depreciación
def depreciaciones_aplicadas(request):
    context = {
        'empresas': get_empresas_activas(),
        'categorias': get_categorias_todas(),
        'ubicaciones': get_ubicaciones_todas()
    }
    return render(request, 'depreciacion/depreciaciones_aplicadas.html', context)



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
    context = {
        'empresas': get_empresas_activas(),
        'categorias': get_categorias_todas(),
        'ubicaciones': get_ubicaciones_todas()
    }
    return render(request, 'reportes/reporte_depreciacion.html', context)

