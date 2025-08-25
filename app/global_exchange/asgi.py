"""
Configuración ASGI para el proyecto global_exchange.

Este archivo expone la variable ``application`` para el despliegue en servidores compatibles con ASGI.

.. module:: asgi
   :platform: Unix, Windows
   :synopsis: Configuración ASGI para global_exchange
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')

application = get_asgi_application()
