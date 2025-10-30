from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # REPORTES DAC VIEW
    path('reporte/pdf/<id_gasto>/', GenerarReportePDF.as_view(), name='reporte_pdf'),
    path('reporte/ingresos/pdf/<id_gasto>/', GenerarReporteIngresosPDF.as_view(), name='reporte_ingresos_pdf'),
    path('voucher/empleado/planilla/<id_planilla>', GenerarVoucherPDF.as_view(), name='generar_voucher'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)