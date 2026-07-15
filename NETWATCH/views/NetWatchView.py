from django.shortcuts import render
from django.db import connections
from django.http import JsonResponse
from django.urls import reverse
from django.http import HttpResponseRedirect
import subprocess
import platform
import concurrent.futures

# ============================================================================
# CONEXIÓN PRINCIPAL — Base de datos NETWATCH (kamilo_testing)
# ============================================================================
DB_NAME = 'netwatch_db'


def get_user_context(request):
    """Extrae datos del usuario de session para pasar al template."""
    return {
        'userName': request.session.get('userName', 'USUARIO'),
    }


def auth_required(request):
    """Retorna redirect si el usuario no tiene sesión activa, None si sí."""
    if not request.session.get('user_id'):
        return HttpResponseRedirect(reverse('login'))
    return None


# ============================================================================
# HELPERS DE BASE DE DATOS — Invocan los SPs definidos en kamilo_testing
# ============================================================================

def nw_get_devices(estado=1, busqueda=''):
    """
    Invoca NW_GET_DEVICES y retorna lista de dispositivos.
    Parámetros:
        estado    (int)  : 1 = Activos, 0 = Inactivos
        busqueda  (str)  : Texto de búsqueda por nombre, IP, marca o área
    """
    devices = []
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_GET_DEVICES', [estado, busqueda])
            cols = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                d = dict(zip(cols, row))
                # Normalizar campos para compatibilidad con templates y Vis.js
                devices.append({
                    'id':            d['id_device'],
                    'name':          d['nombre'],
                    'ip':            d['ip_address'],
                    'area':          d.get('area', ''),
                    'sucursal':      d.get('sucursal', ''),
                    'type':          d.get('tipo_dispositivo', 'OTRO'),
                    'marca':         d.get('marca', ''),
                    'modelo':        d.get('modelo', ''),
                    'community':     d.get('snmp_community', 'public'),
                    'snmp_version':  d.get('snmp_version', 'v2c'),
                    'snmp_port':     d.get('snmp_port', 161),
                    'estado_actual': d.get('estado_actual', 'unknown') or 'unknown',
                    'descripcion':   d.get('descripcion', ''),
                })
    except Exception as e:
        print(f"[NETWATCH] Error en NW_GET_DEVICES: {e}")
    return devices


def nw_get_device_by_id(id_device):
    """Invoca NW_GET_DEVICE_BY_ID y retorna un dict con la info del equipo."""
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_GET_DEVICE_BY_ID', [id_device])
            cols = [desc[0] for desc in cursor.description]
            row  = cursor.fetchone()
            if row:
                return dict(zip(cols, row))
    except Exception as e:
        print(f"[NETWATCH] Error en NW_GET_DEVICE_BY_ID: {e}")
    return None


def nw_insert_device(nombre, ip, tipo, marca, modelo, sucursal, area,
                     snmp_version, community, snmp_port, estado_monitoreo=1):
    """
    Invoca NW_INSERT_DEVICE.
    Retorna: { lastID, guardado, mensaje }
    """
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_INSERT_DEVICE', [
                nombre, ip, tipo, marca, modelo, sucursal, area,
                snmp_version, community, snmp_port, estado_monitoreo
            ])
            row = cursor.fetchone()
            return {
                'lastID':   row[0],
                'guardado': row[1],
                'mensaje':  row[2],
            }
    except Exception as e:
        return {'lastID': 0, 'guardado': 0, 'mensaje': str(e)}


def nw_update_device(id_device, nombre, ip, tipo, marca, modelo, sucursal, area,
                     snmp_version, community, snmp_port, estado_monitoreo=1):
    """
    Invoca NW_UPDATE_DEVICE.
    Retorna: { lastID, guardado, mensaje }
    """
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_UPDATE_DEVICE', [
                id_device, nombre, ip, tipo, marca, modelo, sucursal, area,
                snmp_version, community, snmp_port, estado_monitoreo
            ])
            row = cursor.fetchone()
            return {
                'lastID':   row[0],
                'guardado': row[1],
                'mensaje':  row[2],
            }
    except Exception as e:
        return {'lastID': 0, 'guardado': 0, 'mensaje': str(e)}


def nw_delete_device(id_device):
    """
    Invoca NW_DELETE_DEVICE (baja lógica).
    Retorna: { lastID, guardado, mensaje }
    """
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_DELETE_DEVICE', [id_device])
            row = cursor.fetchone()
            return {
                'lastID':   row[0],
                'guardado': row[1],
                'mensaje':  row[2],
            }
    except Exception as e:
        return {'lastID': 0, 'guardado': 0, 'mensaje': str(e)}


def nw_update_device_status(id_device, estado):
    """
    Invoca NW_UPDATE_DEVICE_STATUS para persistir el estado del último barrido.
    estados válidos: 'online', 'warning', 'offline'
    """
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_UPDATE_DEVICE_STATUS', [id_device, estado])
    except Exception as e:
        print(f"[NETWATCH] Error en NW_UPDATE_DEVICE_STATUS id={id_device}: {e}")


def nw_get_links():
    """
    Invoca NW_GET_LINKS y retorna lista de conexiones de red.
    """
    links = []
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_GET_LINKS', [])
            cols = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                d = dict(zip(cols, row))
                links.append({
                    'id':             d['id_link'],
                    'from':           d['id_device_origen'],
                    'to':             d['id_device_destino'],
                    'nombre_origen':  d.get('nombre_origen', ''),
                    'nombre_destino': d.get('nombre_destino', ''),
                    'puerto_origen':  d.get('puerto_origen', '') or '',
                    'puerto_destino': d.get('puerto_destino', '') or '',
                    'tipo':           d.get('tipo_enlace', 'Cobre') or 'Cobre',
                    'activo':         bool(d.get('estado_enlace', 1)),
                })
    except Exception as e:
        print(f"[NETWATCH] Error en NW_GET_LINKS: {e}")
    return links


def nw_insert_link(id_origen, puerto_origen, id_destino, puerto_destino, tipo_enlace):
    """
    Invoca NW_INSERT_LINK.
    Retorna: { lastID, guardado, mensaje }
    """
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_INSERT_LINK', [
                id_origen, puerto_origen, id_destino, puerto_destino, tipo_enlace
            ])
            row = cursor.fetchone()
            return {'lastID': row[0], 'guardado': row[1], 'mensaje': row[2]}
    except Exception as e:
        return {'lastID': 0, 'guardado': 0, 'mensaje': str(e)}


def nw_delete_link(id_link):
    """
    Invoca NW_DELETE_LINK.
    Retorna: { lastID, guardado, mensaje }
    """
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_DELETE_LINK', [id_link])
            row = cursor.fetchone()
            return {'lastID': row[0], 'guardado': row[1], 'mensaje': row[2]}
    except Exception as e:
        return {'lastID': 0, 'guardado': 0, 'mensaje': str(e)}


def nw_log_event(id_device, tipo_evento, detalles=''):
    """
    Invoca NW_LOG_EVENT para guardar una alerta/cambio de estado en la bitácora.
    Tipos sugeridos: 'DEVICE_DOWN', 'DEVICE_UP', 'UPS_ACTIVE', 'PORT_DOWN'
    """
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_LOG_EVENT', [id_device, tipo_evento, detalles])
    except Exception as e:
        print(f"[NETWATCH] Error en NW_LOG_EVENT: {e}")


def nw_get_events(limit=50):
    """
    Invoca NW_GET_EVENTS y retorna los últimos eventos de la bitácora.
    """
    events = []
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_GET_EVENTS', [limit])
            cols = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                events.append(dict(zip(cols, row)))
    except Exception as e:
        print(f"[NETWATCH] Error en NW_GET_EVENTS: {e}")
    return events


# ============================================================================
# MOTOR DE PING + PERSISTENCIA DE ESTADO
# ============================================================================

def ping_device(device):
    """
    Hace ping a un dispositivo y retorna su estado ('online' u 'offline').
    También persiste el nuevo estado en BD via NW_UPDATE_DEVICE_STATUS
    y registra en bitácora si hubo cambio de estado.
    """
    ip              = device['ip']
    id_device       = device['id']
    estado_anterior = device.get('estado_actual', 'unknown')

    param   = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-w', '1000', ip]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2
        )
        nuevo_estado = 'online' if result.returncode == 0 else 'offline'
    except Exception:
        nuevo_estado = 'offline'

    # Persistir el nuevo estado en BD
    nw_update_device_status(id_device, nuevo_estado)

    # Registrar en bitácora solo si el estado cambió
    if nuevo_estado != estado_anterior:
        tipo_evento = 'DEVICE_UP' if nuevo_estado == 'online' else 'DEVICE_DOWN'
        nw_log_event(
            id_device,
            tipo_evento,
            f"Estado cambió de '{estado_anterior}' a '{nuevo_estado}' — IP: {ip}"
        )

    return {'id': id_device, 'ip': ip, 'status': nuevo_estado}


# ============================================================================
# COLORES, ÍCONOS Y TAMAÑOS DE NODOS PARA VIS.JS
# ============================================================================
DEVICE_COLORS = {
    'online':  {'background': '#10b981', 'border': '#059669', 'glow': 'rgba(16,185,129,0.5)'},
    'offline': {'background': '#ef4444', 'border': '#dc2626', 'glow': 'rgba(239,68,68,0.5)'},
    'unknown': {'background': '#64748b', 'border': '#475569', 'glow': 'rgba(100,116,139,0.4)'},
}

DEVICE_ICONS = {
    'ROUTER':    '\uf4d0',   # fa-route
    'SWITCH':    '\uf6ff',   # fa-network-wired
    'SERVIDOR':  '\uf233',   # fa-server
    'OTRO':      '\uf10b',   # fa-laptop / dispositivo genérico
}

DEVICE_SIZE = {
    'ROUTER':   32,
    'SWITCH':   30,
    'SERVIDOR': 28,
    'OTRO':     26,
}


# ============================================================================
# VISTAS DEL MÓDULO
# ============================================================================

def panel_netwatch(request):
    """Dashboard principal — Centro de Monitoreo."""
    redirect = auth_required(request)
    if redirect:
        return redirect

    devices = nw_get_devices(estado=1)
    return render(request, 'netwatch/dashboard.html', {
        **get_user_context(request),
        'devices': devices,
    })


def admin_netwatch(request):
    """Vista de Administración / Gestión de Dispositivos."""
    redirect = auth_required(request)
    if redirect:
        return redirect

    devices = nw_get_devices(estado=1)
    return render(request, 'netwatch/control_gestion/gestion_equipos.html', {
        **get_user_context(request),
        'devices': devices,
    })


def mapa_red(request):
    """Vista principal del Mapa de Red Interactivo."""
    redirect = auth_required(request)
    if redirect:
        return redirect

    return render(request, 'netwatch/mapa_red.html', {
        **get_user_context(request),
    })


# ============================================================================
# ENDPOINTS JSON / API
# ============================================================================

def get_network_status(request):
    """
    API: Escanea todos los dispositivos activos por ping,
    persiste los nuevos estados y retorna los resultados.
    """
    devices = nw_get_devices(estado=1)

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(ping_device, d): d for d in devices}
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception:
                device = futures[future]
                results.append({'id': device['id'], 'ip': device['ip'], 'status': 'offline'})

    return JsonResponse({'statuses': results})


def get_topology_data(request):
    """
    API: Devuelve nodos y enlaces para el mapa de red (Vis.js).
    Formato: { nodes: [...], edges: [...] }
    """
    try:
        devices = nw_get_devices(estado=1)
        links   = nw_get_links()

        # Construir nodos Vis.js
        nodes = []
        for d in devices:
            status = d.get('estado_actual', 'unknown') or 'unknown'
            # Mapear warning a online ya que quitamos UPS
            if status == 'warning':
                status = 'online'
            col    = DEVICE_COLORS.get(status, DEVICE_COLORS['unknown'])
            tipo   = (d.get('type') or 'OTRO').upper()
            if tipo not in DEVICE_ICONS:
                tipo = 'OTRO'

            icon_code = DEVICE_ICONS[tipo]
            size      = DEVICE_SIZE.get(tipo, 26)

            nodes.append({
                'id':          d['id'],
                'label':       d['name'],
                'ip':          d['ip'],
                'area':        d['area'],
                'sucursal':    d['sucursal'],
                'tipo':        tipo,
                'marca':       d.get('marca', ''),
                'modelo':      d.get('modelo', ''),
                'community':   d.get('community', 'public'),
                'descripcion': d.get('descripcion', ''),
                'status':      status,
                'shape':       'icon',
                'icon': {
                    'face':    '"Font Awesome 6 Free"',
                    'weight':  '900',
                    'code':    icon_code,
                    'size':    size,
                    'color':   col['background'],
                },
                'shadow': {
                    'enabled': True,
                    'color':   col['glow'],
                    'size':    10,
                    'x': 0, 'y': 2,
                }
            })

        # Construir aristas Vis.js
        edges = []
        for lnk in links:
            edge_color = '#10b981' if lnk['activo'] else '#ef4444'
            label      = f"{lnk['tipo']}"
            if lnk['puerto_origen'] or lnk['puerto_destino']:
                label = f"{lnk['puerto_origen']} → {lnk['puerto_destino']}"

            edges.append({
                'id':     lnk['id'],
                'from':   lnk['from'],
                'to':     lnk['to'],
                'title':  f"{lnk['nombre_origen']} [{lnk['puerto_origen']}] → {lnk['nombre_destino']} [{lnk['puerto_destino']}] ({lnk['tipo']})",
                'label':  lnk['tipo'] if lnk['tipo'] not in ('Cobre',) else '',
                'color':  {'color': edge_color, 'highlight': '#22d3ee', 'hover': '#22d3ee'},
                'width':  2,
                'smooth': {'type': 'curvedCW', 'roundness': 0.1},
                'dashes': not lnk['activo'],
            })

        return JsonResponse({'nodes': nodes, 'edges': edges})

    except Exception as e:
        return JsonResponse({'nodes': [], 'edges': [], 'error': str(e)})


def manage_device(request):
    """
    API: Crear / Editar / Dar de baja dispositivos.
    Usa los SPs: NW_INSERT_DEVICE, NW_UPDATE_DEVICE, NW_DELETE_DEVICE.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    p      = request.POST
    action = p.get('action')

    # ── ALTA ──────────────────────────────────────────────────
    if action == 'add':
        result = nw_insert_device(
            nombre         = p.get('nombre', ''),
            ip             = p.get('ip', ''),
            tipo           = p.get('tipo', 'SWITCH'),
            marca          = p.get('marca', ''),
            modelo         = p.get('modelo', ''),
            sucursal       = p.get('sucursal', ''),
            area           = p.get('area', ''),
            snmp_version   = p.get('snmp_version', 'v2c'),
            community      = p.get('community', 'public'),
            snmp_port      = int(p.get('snmp_port', 161)),
            estado_monitoreo = 1,
        )
        return JsonResponse({
            'success': bool(result['guardado']),
            'lastID':  result['lastID'],
            'mensaje': result['mensaje'],
        })

    # ── EDICIÓN ───────────────────────────────────────────────
    elif action == 'edit':
        result = nw_update_device(
            id_device      = p.get('id_device'),
            nombre         = p.get('nombre', ''),
            ip             = p.get('ip', ''),
            tipo           = p.get('tipo', 'SWITCH'),
            marca          = p.get('marca', ''),
            modelo         = p.get('modelo', ''),
            sucursal       = p.get('sucursal', ''),
            area           = p.get('area', ''),
            snmp_version   = p.get('snmp_version', 'v2c'),
            community      = p.get('community', 'public'),
            snmp_port      = int(p.get('snmp_port', 161)),
            estado_monitoreo = int(p.get('estado_monitoreo', 1)),
        )
        return JsonResponse({
            'success': bool(result['guardado']),
            'lastID':  result['lastID'],
            'mensaje': result['mensaje'],
        })

    # ── BAJA LÓGICA ───────────────────────────────────────────
    elif action == 'delete':
        result = nw_delete_device(p.get('id_device'))
        return JsonResponse({
            'success': bool(result['guardado']),
            'mensaje': result['mensaje'],
        })

    return JsonResponse({'success': False, 'error': 'Acción no reconocida'})


def manage_link(request):
    """
    API: Crear / Eliminar enlaces entre dispositivos en el mapa.
    Usa los SPs: NW_INSERT_LINK, NW_DELETE_LINK.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    p      = request.POST
    action = p.get('action')

    # ── AGREGAR ENLACE ────────────────────────────────────────
    if action == 'add':
        result = nw_insert_link(
            id_origen      = p.get('id_origen'),
            puerto_origen  = p.get('puerto_origen', ''),
            id_destino     = p.get('id_destino'),
            puerto_destino = p.get('puerto_destino', ''),
            tipo_enlace    = p.get('tipo_enlace', 'Cobre'),
        )
        return JsonResponse({
            'success': bool(result['guardado']),
            'lastID':  result['lastID'],
            'mensaje': result['mensaje'],
        })

    # ── ELIMINAR ENLACE ───────────────────────────────────────
    elif action == 'delete':
        result = nw_delete_link(p.get('id_link'))
        return JsonResponse({
            'success': bool(result['guardado']),
            'mensaje': result['mensaje'],
        })

    return JsonResponse({'success': False, 'error': 'Acción no reconocida'})


def get_events(request):
    """
    API: Retorna los últimos eventos de la bitácora de red.
    Parámetro GET: limit (default 50)
    """
    limit  = int(request.GET.get('limit', 50))
    events = nw_get_events(limit=limit)

    # Serializar fechas
    for e in events:
        if hasattr(e.get('fecha_evento'), 'strftime'):
            e['fecha_evento'] = e['fecha_evento'].strftime('%Y-%m-%d %H:%M:%S')

    return JsonResponse({'events': events})
