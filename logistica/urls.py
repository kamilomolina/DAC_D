from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('logistica/modal_crear_programacion', views.vista_crear_programacion, name='modal_programacion'),
    path('logistica/procesar_consolidados/', views.procesar_consolidados, name='procesar_consolidados'),
    path('logistica/vehiculos/obtener_vehiculos', views.obtener_vehiculos, name='obtener_vehiculos'),
    path('logistica/destinos/obtener_destinos', views.obtener_destinos, name='obtener_destinos'),
    path('logistica/combustibles/obtener_combustibles', views.obtener_combustibles, name='obtener_combustibles'),
    path('logistica/tripulantes/obtener_tripulantes', views.obtener_tripulantes, name='obtener_tripulantes'),
    path('logistica/programacion/modal_proceso', views.vista_proceso_programacion, name='modal_proceso_p'),
    path('logistica/programaciones', views.vista_tabla_programaciones, name='programaciones'),
    path('logistica/programaciones/insertar_programacion', views.insertar_programacion, name='insertar_programaciones'),
    path('logistica/programaciones_all', views.vista_programacion_all, name='programaciones_all'),
    path('logistica/programaciones_data', views.obtener_programaciones_data, name='programaciones_all_data'),
    path('logistica/programaciones_proceso/<int:id_programacion>', views.actualizar_programacion_historial, name='programaciones_proceso'),
    path('logistica/obtener_programacion/<int:id_programacion>/', views.obtener_datos_programacion, name='obtener_datos_programacion'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)