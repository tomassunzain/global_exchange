from django.db import models
from django.contrib.auth.models import User

class Cliente(models.Model):
    SEGMENTOS = [
        ("MIN", "Minorista"),
        ("CORP", "Corporativo"),
        ("VIP", "VIP"),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=SEGMENTOS, default="MIN")
    usuario = models.ManyToManyfield(User, related_name="clientes")
