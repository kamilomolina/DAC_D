from django.urls import path
from . import views as NetWatchView

urlpatterns = [
    # ── Vistas principales ────────────────────────────────────────────────────
    path('panel/',   NetWatchView.panel_netwatch, name='panel_netwatch'),
    path('admin/',   NetWatchView.admin_netwatch, name='admin_netwatch'),
    path('mapa/',    NetWatchView.mapa_red,        name='mapa_red'),

    # ── API — Escaneo de estados (ping / SNMP) ────────────────────────────────
    path('get/status/',    NetWatchView.get_network_status, name='get_network_status'),

    # ── API — Topología para Vis.js ───────────────────────────────────────────
    path('get/topology/',  NetWatchView.get_topology_data,  name='get_topology_data'),

    # ── API — Bitácora de eventos ─────────────────────────────────────────────
    path('get/events/',    NetWatchView.get_events,          name='nw_get_events'),

    # ── API — CRUD de dispositivos ────────────────────────────────────────────
    path('manage/device/', NetWatchView.manage_device,       name='manage_device'),

    # ── API — CRUD de enlaces / topología ────────────────────────────────────
    path('manage/link/',   NetWatchView.manage_link,         name='manage_link'),

    # ── IP SCANNER ───────────────────────────────────────────────────────────
    path('api/scan/',      NetWatchView.start_network_scan,  name='nw_start_scan'),
    path('api/discovered/',NetWatchView.get_discovered_api,  name='nw_get_discovered'),
    path('inventario/',    NetWatchView.inventario_ip,       name='nw_inventario_ip'),
]
