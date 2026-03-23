from __future__ import absolute_import, unicode_literals

# Esto asegurará que la aplicación de Celery se siempre importa cuando
# Django se inicie para que @shared_task pueda usar esta aplicación.
from .celery import app as celery_app

__all__ = ('celery_app',)
