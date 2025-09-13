"""
Módulo de modelos para la aplicación de clientes.
Contiene las definiciones de las clases de modelo y sus métodos.
"""
from django.db import models
from django.conf import settings
from commons.enums import EstadoRegistroEnum

class Cliente(models.Model):
    """
    Modelo que representa un cliente en el sistema.
    Almacena información relevante como nombre, correo, etc.
    """
    estado = models.CharField(
        max_length=20,
        choices=[(e.value, e.name.title()) for e in EstadoRegistroEnum],
        default=EstadoRegistroEnum.ACTIVO.value,
        help_text="Estado del cliente (activo, eliminado, suspendido, etc.)"
    )

    SEGMENTOS = [
        ("MIN", "Minorista"),
        ("CORP", "Corporativo"),
        ("VIP", "VIP"),
    ]
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=SEGMENTOS, default="MIN")
    usuarios = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="clientes")

    def __str__(self):
        """
        Retorna la representación en cadena del cliente.
        """
        return f"{self.nombre} ({self.get_tipo_display()})"