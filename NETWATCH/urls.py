from django.urls import path
from . import views as NetWatchView

urlpatterns = [
    path('panel/', NetWatchView.panel_netwatch, name='panel_netwatch'),
    path('admin/', NetWatchView.admin_netwatch, name='admin_netwatch'),
    path('get/status/', NetWatchView.get_network_status, name='get_network_status'),
    path('manage/device/', NetWatchView.manage_device, name='manage_device'),
]
