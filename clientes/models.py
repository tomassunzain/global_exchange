from django.db import models
from django.conf import settings

class Cliente(models.Model):
    SEGMENTOS = [
        ("MIN", "Minorista"),
        ("CORP", "Corporativo"),
        ("VIP", "VIP"),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=SEGMENTOS, default="MIN")
    usuario = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="clientes")
