"""
Formularios para la gestión de usuarios.

Incluye formularios para registro y autenticación de usuarios.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from clientes.models import Cliente
from .models import Role, UserRole

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


class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        }),
        required=False,
        help_text="Dejar en blanco para mantener la contraseña actual"
    )

    class Meta:
        model = User
        fields = ["email", "is_active", "password"]
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'usuario@ejemplo.com'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        help_texts = {
            'email': 'Dirección de correo electrónico única',
            'is_active': 'Solo usuarios activos pueden iniciar sesión'
        }


class UserCreateForm(forms.ModelForm):
    """Formulario para crear usuarios desde el panel de administración"""
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        }),
        min_length=8,
        help_text="Mínimo 8 caracteres"
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        }),
        min_length=8,
        help_text="Repite la contraseña anterior"
    )

    class Meta:
        model = User
        fields = ["email", "is_active"]
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'usuario@ejemplo.com'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        help_texts = {
            'email': 'Dirección de correo electrónico única',
            'is_active': 'Solo usuarios activos pueden iniciar sesión'
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe un usuario con este correo.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2:
            if password1 != password2:
                raise ValidationError("Las contraseñas no coinciden.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class AsignarRolForm(forms.Form):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Obtener todos los roles disponibles
        roles = Role.objects.all()

        # Crear checkboxes para cada rol
        choices = [(role.id, role.name) for role in roles]
        self.fields['roles'] = forms.MultipleChoiceField(
            choices=choices,
            widget=forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            required=False
        )

        # Pre-seleccionar roles actuales del usuario si existe
        if user:
            current_roles = user.user_roles.values_list('role_id', flat=True)
            self.fields['roles'].initial = list(current_roles)


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del rol'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del rol'
            })
        }

class AsignarClientesAUsuarioForm(forms.Form):
    clientes = forms.ModelMultipleChoiceField(
        queryset=Cliente.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop("usuario")
        super().__init__(*args, **kwargs)
        self.fields["clientes"].initial = self.usuario.clientes.all()

    def save(self):
        self.usuario.clientes.set(self.cleaned_data["clientes"])
        self.usuario.save()
        return self.usuario
