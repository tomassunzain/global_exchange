from django import forms
from .models import Moneda

class MonedaForm(forms.ModelForm):
    class Meta:
        model = Moneda
        fields = ['codigo', 'nombre', 'simbolo', 'decimales', 'tasa_cambio', 'activa', 'por_defecto']
        labels = {
            'codigo': 'Código ISO',
            'nombre': 'Nombre de la moneda',
            'simbolo': 'Símbolo',
            'decimales': 'Cantidad de decimales',
            'tasa_cambio': 'Tasa vs moneda base',
            'activa': 'Activa para operar',
            'por_defecto': 'Marcar como moneda por defecto',
        }
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PYG'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guaraní paraguayo'}),
            'simbolo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '₲'}),
            'decimales': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 6}),
            'tasa_cambio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00000001'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'por_defecto': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
