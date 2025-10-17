# transacciones/forms.py
from django import forms
from .models import Transaccion
from commons.enums import TipoTransaccionEnum

class TransaccionForm(forms.ModelForm):
    email_mfa = forms.EmailField(
        label="Email para Código de Verificación",
        required=False, # Será requerido dinámicamente
        help_text="Si la operación es una COMPRA (débito), se enviará un código a este email para confirmar."
    )

    class Meta:
        model = Transaccion
        fields = ["cliente", "tipo", "moneda", "monto_operado", "medio_pago", "email_mfa"]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            from clientes.models import Cliente
            from monedas.models import Moneda
            from payments.models import PaymentMethod

            self.fields["cliente"].queryset = Cliente.objects.all()
            self.fields["moneda"].queryset = Moneda.objects.exclude(codigo="PYG")
            self.fields["medio_pago"].queryset = PaymentMethod.objects.none()

            if "cliente" in self.data:
                try:
                    cliente_id = int(self.data.get("cliente"))
                    self.fields["medio_pago"].queryset = PaymentMethod.objects.filter(cliente_id=cliente_id)
                except (ValueError, TypeError):
                    pass
            elif self.instance.pk:
                self.fields["medio_pago"].queryset = self.instance.cliente.metodos_pago.all()
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        email_mfa = cleaned_data.get("email_mfa")

        # Requerir email_mfa si es una compra (débito)
        if tipo == TipoTransaccionEnum.COMPRA and not email_mfa:
            self.add_error('email_mfa', 'Este campo es requerido para transacciones de compra.')

        return cleaned_data
