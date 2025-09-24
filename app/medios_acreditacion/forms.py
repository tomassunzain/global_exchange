from django import forms

from .models import MedioAcreditacion
from commons.enums import TipoMedioAcreditacionEnum

class MedioAcreditacionForm(forms.ModelForm):
    """
    Formulario dinámico para crear y editar medios de acreditación, mostrando campos según el tipo seleccionado.
    """
    class Meta:
        model = MedioAcreditacion
        fields = [
            'tipo_medio',
            # Cuenta bancaria
            'titular_cuenta', 'tipo_cuenta', 'banco', 'numero_cuenta',
            # Billetera
            'proveedor_billetera', 'billetera_email_telefono', 'billetera_titular',
        ]
        widgets = {
            'tipo_medio': forms.Select(attrs={'class': 'form-select'}),
            'titular_cuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_cuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_cuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'proveedor_billetera': forms.TextInput(attrs={'class': 'form-control'}),
            'billetera_email_telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'billetera_titular': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        """
        Valida los campos requeridos y el formato según el tipo de medio de acreditación seleccionado.
        """
        import re

        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_medio')
        errors = {}

        if tipo == TipoMedioAcreditacionEnum.CUENTA_BANCARIA.value:
            # Validar campos obligatorios
            for field in ['titular_cuenta', 'tipo_cuenta', 'banco', 'numero_cuenta']:
                if not cleaned_data.get(field):
                    errors[field] = 'Este campo es obligatorio para cuenta bancaria.'
            # Validar nombre del titular (solo letras y espacios)
            titular = cleaned_data.get('titular_cuenta')
            if titular and not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', titular):
                errors['titular_cuenta'] = 'El nombre del titular solo puede contener letras y espacios.'
            # Validar tipo de cuenta (solo letras y espacios)
            tipo_cuenta = cleaned_data.get('tipo_cuenta')
            if tipo_cuenta and not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', tipo_cuenta):
                errors['tipo_cuenta'] = 'El tipo de cuenta solo puede contener letras y espacios.'
            # Validar banco (letras, números, espacios, puntos, guiones y tildes)
            banco = cleaned_data.get('banco')
            if banco and not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9 .\-]+$', banco):
                errors['banco'] = 'El nombre del banco solo puede contener letras, números, espacios, puntos y guiones.'
            # Validar número de cuenta (solo números, mínimo 6 dígitos)
            numero_cuenta = cleaned_data.get('numero_cuenta')
            if numero_cuenta and not re.match(r'^\d{6,}$', numero_cuenta):
                errors['numero_cuenta'] = 'El número de cuenta debe tener al menos 6 dígitos y solo contener números.'
        elif tipo == TipoMedioAcreditacionEnum.BILLETERA.value:
            for field in ['proveedor_billetera', 'billetera_email_telefono']:
                if not cleaned_data.get(field):
                    errors[field] = 'Este campo es obligatorio para billetera digital.'
            # Validar proveedor de billetera (solo letras y espacios)
            proveedor = cleaned_data.get('proveedor_billetera')
            if proveedor and not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', proveedor):
                errors['proveedor_billetera'] = 'El proveedor solo puede contener letras y espacios.'
            # Validar nombre del titular de billetera (si se ingresa, solo letras y espacios)
            billetera_titular = cleaned_data.get('billetera_titular')
            if billetera_titular and not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', billetera_titular):
                errors['billetera_titular'] = 'El nombre del titular solo puede contener letras y espacios.'
            # Validar email o teléfono
            billetera_email_telefono = cleaned_data.get('billetera_email_telefono')
            if billetera_email_telefono:
                if billetera_email_telefono.isdigit():
                    # Solo números: debe empezar con 09 y tener 10 dígitos
                    if not re.match(r'^09\d{8}$', billetera_email_telefono):
                        errors['billetera_email_telefono'] = 'El número debe empezar con 09 y tener exactamente 10 dígitos.'
                else:
                    # Si contiene letras o símbolos, debe terminar en @gmail.com
                    if not billetera_email_telefono.endswith('@gmail.com'):
                        errors['billetera_email_telefono'] = 'El email debe terminar en @gmail.com.'
        if errors:
            raise forms.ValidationError(errors)
        return cleaned_data
