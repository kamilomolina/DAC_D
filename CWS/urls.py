from django.urls import path, include
from .views import LoginView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # LOGIN
    path('', LoginView.login, name='login'),
    path('modulos', LoginView.modulos, name='modulos_login'),
    path('api/request/login', LoginView.loginRequest, name='loginRequest'),
    path('logout', LoginView.logoutRequest, name='logoutRequest'),

    path('module-request/', LoginView.moduleRequest, name='moduleRequest'),
    path('obtener_empresas/', LoginView.obtener_empresas, name='obtener_empresas'),

    # Incluir las URLs de la aplicación "TALENTO"
    path('modulos/', include('TALENTO.urls')),

    # SERVER SIDE SAMPLE
    #path('admin/dashboard/ticketit', DACView.dashboardTicketit, name='dashboardTicketit'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)