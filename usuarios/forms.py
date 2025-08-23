"""
Formularios para la gestión de usuarios.

Incluye formularios para registro y autenticación de usuarios.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

User = get_user_model()

class RegistroForm(forms.Form):
    """
    Formulario para el registro de nuevos usuarios.

    Campos:
        email (EmailField): Correo electrónico del usuario.
        password1 (CharField): Contraseña.
        password2 (CharField): Confirmación de contraseña.
    """
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(widget=forms.PasswordInput, min_length=8)

    def clean_email(self):
        """
        Valida que el correo electrónico no esté registrado previamente.

        :return: Correo electrónico validado.
        :raises ValidationError: Si el correo ya existe.
        """
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe un usuario con este correo.")
        return email

    def clean(self):
        """
        Valida que las contraseñas coincidan.

        :return: Datos limpios del formulario.
        :raises ValidationError: Si las contraseñas no coinciden.
        """
        data = super().clean()
        if data.get('password1') != data.get('password2'):
            raise ValidationError("Las contraseñas no coinciden.")
        return data

class LoginForm(AuthenticationForm):
    """
    Formulario para el inicio de sesión de usuarios.

    Campos:
        username (EmailField): Correo electrónico del usuario.
    """
    username = forms.EmailField(label="Correo")