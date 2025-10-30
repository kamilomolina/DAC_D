from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establece la variable de entorno predeterminada de Django para el módulo 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dacd.settings')

app = Celery('dacd')

# Usando una cadena aquí significa que el trabajador no tiene que serializar
# la configuración del objeto a un niño.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Cargar módulos de tareas de todas las aplicaciones registradas en Django.
app.autodiscover_tasks()
