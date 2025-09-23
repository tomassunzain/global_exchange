"""
Modelos de la app 'monedas'.

- Moneda: catálogo de monedas operables en el sistema. Debe existir una y solo
  una moneda base (es_base=True). El código se normaliza a ISO 4217 (mayúsculas).
- TasaCambio: último precio de compra/venta por moneda. El tablero mostrará la
  cotización activa más reciente por cada moneda. (Puede incluir campos de
  auditoría de fuente/base/timestamp si se desea persistir datos del proveedor).
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models

ISO4217 = RegexValidator(
    regex=r'^[A-Z]{3}$',
    message='Usá un código ISO 4217 de 3 letras mayúsculas (ej.: PYG, USD, BRL).'
)


class MonedaManager(models.Manager):
    """Manager personalizado para Moneda con soporte para soft delete"""

    def get_queryset(self):
        return super().get_queryset().filter(activa=True)

    def all_with_inactive(self):
        """Retorna todas las monedas incluyendo las inactivas"""
        return super().get_queryset()


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

    # Moneda base del sistema (siempre PYG)
    es_base = models.BooleanField('¿Es moneda base?', default=False)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    objects = MonedaManager()

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

        # Validar que solo PYG puede ser moneda base
        if self.es_base and self.codigo != 'PYG':
            raise ValidationError('Solo la moneda PYG puede ser moneda base del sistema.')

    def save(self, *args, **kwargs):
        # Asegurar que PYG siempre sea la moneda base
        if self.codigo == 'PYG':
            self.es_base = True
            # Desactivar cualquier otra moneda base
            Moneda.objects.all_with_inactive().exclude(pk=self.pk).update(es_base=False)

        # Validar que no se pueda crear otra moneda base
        if self.es_base and self.codigo != 'PYG':
            self.es_base = False

        super().save(*args, **kwargs)

    def delete(self, soft_delete=True, *args, **kwargs):
        """Soft delete por defecto"""
        if soft_delete:
            self.activa = False
            self.save()
        else:
            # Hard delete solo si no es PYG
            if self.codigo == 'PYG':
                raise ValidationError('No se puede eliminar la moneda base PYG.')
            super().delete(*args, **kwargs)

    def __str__(self):
        """
        Retorna una representación legible de la moneda.
        """
        estado = " (inactiva)" if not self.activa else ""
        return f'{self.codigo} - {self.nombre}{estado}'


class TasaCambio(models.Model):
    """
    Cotización (compra/venta) por moneda. Permite múltiples registros históricos.
    """
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name='tasas')
    compra = models.DecimalField('Compra', max_digits=12, decimal_places=2)
    venta = models.DecimalField('Venta', max_digits=12, decimal_places=2)
    variacion = models.DecimalField('Variación %', max_digits=5, decimal_places=2, default=0,
                                    editable=False)

    # Campos para tracking y auditoría
    base_codigo = models.CharField('Base de cotización', max_length=3, validators=[ISO4217], default='PYG')
    fuente = models.CharField('Fuente', max_length=120, blank=True, help_text='Ej: Banco Central, API Externa, Manual')
    ts_fuente = models.DateTimeField('Timestamp (fuente)', null=True, blank=True)

    # Campos de control
    fecha_creacion = models.DateTimeField('Fecha de creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última actualización', auto_now=True)
    activa = models.BooleanField('¿Cotización activa?', default=True)
    es_automatica = models.BooleanField('¿Cargada automáticamente?', default=False)

    class Meta:
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['moneda', 'activa', '-fecha_creacion']),
            models.Index(fields=['moneda', 'ts_fuente']),
        ]
        constraints = [
            # Única "activa" por moneda
            models.UniqueConstraint(
                fields=['moneda'],
                condition=models.Q(activa=True),
                name='uniq_tasa_activa_por_moneda'
            ),
            # Evitar duplicar la misma lectura de fuente/ts
            models.UniqueConstraint(
                fields=['moneda', 'ts_fuente', 'fuente'],
                name='uniq_tasa_moneda_ts_fuente'
            ),
        ]

    def clean(self):
        if self.moneda and self.moneda.es_base:
            raise ValidationError('No se puede cargar tasa de cambio para la moneda base (PYG).')
        if self.compra <= 0 or self.venta <= 0:
            raise ValidationError('Los valores de compra y venta deben ser mayores a cero.')
        if self.venta < self.compra:
            raise ValidationError('El precio de venta no puede ser menor al precio de compra.')
        # Base **siempre** PYG
        self.base_codigo = 'PYG'

    def _tasa_previa(self):
        qs = TasaCambio.objects.filter(moneda=self.moneda)
        # preferí ts_fuente si está; si no, fecha_creacion
        if self.ts_fuente:
            qs = qs.filter(
                models.Q(ts_fuente__lt=self.ts_fuente) |
                models.Q(ts_fuente__isnull=True, fecha_creacion__lt=self.fecha_creacion)
            )
        else:
            qs = qs.filter(fecha_creacion__lt=self.fecha_creacion)
        return qs.order_by('-ts_fuente', '-fecha_creacion').first()

    def calcular_variacion(self):
        prev = (
            TasaCambio.objects.filter(moneda=self.moneda)
            .order_by('-ts_fuente', '-fecha_creacion')
            .first()
        )
        if not prev:
            return Decimal('0.00')
        if prev.compra > 0:
            v = ((self.compra - prev.compra) / prev.compra) * 100
            return v.quantize(Decimal('0.01'))
        return Decimal('0.00')

    def save(self, *args, **kwargs):
        # Forzar base PYG y veto a PYG en moneda
        if self.moneda and self.moneda.es_base:
            raise ValidationError('No se puede guardar tasa para PYG.')
        self.base_codigo = 'PYG'

        is_new = self.pk is None

        # La variación se calcula respecto a la última existente (antes de guardar la nueva)
        if is_new:
            self.variacion = self.calcular_variacion()

        super().save(*args, **kwargs)

        # Activación automática: esta queda activa y desactiva las otras
        if self.activa:
            (TasaCambio.objects
             .filter(moneda=self.moneda)
             .exclude(pk=self.pk)
             .update(activa=False))
