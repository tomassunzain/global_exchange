from django.db import models
from clientes.models import Cliente
from commons.enums import TipoMedioAcreditacionEnum

class MedioAcreditacion(models.Model):
    """
    Modelo que representa un medio de acreditación disponible en el sistema.
    """
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="medios_acreditacion", verbose_name="Cliente")
    TIPO_MEDIO_CHOICES = [(e.value, e.name.replace('_', ' ').title()) for e in TipoMedioAcreditacionEnum]
    tipo_medio = models.CharField(max_length=20, choices=TIPO_MEDIO_CHOICES, verbose_name="Tipo de Medio de Acreditación", default=TipoMedioAcreditacionEnum.CUENTA_BANCARIA.value)

    #TODO unificar modelos a uno generico con payments

    # Campos para Cuenta Bancaria
    titular_cuenta = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre del titular")
    tipo_cuenta = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tipo de cuenta")
    banco = models.CharField(max_length=100, blank=True, null=True, verbose_name="Banco")
    numero_cuenta = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número de cuenta o IBAN")

    # Campos para Billetera Digital
    proveedor_billetera = models.CharField(max_length=100, blank=True, null=True, verbose_name="Proveedor de billetera")
    billetera_email_telefono = models.CharField(max_length=100, blank=True, null=True, verbose_name="Email o teléfono asociado")
    billetera_titular = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre del titular billetera")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Medio de Acreditación"
        verbose_name_plural = "Medios de Acreditación"
        ordering = ["id"]

    def __str__(self):
        if self.tipo_medio == TipoMedioAcreditacionEnum.CUENTA_BANCARIA.value:
            return f"Cuenta bancaria ({self.banco or ''} - {self.numero_cuenta or ''})"
        elif self.tipo_medio == TipoMedioAcreditacionEnum.BILLETERA.value:
            return f"Billetera ({self.proveedor_billetera or ''} - {self.billetera_email_telefono or ''})"
        return f"Medio de acreditación {self.pk}"
