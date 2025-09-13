"""
Configuración WSGI para el proyecto global_exchange.

Este archivo expone la variable ``application`` para el despliegue en servidores compatibles con WSGI.

.. module:: wsgi
   :platform: Unix, Windows
   :synopsis: Configuración WSGI para global_exchange
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "global_exchange.settings.dev")

application = get_wsgi_application()
