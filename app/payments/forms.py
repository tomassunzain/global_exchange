from django import forms
from .models import PaymentMethod

class PaymentMethodForm(forms.ModelForm):
    """
    Formulario para crear y editar métodos de pago.

    :ivar Meta: Clase interna que define los campos y widgets del formulario.
    """
    class Meta:
        model = PaymentMethod
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
