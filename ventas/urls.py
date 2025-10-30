from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('vista_ventas_perdidas/', views.vista_ventas_perdidas, name='vista_ventas_p'),
    path('vista_ventas_perdidas_all/', views.vista_ventas_perdidas_all, name='vista_ventas_p'),
    path('vista_agregar_venta_perdida/', views.vista_agregar_venta_perdida, name='vista_agregar_venta_perdida'),
    path('vista_configuracion_venta_perdida/', views.vista_configuracion_venta_perdida, name='configuracion_venta_perdida'),
    path('vista_reporte_ventas_perdidas/', views.vista_reporte_ventas_perdidas, name='reporte_venta_perdida'),


    path('obtener_motivos/', views.obtener_motivos_ventas_perdidas, name='lista_motivos'),
    path('obtener_empresas_competencias/', views.obtener_empresas_competencias, name='lista_competencias'),
    path('guardar_motivo/', views.guardar_motivo, name='guardar_motivo'),
    path('editar_motivo/', views.editar_motivo, name='editar_motivo'),
    path('borrar_motivo/', views.borrar_motivo, name='borrar_motivo'),
    path('obtener_ventas_perdidas/', views.obtener_ventas_perdidas, name='lista_ventas_perdidas'),
    path('obtener_clientes/', views.obtener_clientes, name='lista_clientes'),
    path('obtener_clientes_super/', views.obtener_clientes_supermercado, name='lista_clientes_supermercado'),
    path('obtener_productos_distribuidora/<int:idCliente>/', views.obtener_productos_distribuidora, name='obtener_productos_distribuidora'),
    path('obtener_productos_supermercado/<int:idCliente>/<int:idAlmacen>/', views.obtener_productos_supermercado, name='obtener_productos_supermercado'),
    path('obtener_motivos/', views.obtener_motivos_ventas_perdidas, name='lista_motivos2'),
    path('vista_configuracion_venta_perdida/obtener_empresas_competencias/', views.obtener_empresas_competencias, name='lista_competencias2'),
    path('guardar_empresa_competencia/', views.guardar_empresa_competencia, name='agregar_empresa_competencia'),
    path('editar_empresa_competencia/<int:id_competencia>/', views.editar_empresa_competencia, name='editar_empresa_competencia'),
    path('eliminar_empresa_competencia/<int:id_competencia>/', views.eliminar_empresa_competencia, name='eliminar_empresa_competencia'),
    path('almacenar_venta_perdida/', views.almacenar_venta_perdida, name='almacenar_venta_perdida'),
    path('obtener_almacenes/', views.obtener_almacenes, name='lista_almacenes'),
    path('obtener_almacenes_dc/', views.obtener_almacenes_dc, name='lista_almacenes_dc'),
    path('obtener_grupos/', views.obtener_grupo, name='lista_grupos'),
    path('obtener_subgrupos/', views.obtener_subgrupos, name='lista_subgrupos'),
    path('obtener_categorias/', views.obtener_categoria, name='lista_categorias'),
    path('obtener_marcas/', views.obtener_marcas, name='lista_marcas'),
    path('obtener_segmentos/', views.obtener_segmentos, name='lista_segmentos'),
    path('obtener_ventas_filtradas/', views.obtener_ventas_perdidas_filtradas, name='lista_ventasf'),
    path('obtener_ventas_filtradas_supermercado/', views.obtener_ventas_perdidas_filtradas_supermercado, name='lista_ventas_supermercado'),
    path('obtener_productos_supermercado2/<int:idCliente>/<int:idAlmacen>/', views.obtener_productos_supermercado2, name='obtener_productos_supermercado2'),
    
    
    # API
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)