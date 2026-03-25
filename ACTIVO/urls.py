from django.urls import path
from .views.ActivoViews import *

app_name = 'ACTIVO'

urlpatterns = [
    path('panel/', panel_activo, name='panel'),
    path('gestion-activos/', gestion_activos, name='gestion_activos'),
    path('fill-categorias-activos/', fill_categorias_activos, name='fill_categorias_activos'),
    path('fill-proveedores-activos/', fill_proveedores_activos, name='fill_proveedores_activos'),
    path('fill-ubicaciones-activos/', fill_ubicaciones_activos, name='fill_ubicaciones_activos'),
    path('get-activos/', get_activos, name='get_activos'),
    path('get-activo-x-id/', get_activo_x_id, name='get_activo_x_id'),
    path('insert-activo/', insert_activo, name='insert_activo'),
    path('update-activo/', update_activo, name='update_activo'),
    path('delete-activo/', delete_activo, name='delete_activo'),

    path('gestion-categorias-activos/', gestion_categorias_activos, name='gestion_categorias_activos'),
    path('get-categorias-activos/', get_categorias_activos, name='get_categorias_activos'),
    path('get-categoria-activo-x-id/', get_categoria_activo_x_id, name='get_categoria_activo_x_id'),
    path('insert-categoria-activo/', insert_categoria_activo, name='insert_categoria_activo'),
    path('update-categoria-activo/', update_categoria_activo, name='update_categoria_activo'),
    path('delete-categoria-activo/', delete_categoria_activo, name='delete_categoria_activo'),

    # ---- NUEVAS RUTAS BASE ----
    # Catálogos
    path('gestion-proveedores/', gestion_proveedores, name='gestion_proveedores'),
    path('get-proveedores/', get_proveedores, name='get_proveedores'),
    path('get-proveedor-x-id/', get_proveedor_x_id, name='get_proveedor_x_id'),
    path('insert-proveedor/', insert_proveedor, name='insert_proveedor'),
    path('update-estado-proveedor/', update_estado_proveedor, name='update_estado_proveedor'),
    path('delete-proveedor/', delete_proveedor, name='delete_proveedor'),
    path('gestion-ubicaciones/', gestion_ubicaciones, name='gestion_ubicaciones'),
    path('gestion-motivos-salida/', gestion_motivos_salida, name='gestion_motivos_salida'),
    
    # Activos
    path('sacar-equipo/', sacar_equipo, name='sacar_equipo'),
    
    # Depreciación
    path('depreciaciones-aplicadas/', depreciaciones_aplicadas, name='depreciaciones_aplicadas'),
    path('historial-depreciacion/', historial_depreciacion, name='historial_depreciacion'),
    path('depreciacion-anual/', depreciacion_anual, name='depreciacion_anual'),
    
    # Consultas
    path('consulta-estado-actual/', consulta_estado_actual, name='consulta_estado_actual'),
    path('consulta-estado-mes/', consulta_estado_mes, name='consulta_estado_mes'),
    
    # Reportes
    path('reporte-general/', reporte_general, name='reporte_general'),
    path('reporte-bajas/', reporte_bajas, name='reporte_bajas'),
    path('reporte-depreciacion/', reporte_depreciacion, name='reporte_depreciacion'),

]
