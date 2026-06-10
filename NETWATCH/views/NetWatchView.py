from django.shortcuts import render
from django.db import connections
from django.http import JsonResponse
from django.urls import reverse
from django.http import HttpResponseRedirect
import subprocess
import platform
import concurrent.futures

# --- CONEXIÓN PRINCIPAL ---
DB_NAME = 'netwatch_db'

def get_devices_from_db():
    """
    Obtiene la lista de dispositivos desde la base de datos ZEUS.
    """
    devices = []
    try:
        with connections[DB_NAME].cursor() as cursor:
            cursor.execute("""
                SELECT id_device, nombre, ip_address, area, sucursal, tipo_dispositivo, snmp_community, marca, descripcion 
                FROM netwatch_devices 
                WHERE estado_monitoreo = 1
            """)
            rows = cursor.fetchall()
            for r in rows:
                devices.append({
                    "id": r[0],
                    "name": r[1],
                    "ip": r[2],
                    "area": r[3],
                    "sucursal": r[4],
                    "type": r[5],
                    "community": r[6],
                    "marca": r[7],
                    "descripcion": r[8]
                })
    except Exception as e:
        print(f"Error cargando BD ZEUS: {e}")
        # Solo devolvemos vacío si falla la BD
    return devices

def ping_device(device):
    """
    Pings a device and checks its Power Source status via SNMP.
    """
    ip = device['ip']
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-w', '1000', ip]
    
    try:
        # 1. Verificar si está encendido (ICMP)
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        
        if result.returncode == 0:
            # 2. Si responde, verificamos la FUENTE DE PODER vía paquetes SNMP
            # Aquí el switch nos dirá si está con Energía Directa o UPS
            
            # SIMULACIÓN DE DETECCIÓN POR PAQUETES:
            # En un entorno real, aquí se envía la consulta SNMP al switch.
            # Si el switch responde que su fuente principal está DOWN pero sigue encendido,
            # significa que está con la UPS.
            
            is_on_ups = False
            # is_on_ups = check_snmp_power_status(ip, device['community']) # Función real
            
            # Simulación para el demo (puedes probar con IPs que terminen en .100)
            if ip.endswith('.100') or ip.endswith('.101'):
                is_on_ups = True

            if is_on_ups:
                return 'warning' # AMARILLO (Con UPS)
            return 'online'      # VERDE (Energía Directa)
            
        else:
            return 'offline'     # ROJO (Sin energía / Desconectado)
    except Exception:
        return 'offline'

# --- VISTAS DEL MÓDULO ---

def panel_netwatch(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return HttpResponseRedirect(reverse('login'))
    
    userName = request.session.get('userName', 'USUARIO')
    devices = get_devices_from_db()
    
    return render(request, 'netwatch/dashboard.html', {
        'userName': userName,
        'devices': devices
    })

def admin_netwatch(request):
    """
    Vista de Administración de Dispositivos.
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return HttpResponseRedirect(reverse('login'))
        
    userName = request.session.get('userName', 'USUARIO')
    devices = get_devices_from_db()
    
    return render(request, 'netwatch/admin.html', {
        'userName': userName,
        'devices': devices
    })

def get_network_status(request):
    """
    API endpoint que refresca los estados consultando la BD ZEUS.
    """
    devices = get_devices_from_db()
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_device = {executor.submit(ping_device, d): d for d in devices}
        
        for future in concurrent.futures.as_completed(future_to_device):
            device = future_to_device[future]
            try:
                status = future.result()
            except Exception:
                status = 'offline'
            
            results.append({
                'id': device['id'],
                'ip': device['ip'],
                'status': status
            })
            
    return JsonResponse({'statuses': results})

def manage_device(request):
    """
    API para Crear/Editar/Eliminar dispositivos.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        id_device = request.POST.get('id_device')
        nombre = request.POST.get('nombre')
        ip = request.POST.get('ip')
        area = request.POST.get('area')
        sucursal = request.POST.get('sucursal')
        tipo = request.POST.get('tipo')
        marca = request.POST.get('marca')
        community = request.POST.get('community', 'public')
        
        try:
            with connections[DB_NAME].cursor() as cursor:
                if action == 'add':
                    cursor.execute("""
                        INSERT INTO netwatch_devices (nombre, ip_address, area, sucursal, tipo_dispositivo, marca, snmp_community)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [nombre, ip, area, sucursal, tipo, marca, community])
                
                elif action == 'edit':
                    cursor.execute("""
                        UPDATE netwatch_devices 
                        SET nombre=%s, ip_address=%s, area=%s, sucursal=%s, tipo_dispositivo=%s, marca=%s, snmp_community=%s
                        WHERE id_device=%s
                    """, [nombre, ip, area, sucursal, tipo, marca, community, id_device])
                
                elif action == 'delete':
                    cursor.execute("UPDATE netwatch_devices SET estado_monitoreo=0 WHERE id_device=%s", [id_device])
                
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})
