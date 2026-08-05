from django.urls import path
from . import views as NetWatchView

urlpatterns = [
    # ── Vistas principales ─────────────────────────────────────────────────────────
    path('panel/',       NetWatchView.panel_netwatch,    name='panel_netwatch'),
    path('admin/',       NetWatchView.admin_netwatch,    name='admin_netwatch'),
    path('mapa/',        NetWatchView.mapa_red,          name='mapa_red'),
    path('inventario/',  NetWatchView.inventario_ip,     name='nw_inventario_ip'),

    # ── API — Monitoreo de estado ────────────────────────────────────────
    path('get/status/',      NetWatchView.get_network_status, name='get_network_status'),
    path('get/topology/',    NetWatchView.get_topology_data,  name='get_topology_data'),
    path('get/events/',      NetWatchView.get_events,         name='nw_get_events'),

    # ── API — CRUD dispositivos y enlaces ───────────────────────────────
    path('manage/device/',   NetWatchView.manage_device,      name='manage_device'),
    path('manage/link/',     NetWatchView.manage_link,        name='manage_link'),

    # ── API — IP Scanner ───────────────────────────────────────────────────────
    path('api/scan/',         NetWatchView.start_network_scan, name='nw_start_scan'),
    path('api/scan/status/',  NetWatchView.get_scan_status,   name='nw_scan_status'),
    path('api/discovered/',   NetWatchView.get_discovered_api, name='nw_get_discovered'),
    path('api/quick-save/',   NetWatchView.quick_save_device,  name='nw_quick_save'),

    # ── API — Segmentos de red ────────────────────────────────────────────────
    path('api/segments/',     NetWatchView.manage_segments,   name='nw_segments'),
]
