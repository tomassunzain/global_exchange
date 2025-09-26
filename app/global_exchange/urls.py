"""
URL configuration for global_exchange project.

Configuración de URLs para el proyecto **global_exchange**.

Incluye rutas para:

- Panel de administración de Django.
- Aplicación de usuarios.
- Página de inicio (landing page).
- Dashboard principal.
- Aplicación de clientes.
- Aplicación de exchange (tasas de cambio).
- Documentación generada por Sphinx.
- Aplicación de monedas.
- Aplicación de pagos.
- Aplicación de medios de acreditación.
"""

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.views.generic import RedirectView
import os

#: Lista principal de URLs del proyecto.
urlpatterns = [
    # --- Administración ---
    path('admin/', admin.site.urls, name="admin"),

    # --- Usuarios ---
    path('usuarios/', include(('usuarios.urls', 'usuarios'), namespace='usuarios')),

    # --- Landing page ---
    path(
        '',
        __import__('global_exchange.views', fromlist=['landing_page']).landing_page,
        name='landing'
    ),

    # --- Dashboard principal ---
    path('dashboard/', lambda r: redirect('usuarios:dashboard'), name='dashboard'),

    # --- Clientes ---
    path('clientes/', include(('clientes.urls', 'clientes'), namespace='clientes')),

    # --- Exchange ---
    path('exchange/', include(('exchange.urls', 'exchange'), namespace='exchange')),

    # --- Documentación generada con Sphinx ---
    path("docs/", RedirectView.as_view(url="/docs/index.html", permanent=False)),
    re_path(
        r"^docs/(?P<path>.*)$",
        serve,
        {"document_root": os.path.join(settings.BASE_DIR, "docs/build/html")},
        name="documentacion",
    ),

    # --- Monedas ---
    path('monedas/', include('monedas.urls')),

    # --- Pagos ---
    path('payments/', include(('payments.urls', 'payments'), namespace='payments')),

    # --- Medios de acreditación ---
    path(
        'medios_acreditacion/',
        include(('medios_acreditacion.urls', 'medios_acreditacion'), namespace='medios_acreditacion')
    ),
]
