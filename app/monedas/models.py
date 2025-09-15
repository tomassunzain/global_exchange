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
    nombre = models.CharField('Nombre', max_length=80)
    simbolo = models.CharField('Símbolo', max_length=5, default='₲')
    decimales = models.PositiveSmallIntegerField(
        'Decimales', default=0, validators=[MinValueValidator(0), MaxValueValidator(6)]
    )
    activa = models.BooleanField('Activa', default=True)

    # Moneda base del sistema (exactamente una)
    es_base = models.BooleanField('¿Es moneda base?', default=False)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-es_base', 'codigo']
        verbose_name = 'Moneda'
        verbose_name_plural = 'Monedas'
        constraints = [
            # Solo puede existir una fila con es_base=True
            models.UniqueConstraint(
                fields=['es_base'],
                condition=models.Q(es_base=True),
                name='uniq_moneda_base_global',
            ),
        ]

    def clean(self):
        if self.codigo:
            self.codigo = self.codigo.upper()

    def __str__(self):
        return f'{self.codigo} - {self.nombre}'


class TasaCambio(models.Model):
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name='tasas')
    compra = models.DecimalField('Compra', max_digits=12, decimal_places=2)
    venta = models.DecimalField('Venta', max_digits=12, decimal_places=2)
    variacion = models.DecimalField('Variación %', max_digits=5, decimal_places=2, default=0)
    fecha_actualizacion = models.DateTimeField('Última actualización', auto_now=True)
    activa = models.BooleanField('Activa', default=True)

    class Meta:
        ordering = ['-fecha_actualizacion']
        verbose_name = 'Tasa de Cambio'
        verbose_name_plural = 'Tasas de Cambio'

    def __str__(self):
        return f'{self.moneda.codigo}: {self.compra}/{self.venta}'