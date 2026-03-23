import os
import django

# Configura la variable de entorno para especificar el archivo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','dacd.settings')

# Inicializa Django
django.setup()

vista_prueba()
