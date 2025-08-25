"""
Configuración principal de la aplicación usuarios.

Define la configuración y el nombre de la app para Django.
"""

from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    """
    Configuración de la clase de la aplicación usuarios.

    :ivar default_auto_field: Tipo de campo automático por defecto.
    :ivar name: Nombre de la aplicación.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
