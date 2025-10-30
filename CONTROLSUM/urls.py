from django.urls import path
from .views import ControlSumView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('logout', ControlSumView.logoutRequest, name='logoutRequest'),
    path('dashboard', ControlSumView.dashboard, name='dashboard'),
    path('panel/', ControlSumView.panel_controlsuministros, name='panel_controlsuministros'),

    # ------------------------------------------------------------------------------------------------------------------------ #

    path('listado/suministros', ControlSumView.listado_suministro_data, name='listado_suministro_data'),
    path('insertar/actualizar/suministro', ControlSumView.insertar_actualizar_suministro, name='insertar_actualizar_suministro'),
    path('get/suministros/data', ControlSumView.get_suministros_data, name='get_suministros_data'),
    path('get/grupos/data', ControlSumView.get_grupos_por_usuario, name='get_grupos_por_usuario'),
    path('get/almacenes/usuario', ControlSumView.get_almacenes_por_usuario, name='get_almacenes_por_usuario'),
    path('obtener/acreedores', ControlSumView.obtener_acreedores, name='obtener_acreedores'),

    # ------------------------------------------------------------------------------------------------------------------------ #

    # path('proveedores/por/categoria/data', ControlSumView.proveedores_por_categoria_data, name='proveedores_por_categoria_data'),
    path('actualizar/estado/suministro', ControlSumView.actualizar_estado_sum, name='actualizar_estado_sum'),
    path('obtener/stock/bajo/data', ControlSumView.obtener_stock_bajo_data, name='obtener_stock_bajo_data'),
    path('obtener/suministros/por/categoria/data', ControlSumView.obtener_suministros_por_categoria_data, name='obtener_suministros_por_categoria_data'),
    path('listado/asignaciones', ControlSumView.listado_asignaciones_data, name='listado_asignaciones_data'),
    path('get/asignaciones/data', ControlSumView.get_asignaciones_data, name='get_asignaciones_data'),
    path('insertar/actualizar/asignacion', ControlSumView.insertar_actualizar_asignacion, name='insertar_actualizar_asignacion'),   
    path('obtener/usuario/por/nombre_data', ControlSumView.obtener_usuario_por_nombre_data, name='obtener_usuario_por_nombre_data'),
    path('actualizar/estado/asignacion', ControlSumView.actualizar_estado_asignacion, name='actualizar_estado_asignacion'),
    path('obtener/asignacion/data', ControlSumView.obtener_asignacion_data, name='obtener_asignacion_data'),

    # ------------------------------------------------------------------------------------------------------------------------ #

    path('listado/requisicion/data', ControlSumView.listado_requisicion_data, name='listado_requisicion_data'),
    path('get/requisicion/data', ControlSumView.get_requisicion_data, name='get_requisicion_data'),
    path('actualizar/estado/detalle/requisicion_data', ControlSumView.actualizar_estado_detalle_requisicion_data, name='actualizar_estado_detalle_requisicion_data'),
    path('obtener/detalles/requisicion/data', ControlSumView.obtener_detalles_requisicion_data, name='obtener_detalles_requisicion_data'),   
    path('obtener/nombres/usuarios/data', ControlSumView.obtener_nombres_usuarios_data, name='obtener_nombres_usuarios_data'),
    path('actualizar/estado', ControlSumView.actualizar_estado, name='actualizar_estado'),
    path('grupos/por/usuario/data', ControlSumView.grupos_por_usuario_data, name='grupos_por_usuario_data'),
    path('insertar/actualizar/requisicion/data', ControlSumView.insertar_actualizar_requisicion_data, name='insertar_actualizar_requisicion_data'),
    path('actualizar/estado/requisicion', ControlSumView.actualizar_estado_requisicion, name='actualizar_estado_requisicion'),
    path('insertar/actualizar/detalle/requisicion/data', ControlSumView.insertar_actualizar_detalle_requisicion_data, name='insertar_actualizar_detalle_requisicion_data'),
    path('obtener/detalles/data', ControlSumView.obtener_detalles_data, name='obtener_detalles_data'),

    # ------------------------------------------------------------------------------------------------------------------------ #

    path('obtener/precio/unitario/data', ControlSumView.obtener_precio_unitario_data, name='obtener_precio_unitario_data'),
    path('obtener/requisicion/y/detalle/data', ControlSumView.obtener_requisicion_y_detalle_data, name='obtener_requisicion_y_detalle_data'),
    path('verificar/detalles/requisicion/data', ControlSumView.verificar_detalles_requisicion_data, name='verificar_detalles_requisicion_data'),

    # ------------------------------------------------------------------------------------------------------------------------ #

    path('editar/detalle/requisicion/data', ControlSumView.editar_detalle_requisicion_data, name='editar_detalle_requisicion_data'),
    # path('listado/proveedores/categorias/data', ControlSumView.listado_proveedores_categorias_data, name='listado_proveedores_categorias_data'),
    # path('get/proveedor/categoria/data', ControlSumView.get_proveedor_categoria_data, name='get_proveedor_categoria_data'),
    # path('insertar/actualizar/proveedor/categoria', ControlSumView.insertar_actualizar_proveedor_categoria, name='insertar_actualizar_proveedor_categoria'),
    # path('actualizar/estado/proveedor_categoria', ControlSumView.actualizar_estado_proveedor_categoria, name='actualizar_estado_proveedor_categoria'),
    path('listado/almacenes/data', ControlSumView.listado_almacenes_data, name='listado_almacenes_data'),
    path('get/almacenes/data', ControlSumView.get_almacenes_data, name='get_almacenes_data'),
    path('insertar/actualizar/almacen/data', ControlSumView.insertar_actualizar_almacen_data, name='insertar_actualizar_almacen_data'),

    # ------------------------------------------------------------------------------------------------------------------------ #

    path('actualizar/estado/almacenes', ControlSumView.actualizar_estado_almacenes, name='actualizar_estado_almacenes'),
    path('listado/adquisicion/data', ControlSumView.listado_adquisicion_data, name='listado_adquisicion_data'),
    path('get/adquisicion/data', ControlSumView.get_adquisicion_data, name='get_adquisicion_data'),
    path('insertar/actualizar/adquisicion/data', ControlSumView.insertar_actualizar_adquisicion_data, name='insertar_actualizar_adquisicion_data'),
    path('insertar/actualizar/detalle/adquisicion/data', ControlSumView.insertar_actualizar_detalle_adquisicion_data, name='insertar_actualizar_detalle_adquisicion_data'),
    path('obtener/requisiciones/usuario', ControlSumView.obtener_requisiciones_usuario, name='obtener_requisiciones_usuario'),
    path('obtener/requisicion/detalles/usuario', ControlSumView.obtener_requisicion_detalles_usuario, name='obtener_requisicion_detalles_usuario'),
    path('obtener/metodos/pago', ControlSumView.obtener_metodos_pago, name='obtener_metodos_pago'),
    path('actualizar/estado/adquisicion', ControlSumView.actualizar_estado_adquisicion, name='actualizar_estado_adquisicion'),
    path('obtener/adquisicion/y/detalle/data', ControlSumView.obtener_adquisicion_y_detalle_data, name='obtener_adquisicion_y_detalle_data'),
    path('obtener_detalle_adquisicion', ControlSumView.obtener_detalle_adquisicion, name='obtener_detalle_adquisicion'),

    # ------------------------------------------------------------------------------------------------------------------------ #

    path('listado/devoluciones/data', ControlSumView.listado_devoluciones_data, name='listado_devoluciones_data'),
    path('insertar/actualizar/devolucion/data', ControlSumView.insertar_actualizar_devolucion_data, name='insertar_actualizar_devolucion_data'),
    path('get/devoluciones/data', ControlSumView.get_devoluciones_data, name='get_devoluciones_data'),
    path('actualizar/estado/devolucion', ControlSumView.actualizar_estado_devolucion, name='actualizar_estado_devolucion'),
    path('obtener/motivos/devoluciones_data', ControlSumView.obtener_motivos_devoluciones_data, name='obtener_motivos_devoluciones_data'),

    # ------------------------------------------------------------------------------------------------------------------------ #
    path('movimientos/suministros/data', ControlSumView.movimientos_suministros_data, name='movimientos_suministros_data'),
    path('historial/suministros/data', ControlSumView.historial_suministros_data, name='historial_suministros_data'),
    path('obtener/movimientos/x/suministro', ControlSumView.obtener_movimientos_x_suministro, name='obtener_movimientos_x_suministro')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)