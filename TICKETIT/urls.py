from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/notificaciones/reportes', views.notificacion_correos_reportes, name='notificacion_correos_reportes'),
    path('api/get/menus/modulo', views.menus_x_modulo, name='menus_x_modulo'),
    path('api/get/correos/acceso', views.correos_x_acceso, name='correos_x_acceso'),
    path('api/get/correos/not/acceso', views.correos_not_acceso, name='correos_not_acceso'),
    path('api/get/add/deletecorreos/acceso', views.add_delete_correo, name='add_delete_correo'),

    path('admin/sistemas/environments', views.environments_sistemas, name='environments_sistemas'),
    path('api/get/sistemas/url', views.sistemas_urls, name='sistemas_urls'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)