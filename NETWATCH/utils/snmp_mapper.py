import time
import socket
from pysnmp.hlapi import *

def mac_to_hex(mac_bytes):
    """Convierte bytes crudos de MAC a string hexadecimal (ej. 00:11:22:33:44:55)."""
    return ':'.join(f'{b:02x}' for b in mac_bytes)

def fetch_mac_table(ip, community='public', port=161):
    """
    Se conecta al switch vía SNMP y extrae la tabla FDB (Forwarding Data Base).
    Retorna un diccionario: { "MAC_ADDRESS": port_number }
    """
    mac_to_port = {}
    
    try:
        # OID base para dot1dTpFdbPort (1.3.6.1.2.1.17.4.3.1.2)
        # La tabla FDB devuelve los puertos Bridge (dot1dBasePort).
        for (errorIndication,
             errorStatus,
             errorIndex,
             varBinds) in nextCmd(SnmpEngine(),
                                  CommunityData(community, mpModel=1), # v2c
                                  UdpTransportTarget((ip, port), timeout=2.0, retries=1),
                                  ContextData(),
                                  ObjectType(ObjectIdentity('1.3.6.1.2.1.17.4.3.1.2')),
                                  lexicographicMode=False):

            if errorIndication or errorStatus:
                # Silencioso si falla
                break
                
            for varBind in varBinds:
                # varBind[0] contiene el OID + MAC decimal (ej. 1.3.6.1.2.1.17.4.3.1.2.0.11.22.33.44.55)
                # varBind[1] contiene el puerto (bridge port)
                oid_tuple = varBind[0].asTuple()
                mac_dec = oid_tuple[-6:]
                mac_hex = ':'.join(f'{b:02x}' for b in mac_dec).upper()
                bridge_port = int(varBind[1])
                mac_to_port[mac_hex] = bridge_port

    except Exception as e:
        print(f"[SNMP] Error leyendo MAC table de {ip}: {e}")
        
    return mac_to_port

def discover_topology(devices):
    """
    Función principal de descubrimiento.
    Toma una lista de diccionarios de dispositivos desde la DB:
    [{'id': 1, 'ip': '192.168.0.10', 'mac_address': 'AA:BB...', 'community': 'public', 'tipo': 'SWITCH'}, ...]
    
    Retorna una lista de enlaces propuestos:
    [{'from': id1, 'to': id2, 'port_from': '10', 'port_to': ''}, ...]
    """
    links = []
    
    # Filtrar solo switches y routers para interrogar
    switches = [d for d in devices if str(d.get('type', '')).upper() in ['SWITCH', 'ROUTER'] and d.get('ip')]
    
    for switch in switches:
        ip = switch.get('ip')
        comm = switch.get('community') or 'public'
        
        # Leer la tabla MAC del switch
        fdb = fetch_mac_table(ip, community=comm)
        
        if not fdb:
            continue
            
        # Correlacionar MACs aprendidas con los demás dispositivos administrados
        for dev in devices:
            if dev['id'] == switch['id']:
                continue
                
            dev_mac = str(dev.get('modelo', '')).upper().strip()
            
            # Formatear la MAC por si acaso (quitar guiones, espacios)
            dev_mac = dev_mac.replace('-', ':')
            
            if dev_mac in fdb:
                bridge_port = fdb[dev_mac]
                
                # Proponemos el enlace.
                # Nota: 'bridge_port' es numérico (ej. 12).
                # Un switch real en producción tendría varios MACs en un uplink, 
                # así que deberíamos filtrar puertos uplink. 
                # Por ahora hacemos una conexión básica.
                links.append({
                    'id_origen': switch['id'],
                    'puerto_origen': f"Port {bridge_port}",
                    'id_destino': dev['id'],
                    'puerto_destino': '', # No podemos saber el puerto destino (del otro lado) a menos que usemos LLDP
                    'tipo_enlace': 'Cobre'
                })
                
    return links

def auto_discover_switches(discovered_ips, default_community='public'):
    """
    Toma una lista de diccionarios con {'ip_address': '...', ...}
    Hace un getCmd SNMP a sysDescr.0 para comprobar si es un switch/router.
    Retorna una lista de las IPs descubiertas que son switches.
    """
    found_switches = []
    
    for d in discovered_ips:
        ip = d.get('ip_address')
        if not ip: continue
        
        try:
            iterator = getCmd(SnmpEngine(),
                              CommunityData(default_community, mpModel=1), # v2c
                              UdpTransportTarget((ip, 161), timeout=1.0, retries=0),
                              ContextData(),
                              ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))) # sysDescr
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            
            if errorIndication or errorStatus:
                continue
                
            sysdescr = str(varBinds[0][1]).lower()
            
            # Simple keyword matching to identify switches/routers
            keywords = ['switch', 'router', 'cisco', 'mikrotik', 'hp', 'aruba', 'procurve', 'sw']
            if any(kw in sysdescr for kw in keywords):
                found_switches.append(d)
                
        except Exception as e:
            pass
            
    return found_switches
