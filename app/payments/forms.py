from django import forms
from .models import PaymentMethod

class PaymentMethodForm(forms.ModelForm):
    """
    Formulario dinámico para crear y editar métodos de pago, mostrando campos según el tipo seleccionado.
    """
    class Meta:
        model = PaymentMethod
        fields = [
            'payment_type',
            # Cuenta bancaria
            'titular_cuenta', 'tipo_cuenta', 'banco', 'numero_cuenta',
            # Billetera
            'proveedor_billetera', 'billetera_email_telefono', 'billetera_titular',
            # Tarjeta
            'tarjeta_nombre', 'tarjeta_numero', 'tarjeta_vencimiento', 'tarjeta_cvv', 'tarjeta_marca',
        ]
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            # Solo letras y espacios
            'titular_cuenta': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100', 'pattern': '^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'title': 'Solo letras', 'inputmode': 'text'}),
            'tipo_cuenta': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '50', 'pattern': '^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'title': 'Solo letras', 'inputmode': 'text'}),
            'banco': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100', 'pattern': '^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'title': 'Solo letras', 'inputmode': 'text'}),
            # Solo números
            'numero_cuenta': forms.NumberInput(attrs={'class': 'form-control', 'maxlength': '34', 'pattern': '^\d+$', 'title': 'Solo números', 'inputmode': 'numeric', 'min': '0'}),
            'proveedor_billetera': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100', 'pattern': '^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'title': 'Solo letras', 'inputmode': 'text', 'id': 'id_proveedor_billetera'}),
            'billetera_email_telefono': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100'}),
            'billetera_titular': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100', 'pattern': '^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'title': 'Solo letras', 'inputmode': 'text'}),
            'tarjeta_nombre': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '100', 'pattern': '^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'title': 'Solo letras', 'inputmode': 'text'}),
            'tarjeta_numero': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '19', 'title': '16 dígitos numéricos', 'inputmode': 'numeric'}),
            'tarjeta_vencimiento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'MM/AA o MM/AAAA',
                'title': 'Formato MM/AA o MM/AAAA',
                'inputmode': 'numeric',
                'maxlength': '7',
            }),
            'tarjeta_cvv': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '4', 'pattern': '^\d{3,4}$', 'title': '3 o 4 dígitos numéricos', 'inputmode': 'numeric'}),
            'tarjeta_marca': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '20', 'pattern': '^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'title': 'Solo letras', 'inputmode': 'text'}),
        }


    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        import re

        # Validaciones backend estrictas
        if payment_type == 'tarjeta':
            tarjeta_numero = cleaned_data.get('tarjeta_numero')
            if not tarjeta_numero or not re.fullmatch(r'\d{16}', str(tarjeta_numero)):
                self.add_error('tarjeta_numero', 'El número de tarjeta debe tener exactamente 16 dígitos numéricos.')
            tarjeta_cvv = cleaned_data.get('tarjeta_cvv')
            if not tarjeta_cvv or not re.fullmatch(r'\d{3,4}', str(tarjeta_cvv)):
                self.add_error('tarjeta_cvv', 'El CVV debe tener 3 o 4 dígitos numéricos.')
            tarjeta_nombre = cleaned_data.get('tarjeta_nombre')
            if tarjeta_nombre and not re.fullmatch(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+', tarjeta_nombre):
                self.add_error('tarjeta_nombre', 'Solo se permiten letras en el nombre de la tarjeta.')
            tarjeta_marca = cleaned_data.get('tarjeta_marca')
            if tarjeta_marca and not re.fullmatch(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+', tarjeta_marca):
                self.add_error('tarjeta_marca', 'Solo se permiten letras en la marca de la tarjeta.')
            # Validación de fecha de vencimiento
            tarjeta_vencimiento = cleaned_data.get('tarjeta_vencimiento')
            import datetime
            if tarjeta_vencimiento:
                # Permitir MM/AA o MM/AAAA
                match = re.fullmatch(r'(0[1-9]|1[0-2])/((\d{2})|(\d{4}))', tarjeta_vencimiento)
                if not match:
                    self.add_error('tarjeta_vencimiento', 'El formato debe ser MM/AA o MM/AAAA.')
                else:
                    mes = int(tarjeta_vencimiento[:2])
                    anio = tarjeta_vencimiento[3:]
                    if len(anio) == 2:
                        anio = int('20' + anio)
                    else:
                        anio = int(anio)
                    hoy = datetime.date.today()
                    # La fecha debe ser igual o posterior al mes actual
                    if anio < hoy.year or (anio == hoy.year and mes < hoy.month):
                        self.add_error('tarjeta_vencimiento', 'La fecha de vencimiento no puede ser pasada.')
                    if not (1 <= mes <= 12):
                        self.add_error('tarjeta_vencimiento', 'El mes debe estar entre 01 y 12.')

        if payment_type == 'cuenta_bancaria':
            titular_cuenta = cleaned_data.get('titular_cuenta')
            tipo_cuenta = cleaned_data.get('tipo_cuenta')
            banco = cleaned_data.get('banco')
            numero_cuenta = cleaned_data.get('numero_cuenta')
            if titular_cuenta and not re.fullmatch(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+', titular_cuenta):
                self.add_error('titular_cuenta', 'Solo se permiten letras en el nombre del titular.')
            if tipo_cuenta and not re.fullmatch(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+', tipo_cuenta):
                self.add_error('tipo_cuenta', 'Solo se permiten letras en el tipo de cuenta.')
            if banco and not re.fullmatch(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+', banco):
                self.add_error('banco', 'Solo se permiten letras en el banco.')
            if numero_cuenta and not re.fullmatch(r'\d+', str(numero_cuenta)):
                self.add_error('numero_cuenta', 'Solo se permiten números en el número de cuenta.')

        if payment_type == 'billetera':
            proveedor_billetera = cleaned_data.get('proveedor_billetera')
            billetera_titular = cleaned_data.get('billetera_titular')
            # Limpiar caracteres no permitidos (solo letras y espacios)
            if proveedor_billetera:
                proveedor_billetera_limpio = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', proveedor_billetera)
                cleaned_data['proveedor_billetera'] = proveedor_billetera_limpio
            if billetera_titular:
                billetera_titular_limpio = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', billetera_titular)
                cleaned_data['billetera_titular'] = billetera_titular_limpio
            billetera_email_telefono = cleaned_data.get('billetera_email_telefono')
            if not billetera_email_telefono:
                self.add_error('billetera_email_telefono', 'Debe ingresar un número de celular paraguayo o un email válido.')
            else:
                # Si solo números
                if billetera_email_telefono.isdigit():
                    if not billetera_email_telefono.startswith('09') or len(billetera_email_telefono) != 10:
                        self.add_error('billetera_email_telefono', 'El número debe empezar con 09 y tener 10 dígitos (ej: 0971234568).')
                else:
                    # Email debe ser válido y terminar en @gmail.com
                    email_regex = r'^[\w\.-]+@gmail\.com$'
                    if not re.fullmatch(email_regex, billetera_email_telefono):
                        self.add_error('billetera_email_telefono', 'El email debe ser válido y terminar en @gmail.com.')
        return cleaned_data


