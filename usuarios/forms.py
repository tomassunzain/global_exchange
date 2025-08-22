from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import Role, UserRole

User = get_user_model()


class RegistroForm(forms.Form):
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput, min_length=8)
    password2 = forms.CharField(widget=forms.PasswordInput, min_length=8)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe un usuario con este correo.")
        return email

    def clean(self):
        data = super().clean()
        if data.get('password1') != data.get('password2'):
            raise ValidationError("Las contraseñas no coinciden.")
        return data


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Correo")


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ["email", "is_active", "password"]


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