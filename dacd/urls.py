from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from django.conf.urls import handler404
from CWS.views import custom_404

urlpatterns = [
    path('DAC/', include('myapp.urls')), 
    path('DAC/', include('logistica.urls')), 
    path('DAC/ventas/', include('ventas.urls')), 
    path('DAC/', include('DAC.urls')), 
    path('TICKETIT/', include('TICKETIT.urls')), 
    path('CWS/', include('CWS.urls')), 
    path('API/', include('API.urls')), 
    path('REPORTERIA/', include('REPORTERIA.urls')),
    path('CWS/modulos/contabilidad/', include('CONTABLE.urls')),
    path('CWS/modulos/control/suministros/', include('CONTROLSUM.urls'))
]

# Configuración de handlers para errores
handler404 = 'CWS.views.custom_404'

# Manejo de archivos estáticos y de medios (solo en DEBUG)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)