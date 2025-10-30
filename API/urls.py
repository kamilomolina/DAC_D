from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
#from drf_yasg.views import get_schema_view
#from drf_yasg import openapi
#from rest_framework import permissions

#schema_view = get_schema_view(
#    openapi.Info(
#        title="API de ejemplo",
#        default_version='v1',
#        description="Descripción de tu API",
#        # Términos del servicio y contacto son opcionales
#    ),
#    public=True,
#    permission_classes=(permissions.AllowAny,),
#)

urlpatterns = [
    # SEND QUERY POST
    path('update/estructura/super/local', UpdateEstructuraSuperToLocal.as_view(), name='update_estructura_super_nube_local'),
    
    # CRONTABS
    path('sincronizar/numero/cai/super/local/<maquina>', UpdateCAINumeroIngresado.as_view(), name='update_cai_numero_ingresado'),
    path('sincronizar/data/super/local/<maquina>', UpdateDataSuperToLocal.as_view(), name='sincronizar_data_super_nube_local'),
    path('sync/ingresos/pendientes/super/bancario', SyncIngresosPendientesToBank.as_view(), name='sync_ingresos_pendientes_super_bancario'),
    path('sync/data/global/local/<maquina>', UpdateDataGlobalToLocal.as_view(), name='sync_data_global_security_local'),
    path('get/disponiblidad/cajas/super/conn', GetDisponibilidadCajaSupermercado.as_view(), name='get_disponibilidad_cajas_super_conn'),
    path('sync/saldos/movil/app', updateSaldosMovil.as_view(), name='update_saldos_movil'),


    # ================================== REPORTES DATA ==================================    
    
    # COMPRAS
    path('reporte/ranking/proveedores', ReporteRankingProveedores.as_view(), name='reporte_ranking_proveedores'),
    path('reporte/ranking/proveedores/detalles', ReporteRankingProveedoresDetalles.as_view(), name='reporte_ranking_proveedores_detalles'),


    # SUPER
    path('articulos/proveedor/set/principal', SetPrincipalArticulosProveedorSupermercado.as_view(), name='articulos_proveedores_data'),
    path('reporte/articulos/proveedores', ArticulosProveedoresSupermercadoData.as_view(), name='articulos_proveedores_data'),





    # ================================== TOKEN FX ==================================   
    
    # TOKEN
    path('token/validar/solicitud', TokenValidarExisteUnaSolicitud.as_view(), name='token_validar_existe_una_solicitud'),

    path('token/generar/solicitud', TokenGenerarSolicitud.as_view(), name='token_generar_solicitud'),
    path('token/get/mis/solicitud', TokenGetMisSolicitudes.as_view(), name='token_get_mis_solicitudes'),
    path('token/get/solicitud', TokenGetSolicitudes.as_view(), name='token_get_solicitudes'),
    path('token/get/details/solicitud', TokenGetSolicitudesDetails.as_view(), name='token_get_solicitudes_details'),

    path('token/cancelar/solicitud', TokenCancelarSolicitud.as_view(), name='token_cancel_solicitudes'),
    path('token/detalle/solicitud/revisar', TokenRevisarDetalleSolicitud.as_view(), name='token_revisar_detalle_solicitud'),
    path('token/solicitud/comentario', TokenSolicitudComentario.as_view(), name='token_solicitud_comentario'),
    path('token/verify', TokenValidar.as_view(), name='token_validar'),
    path('token/v2/verify', TokenValidar_v2.as_view(), name='token_validar_v2'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)