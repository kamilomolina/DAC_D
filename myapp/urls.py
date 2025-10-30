from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.vista_principal, name="vista_principal"),
    path('telefonos/', views.vista_telefonos, name='lista_telefonos'),
    path('telefonos/', views.vista_telefonos, name='vista_telefonos'),
    path('telefonos/obtener_telefonos/', views.obtener_telefonos, name='obtener_telefonos'),
    path('favicon.ico', views.favicon), 
    path('telefonos/editar/<int:telefono_id>/', views.editar_telefono, name='editar_telefono'),
    path('telefonos/agregar/', views.agregar_telefono, name='agregar_telefono'),
    path('', views.index, name='index'),
    path('telefonos/eliminar_telefono/<int:telefono_id>/', views.eliminar_telefono, name='eliminar_telefono'),
    path('telefonos/obtener_supervisores/', views.obtener_supervisores, name='obtener_supervisores'),
    path('telefonos/obtener_vendedores/', views.obtener_vendedores, name='obtener_vendedores'),        
    path('telefonos/obtener_vendedores_modal/<str:nombre_vendedor>/', views.obtener_vendedores_modal, name='obtener_vendedores_modal'),  
    path('telefonos/obtener_usuarios/', views.obtener_usuarios, name='obtener_usuarios'),        
    path('telefonos/obtener_codigo/', views.obtener_codigo, name='obtener_codigo'),
    path('telefonos/obtener_rutas/', views.obtener_rutas, name='obtener_rutas'),
    path('telefonos/obtener_ruta_v/<str:nombre_empleado>/', views.obtener_rutas_v, name='obtener_rutas_v'),
    path('telefonos/obtener_vendedores_no_a/<str:nombre_empleado>/', views.obtener_vendedores_no_asociados, name='obtener_rutas_v_no'),
    path('telefonos/obtener_ruta_x_vendedor/<str:id_empleado>/', views.rutas_por_vendedor, name='rutas_por_vendedor'),
    path('telefonos/obtener_rotacion_productos/<str:fecha_inicio>/<str:fecha_fin>/<int:entero1>/<int:entero2>/', views.obtener_rotacion_producto, name='obtener_rotacion_producto'),
    path('productos/rotacion_productos/<int:mes>/<int:mes2>/<int:anio>/', views.vista_rotacion_producto, name='vista_rotacion_productos'),

    # API
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)