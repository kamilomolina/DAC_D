from django.shortcuts import render
from django.db import connections
from django.http import JsonResponse
from django.urls import reverse
from django.http import HttpResponseRedirect
import subprocess
import platform
import concurrent.futures
import threading
import ipaddress
import socket
import re

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
    """Invoca NW_GET_LINKS y retorna lista de conexiones de red."""
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
    """Invoca NW_GET_EVENTS y retorna los últimos eventos de la bitácora."""
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

    nw_update_device_status(id_device, nuevo_estado)

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
    'online':     {'background': '#10b981', 'border': '#059669', 'glow': 'rgba(16,185,129,0.5)'},
    'offline':    {'background': '#ef4444', 'border': '#dc2626', 'glow': 'rgba(239,68,68,0.5)'},
    'unknown':    {'background': '#64748b', 'border': '#475569', 'glow': 'rgba(100,116,139,0.4)'},
    'discovered': {'background': '#00d2ff', 'border': '#0099cc', 'glow': 'rgba(0,210,255,0.4)'},
}

DEVICE_ICONS = {
    'ROUTER':    '\uf4d0',   # fa-route
    'SWITCH':    '\uf6ff',   # fa-network-wired
    'SERVIDOR':  '\uf233',   # fa-server
    'AP':        '\uf1eb',   # fa-wifi
    'PC':        '\uf109',   # fa-laptop
    'OTRO':      '\uf10b',   # fa-mobile
}

DEVICE_SIZE = {
    'ROUTER':   34,
    'SWITCH':   32,
    'SERVIDOR': 30,
    'AP':       28,
    'PC':       26,
    'OTRO':     24,
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
# ENDPOINTS JSON / API — MONITOREO
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
    Incluye también los dispositivos descubiertos por el escáner.
    """
    try:
        devices    = nw_get_devices(estado=1)
        links      = nw_get_links()
        discovered = nw_get_discovered_ips()

        # ── Nodos de dispositivos administrados ──────────────────────────────
        nodes = []
        for d in devices:
            status = d.get('estado_actual', 'unknown') or 'unknown'
            if status == 'warning':
                status = 'online'
            col  = DEVICE_COLORS.get(status, DEVICE_COLORS['unknown'])
            tipo = (d.get('type') or 'OTRO').upper()
            if tipo not in DEVICE_ICONS:
                tipo = 'OTRO'

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
                    'face':   '"Font Awesome 6 Free"',
                    'weight': '900',
                    'code':   DEVICE_ICONS[tipo],
                    'size':   DEVICE_SIZE.get(tipo, 26),
                    'color':  col['background'],
                },
                'shadow': {
                    'enabled': True,
                    'color':   col['glow'],
                    'size':    10,
                    'x': 0, 'y': 2,
                }
            })

        # ── Nodos de dispositivos DESCUBIERTOS (floating) ────────────────────
        for d in discovered:
            tipo = (d.get('tipo_dispositivo') or 'OTRO').upper()
            if tipo not in DEVICE_ICONS:
                tipo = 'OTRO'
            icon_code = DEVICE_ICONS[tipo]
            col       = DEVICE_COLORS['discovered']

            # Etiqueta: hostname si existe, si no la IP
            hostname = d.get('hostname') or ''
            label    = hostname.split('.')[0] if hostname else d['ip_address']
            sublabel = d['ip_address'] if hostname else ''
            full_label = f"{label}\n{sublabel}" if sublabel else label

            nodes.append({
                'id':          f"disc_{d['id_discovered']}",
                'label':       full_label,
                'ip':          d['ip_address'],
                'area':        'Escáner',
                'sucursal':    d.get('vendor') or 'Desconocido',
                'tipo':        tipo,
                'marca':       d.get('vendor', ''),
                'modelo':      d.get('mac_address', ''),
                'community':   '',
                'descripcion': f"MAC: {d.get('mac_address','?')} | TTL: {d.get('ttl','?')} | Detectado automáticamente",
                'status':      'discovered',
                'shape':       'icon',
                'icon': {
                    'face':   '"Font Awesome 6 Free"',
                    'weight': '900',
                    'code':   icon_code,
                    'size':   DEVICE_SIZE.get(tipo, 24),
                    'color':  col['background'],
                },
                'shadow': {
                    'enabled': True,
                    'color':   col['glow'],
                    'size':    10,
                    'x': 0, 'y': 2,
                }
            })

        # ── Aristas / Conexiones ─────────────────────────────────────────────
        edges = []
        for lnk in links:
            c   = '#10b981' if lnk['activo'] else '#ef4444'
            lbl = ''
            if lnk.get('puerto_origen') and lnk.get('puerto_destino'):
                lbl = f"{lnk['puerto_origen']} ↔ {lnk['puerto_destino']}"
            edges.append({
                'id':     lnk['id'],
                'from':   lnk['from'],
                'to':     lnk['to'],
                'label':  lbl,
                'font':   {'align': 'top', 'size': 9, 'color': '#94a3b8'},
                'color':  {'color': c, 'highlight': '#f59e0b'},
                'width':  2,
                'smooth': {'type': 'cubicBezier', 'roundness': 0.4},
                'arrows': 'to;from',
                'dashes': not lnk['activo'],
            })

        return JsonResponse({'success': True, 'nodes': nodes, 'edges': edges})

    except Exception as e:
        print(f"[NETWATCH] Error get_topology_data: {e}")
        return JsonResponse({'success': False, 'error': str(e), 'nodes': [], 'edges': []})


def manage_device(request):
    """
    API: CRUD de dispositivos.
    Usa los SPs: NW_INSERT_DEVICE, NW_UPDATE_DEVICE, NW_DELETE_DEVICE.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    p      = request.POST
    action = p.get('action')

    # ── INSERTAR ───────────────────────────────────────────────
    if action == 'insert':
        result = nw_insert_device(
            nombre         = p.get('nombre', ''),
            ip             = p.get('ip_address', ''),
            tipo           = p.get('tipo_dispositivo', 'OTRO'),
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

    # ── ACTUALIZAR ─────────────────────────────────────────────
    elif action == 'update':
        result = nw_update_device(
            id_device      = p.get('id_device'),
            nombre         = p.get('nombre', ''),
            ip             = p.get('ip_address', ''),
            tipo           = p.get('tipo_dispositivo', 'OTRO'),
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

    for e in events:
        if hasattr(e.get('fecha_evento'), 'strftime'):
            e['fecha_evento'] = e['fecha_evento'].strftime('%Y-%m-%d %H:%M:%S')

    return JsonResponse({'events': events})


# ============================================================================
# HELPERS — SEGMENTOS DE RED
# ============================================================================

def nw_get_segments():
    """Retorna lista de segmentos de red guardados."""
    segs = []
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_GET_SEGMENTS')
            cols = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                segs.append(dict(zip(cols, row)))
    except Exception as e:
        print(f"[NETWATCH] Error en NW_GET_SEGMENTS: {e}")
    return segs


def nw_upsert_segment(nombre, subnet, descripcion=''):
    """Inserta o actualiza un segmento de red."""
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_UPSERT_SEGMENT', [nombre, subnet, descripcion])
            row = cursor.fetchone()
            if row:
                return {'lastID': row[0], 'guardado': row[1], 'mensaje': row[2]}
    except Exception as e:
        print(f"[NETWATCH] Error en NW_UPSERT_SEGMENT: {e}")
    return {'lastID': 0, 'guardado': 0, 'mensaje': 'Error'}


def nw_save_segment_layout(subnet, layout_json):
    """Guarda las posiciones X/Y del mapa de un segmento."""
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_SAVE_SEGMENT_LAYOUT', [subnet, layout_json])
    except Exception as e:
        print(f"[NETWATCH] Error en NW_SAVE_SEGMENT_LAYOUT: {e}")


def nw_get_discovered_by_segment(subnet):
    """Retorna IPs descubiertas filtradas por el prefijo /24 del segmento."""
    ips = []
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_GET_DISCOVERED_BY_SEGMENT', [subnet])
            cols = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                ips.append(dict(zip(cols, row)))
    except Exception as e:
        print(f"[NETWATCH] Error en NW_GET_DISCOVERED_BY_SEGMENT: {e}")
    return ips


# ============================================================================
# IP SCANNER — Escaneo no invasivo en segundo plano
# ============================================================================

# Mapa de prefijos OUI -> Fabricante (primeros 3 octetos de la MAC en mayúscula)
_OUI_MAP = {
    '00:50:56': 'VMware',          '00:0C:29': 'VMware',
    '00:1A:A0': 'Dell',            '00:14:22': 'Dell',
    'B8:AC:6F': 'Dell',            '18:66:DA': 'Dell',
    '3C:D9:2B': 'Hewlett-Packard', '00:26:55': 'Hewlett-Packard',
    '00:18:FE': 'Cisco',           '00:1E:E5': 'Cisco',
    '00:1B:D4': 'Cisco',           'F8:72:EA': 'Cisco',
    '04:DA:D2': 'Cisco',           '00:11:92': 'Cisco',
    'F8:C2:88': 'Ubiquiti',        '44:D9:E7': 'Ubiquiti',
    '00:27:22': 'Ubiquiti',        '24:A4:3C': 'Ubiquiti',
    '68:72:51': 'Ubiquiti',        'DC:9F:DB': 'Ubiquiti',
    '80:2A:A8': 'Ubiquiti',        '74:83:C2': 'MikroTik',
    '4C:5E:0C': 'MikroTik',        'D4:CA:6D': 'MikroTik',
    'B8:27:EB': 'Raspberry Pi',    'DC:A6:32': 'Raspberry Pi',
    '7C:2E:BD': 'Raspberry Pi',    '28:CD:C1': 'Apple',
    'A4:5E:60': 'Apple',           '00:1C:B3': 'Apple',
    '3C:15:C2': 'Apple',           '00:15:5D': 'Microsoft/Hyper-V',
}


def _get_vendor_from_mac(mac):
    """Deduce fabricante por los primeros 3 octetos de la MAC (OUI)."""
    if not mac or len(mac) < 8:
        return ''
    return _OUI_MAP.get(mac[:8].upper(), '')


def _extract_ttl(ping_output):
    """Extrae TTL de la salida del ping (Windows y Linux)."""
    m = re.search(r'TTL=(\d+)', ping_output, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def _guess_device_type(hostname, vendor, ttl):
    """
    Clasifica el dispositivo usando hostname, vendor y TTL.
    - TTL ~255 → Network gear (Cisco/Ubiquiti)
    - TTL ~128 → Windows PC
    - TTL ~64  → Linux/Mac/servidor
    """
    h = (hostname or '').lower()
    v = (vendor   or '').lower()

    # Por vendor conocido
    if 'cisco' in v:
        return 'SWITCH' if any(x in h for x in ['sw', 'switch']) else 'ROUTER'
    if any(x in v for x in ['ubiquiti', 'unifi', 'mikrotik']):
        if any(x in h for x in ['ap', 'wifi', 'wireless', 'uap']): return 'AP'
        if any(x in h for x in ['sw', 'switch']):                   return 'SWITCH'
        return 'ROUTER'
    if 'raspberry' in v:
        return 'SERVIDOR'

    # Por hostname
    if any(x in h for x in ['sw', 'switch', 'swt']):                           return 'SWITCH'
    if any(x in h for x in ['ap', 'wifi', 'wireless', 'uap']):                 return 'AP'
    if any(x in h for x in ['rt', 'router', 'gw', 'gateway', 'usg', 'edge']):  return 'ROUTER'
    if any(x in h for x in ['srv', 'server', 'nas', 'vm', 'esxi', 'proxmox']): return 'SERVIDOR'
    if any(x in h for x in ['pc', 'desk', 'lap', 'wks', 'workstation']):       return 'PC'

    # Por TTL como último recurso
    if ttl and ttl >= 200: return 'ROUTER'    # Network gear ~255
    if ttl and ttl >= 100: return 'PC'        # Windows ~128
    if ttl and ttl >= 50:  return 'SERVIDOR'  # Linux ~64

    return 'OTRO'


def nw_upsert_discovered_ip(ip, mac, hostname, tipo, vendor='', ttl=0):
    """Llama al SP NW_UPSERT_DISCOVERED_IP con todos los campos."""
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_UPSERT_DISCOVERED_IP',
                            [ip, mac, hostname, tipo, vendor, int(ttl) if ttl else 0])
    except Exception as e:
        print(f"[NETWATCH] Error en NW_UPSERT_DISCOVERED_IP ({ip}): {e}")


def nw_get_discovered_ips(subnet=None):
    """
    Retorna IPs descubiertas.
    Si se pasa subnet, filtra al prefijo /24 correspondiente.
    """
    if subnet:
        return nw_get_discovered_by_segment(subnet)
    ips = []
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.callproc('NW_GET_DISCOVERED_IPS')
            cols = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                ips.append(dict(zip(cols, row)))
    except Exception as e:
        print(f"[NETWATCH] Error en NW_GET_DISCOVERED_IPS: {e}")
    return ips


def parse_subnet(subnet_str):
    """
    Parsea una cadena de subred y retorna lista de IPs.
    Formatos soportados: '192.168.0.0/24' o '192.168.0.1-254'
    """
    subnet_str = subnet_str.strip()
    ips = []
    try:
        if '/' in subnet_str:
            network = ipaddress.ip_network(subnet_str, strict=False)
            ips = [str(ip) for ip in network.hosts()]
        elif '-' in subnet_str:
            base_ip, end_host = subnet_str.rsplit('-', 1)
            parts = base_ip.strip().split('.')
            if len(parts) == 4 and end_host.strip().isdigit():
                start = int(parts[3])
                end   = int(end_host.strip())
                base  = '.'.join(parts[:3])
                ips   = [f"{base}.{i}" for i in range(start, end + 1)]
        else:
            ipaddress.ip_address(subnet_str)
            ips = [subnet_str]
    except Exception as e:
        print(f"[NETWATCH] Error parseando subred '{subnet_str}': {e}")
    return ips


def _ping_and_discover(ip):
    """
    Ping ICMP no invasivo (1 paquete, timeout 1 s).
    Si el host responde: extrae MAC (ARP), Hostname (DNS inverso), TTL, Vendor.
    """
    is_win = platform.system().lower() == 'windows'
    param  = '-n' if is_win else '-c'
    cmd    = ['ping', param, '1', '-w', '1000' if is_win else '1', ip]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, timeout=3)
        if result.returncode != 0:
            return  # Host sin respuesta, ignorar

        ttl      = _extract_ttl(result.stdout)
        mac      = ''
        hostname = ''

        # MAC via ARP (solo funciona en misma subred local)
        try:
            arp = subprocess.run(['arp', '-a', ip], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, timeout=2)
            m = re.search(r'([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}', arp.stdout)
            if m:
                mac = m.group(0).replace('-', ':').upper()
        except Exception:
            pass

        # Hostname via DNS inverso (pasivo, sin paquetes extra)
        try:
            info = socket.gethostbyaddr(ip)
            if info and info[0]:
                hostname = info[0]
        except Exception:
            pass

        vendor = _get_vendor_from_mac(mac)
        tipo   = _guess_device_type(hostname, vendor, ttl)

        nw_upsert_discovered_ip(ip, mac, hostname, tipo, vendor, ttl)

    except subprocess.TimeoutExpired:
        pass
    except Exception as e:
        print(f"[NETWATCH] Error escaneando {ip}: {e}")


# Estado global del escaneo (para polling de progreso en frontend)
_SCAN_STATE = {'running': False, 'subnet': '', 'total': 0, 'done': 0}
_SCAN_LOCK  = threading.Lock()


def _network_scan_worker(subnet_str):
    """Worker que corre en hilo daemon y actualiza _SCAN_STATE."""
    global _SCAN_STATE
    ips = parse_subnet(subnet_str)
    if not ips:
        with _SCAN_LOCK:
            _SCAN_STATE['running'] = False
        return

    with _SCAN_LOCK:
        _SCAN_STATE.update({'running': True, 'subnet': subnet_str,
                            'total': len(ips), 'done': 0})

    print(f"[NETWATCH] Escaneando {len(ips)} IPs en {subnet_str} ...")

    def _run(ip):
        _ping_and_discover(ip)
        with _SCAN_LOCK:
            _SCAN_STATE['done'] += 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(30, len(ips))) as ex:
        ex.map(_run, ips)

    with _SCAN_LOCK:
        _SCAN_STATE['running'] = False

    print(f"[NETWATCH] Escaneo finalizado: {subnet_str}")


# ============================================================================
# ENDPOINTS API — SCANNER + SEGMENTOS
# ============================================================================

def start_network_scan(request):
    """
    POST /netwatch/api/scan/
    Inicia el escaneo de red en segundo plano.
    Body: subnet (str), segment_name (str, opcional)
    """
    auth = auth_required(request)
    if auth: return auth

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})

    subnet = request.POST.get('subnet', '').strip()
    nombre = request.POST.get('segment_name', subnet).strip()

    if not subnet:
        return JsonResponse({'success': False, 'error': 'Debe especificar una subred'})

    with _SCAN_LOCK:
        if _SCAN_STATE['running']:
            return JsonResponse({'success': False,
                                 'error': f"Escaneo en curso: {_SCAN_STATE['subnet']}"})

    nw_upsert_segment(nombre, subnet)

    total = len(parse_subnet(subnet))
    t = threading.Thread(target=_network_scan_worker, args=(subnet,))
    t.daemon = True
    t.start()

    return JsonResponse({'success': True,
                         'message': f'Escaneo iniciado para {subnet}',
                         'total': total})


def get_scan_status(request):
    """
    GET /netwatch/api/scan/status/
    Progreso del escaneo actual (para polling en el frontend).
    """
    with _SCAN_LOCK:
        state = dict(_SCAN_STATE)
    pct = int((state['done'] / state['total'] * 100)) if state['total'] > 0 else 0
    state['percent'] = pct
    return JsonResponse({'success': True, **state})


def inventario_ip(request):
    """Vista: Inventario de IPs con escáner integrado."""
    auth = auth_required(request)
    if auth: return auth

    subnet   = request.GET.get('subnet', '')
    segments = nw_get_segments()
    ctx = {
        **get_user_context(request),
        'segments':       segments,
        'active_subnet':  subnet,
        'discovered_ips': nw_get_discovered_ips(subnet=subnet) if subnet else [],
    }
    return render(request, 'netwatch/inventario_ip.html', ctx)


def get_discovered_api(request):
    """GET /netwatch/api/discovered/ — JSON de IPs descubiertas."""
    subnet = request.GET.get('subnet', '').strip()
    ips    = nw_get_discovered_ips(subnet=subnet if subnet else None)
    for ip in ips:
        if hasattr(ip.get('last_seen'), 'strftime'):
            ip['last_seen'] = ip['last_seen'].strftime('%Y-%m-%d %H:%M:%S')
    return JsonResponse({'success': True, 'ips': ips})


def manage_segments(request):
    """
    GET  /netwatch/api/segments/ — Lista segmentos.
    POST /netwatch/api/segments/ — Crear/actualizar segmento o guardar layout.
    """
    if request.method == 'GET':
        segs = nw_get_segments()
        for s in segs:
            for k in ('created_at', 'updated_at'):
                if hasattr(s.get(k), 'strftime'):
                    s[k] = s[k].strftime('%Y-%m-%d %H:%M:%S')
        return JsonResponse({'success': True, 'segments': segs})

    action = request.POST.get('action', 'upsert')

    if action == 'save_layout':
        subnet = request.POST.get('subnet', '')
        layout = request.POST.get('layout_json', '{}')
        nw_save_segment_layout(subnet, layout)
        return JsonResponse({'success': True})

    if action == 'upsert':
        nombre = request.POST.get('nombre', '')
        subnet = request.POST.get('subnet', '')
        desc   = request.POST.get('descripcion', '')
        res    = nw_upsert_segment(nombre, subnet, desc)
        return JsonResponse({'success': bool(res.get('guardado', 0)), **res})

    return JsonResponse({'success': False, 'error': 'Acción no reconocida'})
