from django.urls import path
from .views import DACView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # SALDOS NEGATIVOS
    path('reportes/super/negativos/saldo', DACView.reporte_negativos_super, name='reporte_negativos_super'),

    path('api/get/super/negativos/saldo', DACView.listNegativosSuperSaldo, name='listNegativosSuperSaldo'),
    path('api/get/super/saldo/articulo', DACView.getSaldoActualArticulo, name='getSaldoActualArticulo'),

    # EMPRESAS COMPETENCIAS
    path('admin/empresas/competencias', DACView.empresas_competencias, name='empresas_competencias'),
    path('api/list/empresas/competencia', DACView.listEmpresasCompetencias, name='listEmpresasCompetencias'),
    path('api/save/edit/empresas/competencias', DACView.saveEditEmpresasCompetencias, name='saveEditEmpresasCompetencias'),
    path('api/update/status/empresas/competencias', DACView.updateStatusEmpresasCompetencias, name='updateStatusEmpresasCompetencias'),
    
    # MOTIVOS COMPETENCIAS
    path('admin/motivos/ventas/perdidas', DACView.motivos_venta_perdida, name='motivos_venta_perdida'),
    path('api/list/motivos/ventas/perdidas', DACView.listMotivosVentasPerdidas, name='listMotivosVentasPerdidas'),
    path('api/save/edit/motivos', DACView.saveEditMotivosVP, name='saveEditMotivosVP'),
    path('api/update/status/motivos', DACView.updateStatusMotivos, name='updateStatusMotivos'),

    # VENTA PERDIDA
    path('admin/ventas/perdidas', DACView.ventas_perdidas, name='ventas_perdidas'),
    path('api/list/productos/formato', DACView.productosFormato, name='productosFormato'),
    path('api/list/presentaciones/productos/formato', DACView.presentacionesProductoFormato, name='presentacionesProductoFormato'),
    path('api/get/data/presentacion/producto', DACView.getDataPresentacionAlmacen, name='getDataPresentacionAlmacen'),
    path('api/save/venta/perdida', DACView.saveVentaPerdida, name='saveVentaPerdida'),
    
    path('admin/reporte/ventas/perdidas', DACView.reporte_ventas_perdidas, name='reporte_ventas_perdidas'),
    path('api/data/venta/perdida', DACView.data_reporte_venta_perdida, name='data_reporte_venta_perdida'),

    path('fox/facturas/<date1>/<date2>', DACView.consultar_facturas, name='consultar_facturas'),
    path('fox/facturas/prg', DACView.consultar_facturas_prg, name='consultar_facturas_prg'),
    path('fox/update/almacen/<id_almacen>/<nuevo_id_almacen_a>', DACView.actualizar_id_almacen_a, name='actualizar_id_almacen_a'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)