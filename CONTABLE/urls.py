from django.urls import path
from .views import ContableView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('panel/', ContableView.panel_contabilidad, name='panel_contabilidad'),
    path('panel/clasificacion/cuentas', ContableView.conta_clasificacion_cuentas, name='conta_clasificacion_cuentas'),

    path('panel/clasificacion/cuentas/nic', ContableView.conta_clasificacion_cuentas_nic, name='conta_clasificacion_cuentas_nic'),
    path('panel/cuentas/nic', ContableView.cuentas_nic, name='cuentas_nic'),

    path('panel/firmas/financieras', ContableView.firmas_view, name='firmas_view'),
    path('dataFirmasFinancieras', ContableView.dataFirmasFinancieras, name='dataFirmasFinancieras'),
    
    path('dataClasificacionCuentas', ContableView.dataClasificacionCuentas, name='dataClasificacionCuentas'),
    path('dataCuentasNIC', ContableView.dataCuentasNIC, name='dataCuentasNIC'),
    path('dataCuentasDisponiblesNIC', ContableView.dataCuentasDisponiblesNIC, name='dataCuentasDisponiblesNIC'),
    path('dataCuentasAsociadasNIC', ContableView.dataCuentasAsociadasNIC, name='dataCuentasAsociadasNIC'),

    path('dataCuentasContables', ContableView.dataCuentasContables, name='dataCuentasContables'),
    path('update_status_cuentas_contables', ContableView.update_status_cuentas_contables, name='update_status_cuentas_contables'),
    
    path('cuentas_contables/', ContableView.cuentas_contables, name='cuentas_contables'),
    path('obtener_subcuentas/', ContableView.obtener_subcuentas, name='obtener_subcuentas'),
    path('generar_codigo/', ContableView.generar_codigo, name='generar_codigo'),
    path('insertar_actualizar_cuenta/', ContableView.insertar_actualizar_cuenta, name='insertar_actualizar_cuenta'),
    path('conta_update_es_cuenta_padre', ContableView.conta_update_es_cuenta_padre, name='conta_update_es_cuenta_padre'),


    path('insert_update_clasificacion_cuentas', ContableView.insert_update_clasificacion_cuentas, name='insert_update_clasificacion_cuentas'),
    path('update_status_clasificacion_cuentas', ContableView.update_status_clasificacion_cuentas, name='update_status_clasificacion_cuentas'),

    path('insert_remove_cuenta_x_nic', ContableView.insert_remove_cuenta_x_nic, name='insert_remove_cuenta_x_nic'),

    path('insert_update_cuenta_nic', ContableView.insert_update_cuenta_nic, name='insert_update_cuenta_nic'),
    path('update_status_cuentas_nic', ContableView.update_status_cuentas_nic, name='update_status_cuentas_nic'),
    
    path('panel/cuentas/gastos', ContableView.cuentas_gastos, name='cuentas_gastos'),
    path('dataCuentasGastos', ContableView.dataCuentasGastos, name='dataCuentasGastos'),
    path('insert_update_cuentas_gastos', ContableView.insert_update_cuentas_gastos, name='insert_update_cuentas_gastos'),
    path('update_status_cuentas_gastos', ContableView.update_status_cuentas_gastos, name='update_status_cuentas_gastos'),
    path('conta_update_es_padre_cuentas_gastos', ContableView.conta_update_es_padre_cuentas_gastos, name='conta_update_es_padre_cuentas_gastos'),


    path('panel/contabilidad/partida/manual/<int:partida>/<int:empresa>', ContableView.conta_new_edit_partida, name='conta_new_edit_partida'),
    path('insert_update_partidas_header_details', ContableView.insert_update_partidas_header_details, name='insert_update_partidas_header_details'),
    path('get_tasa_cambio_x_fecha', ContableView.get_tasa_cambio_x_fecha, name='get_tasa_cambio_x_fecha'),
    
    path('panel/tasa/cambio', ContableView.conta_tasa_cambio, name='conta_tasa_cambio'),
    path('dataTasaCambio', ContableView.dataTasaCambio, name='dataTasaCambio'),
    path('insert_update_tasa_cambio', ContableView.insert_update_tasa_cambio, name='insert_update_tasa_cambio'),
    path('update_status_tasa_cambio', ContableView.update_status_tasa_cambio, name='update_status_tasa_cambio'),
    
    
    path('panel/libro/mayor/<int:empresa>', ContableView.conta_libro_mayor, name='conta_libro_mayor'),
    path('dataLibroMayor', ContableView.dataLibroMayor, name='dataLibroMayor'),
    
    
    path('panel/entregar/periodo/<int:empresa>', ContableView.conta_entregar_periodos, name='conta_entregar_periodos'),

]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
