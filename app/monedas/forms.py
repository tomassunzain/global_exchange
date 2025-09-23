"""
Forms de la app 'monedas'.

- MonedaForm: formulario simple para ABM de Moneda. Los widgets incluyen
  clases Bootstrap para una UI consistente con el resto del sistema.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Moneda, TasaCambio


class MonedaForm(forms.ModelForm):
    class Meta:
        model = Moneda
        fields = ['codigo', 'nombre', 'simbolo', 'decimales', 'activa']
        labels = {
            'codigo': 'Código ISO',
            'nombre': 'Nombre de la moneda',
            'simbolo': 'Símbolo',
            'decimales': 'Cantidad de decimales',
            'activa': 'Activa para operar',
        }
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PYG'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guaraní paraguayo'}),
            'simbolo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '₲'}),
            'decimales': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 6}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo'].upper()

        # Validar que no exista otra moneda con el mismo código (incluyendo inactivas)
        if self.instance.pk:
            # En edición, excluir la instancia actual
            existe = Moneda.objects.all_with_inactive().exclude(pk=self.instance.pk).filter(codigo=codigo).exists()
        else:
            # En creación, verificar contra todas las monedas
            existe = Moneda.objects.all_with_inactive().filter(codigo=codigo).exists()

        if existe:
            raise ValidationError('Ya existe una moneda con este código.')

        return codigo

    def clean(self):
        cleaned_data = super().clean()
        codigo = cleaned_data.get('codigo', '').upper()

        # Validar que solo PYG puede ser moneda base
        if codigo != 'PYG' and self.instance.es_base:
            raise ValidationError('Solo la moneda PYG puede ser moneda base del sistema.')

        return cleaned_data
