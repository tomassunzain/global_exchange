# transacciones/forms.py
from django import forms
from .models import Transaccion
from commons.enums import TipoTransaccionEnum

class TransaccionForm(forms.ModelForm):
    class Meta:
        model = Transaccion
        fields = ["cliente", "tipo", "moneda", "monto_operado"]

    # puedes personalizar los widgets si quieres bootstrap-friendly
    cliente = forms.ModelChoiceField(queryset=None)
    moneda = forms.ModelChoiceField(queryset=None)
    monto_operado = forms.DecimalField(decimal_places=2, max_digits=18)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from clientes.models import Cliente
        from monedas.models import Moneda
        self.fields["cliente"].queryset = Cliente.objects.all()
        self.fields["moneda"].queryset = Moneda.objects.exclude(codigo="PYG")
