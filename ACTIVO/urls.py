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
    path('get-ubicaciones/', get_ubicaciones, name='get_ubicaciones'),
    path('get-ubicacion-x-id/', get_ubicacion_x_id, name='get_ubicacion_x_id'),
    path('insert-ubicacion/', insert_ubicacion, name='insert_ubicacion'),
    path('delete-ubicacion/', delete_ubicacion, name='delete_ubicacion'),

    path('gestion-motivos-salida/', gestion_motivos_salida, name='gestion_motivos_salida'),
    path('get-motivos-salida/', get_motivos_salida, name='get_motivos_salida'),
    path('get-motivo-salida-x-id/', get_motivo_salida_x_id, name='get_motivo_salida_x_id'),
    path('insert-motivo-salida/', insert_motivo_salida, name='insert_motivo_salida'),
    path('delete-motivo-salida/', delete_motivo_salida, name='delete_motivo_salida'),
    

    
    # Depreciación
    path('depreciaciones-aplicadas/', depreciaciones_aplicadas, name='depreciaciones_aplicadas'),
    path('get-depreciaciones-aplicadas/', get_depreciaciones_aplicadas, name='get_depreciaciones_aplicadas'),
    
    # Consultas
    path('consulta-estado-actual/', consulta_estado_actual, name='consulta_estado_actual'),
    path('consulta-estado-mes/', consulta_estado_mes, name='consulta_estado_mes'),
    
    # Reportes
    path('reporte-general/', reporte_general, name='reporte_general'),
    path('get-reporte-general/', get_reporte_general, name='get_reporte_general'),
    path('reporte-bajas/', reporte_bajas, name='reporte_bajas'),
    path('reporte-depreciacion/', reporte_depreciacion, name='reporte_depreciacion'),
    path('reporte-calendario/', reporte_calendario, name='reporte_calendario'),
    path('get-activos-calendario/', get_activos_calendario, name='get_activos_calendario'),
    path('get-activos-por-fecha/', get_activos_por_fecha, name='get_activos_por_fecha'),

]
