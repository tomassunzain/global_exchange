from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models


ISO4217 = RegexValidator(
    regex=r'^[A-Z]{3}$',
    message='Usá un código ISO 4217 de 3 letras mayúsculas (ej.: PYG, USD, BRL).'
)


class Moneda(models.Model):
    codigo = models.CharField(
        'Código ISO', max_length=3, unique=True, validators=[ISO4217],
        help_text='Ej.: PYG, USD, BRL'
    )
    nombre = models.CharField('Nombre', max_length=80)  # Guaraní paraguayo, Dólar estadounidense, etc.
    simbolo = models.CharField('Símbolo', max_length=5, default='₲')  # ₲, $, R$, etc.
    decimales = models.PositiveSmallIntegerField(
        'Decimales', default=0, validators=[MinValueValidator(0), MaxValueValidator(6)]
    )
    # Tasa de cambio vs la moneda base configurada del sistema (definila en settings o admin)
    tasa_cambio = models.DecimalField('Tasa (vs base)', max_digits=18, decimal_places=8, default=1)
    activa = models.BooleanField('Activa', default=True)
    por_defecto = models.BooleanField('¿Moneda por defecto?', default=False)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    por_defecto = models.BooleanField('¿Moneda por defecto?', default=False)

    class Meta:
        ordering = ['-por_defecto', 'codigo']
        verbose_name = 'Moneda'
        verbose_name_plural = 'Monedas'
        constraints = [
            models.UniqueConstraint(
                fields=['por_defecto'],  # <-- ¡al menos un campo!
                condition=models.Q(por_defecto=True),  # <-- aplica solo cuando es True
                name='uniq_moneda_por_defecto_global',
            ),
        ]

    def clean(self):
        if self.codigo:
            self.codigo = self.codigo.upper()

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'
