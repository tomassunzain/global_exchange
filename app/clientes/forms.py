"""
Formularios para la aplicación de clientes.
Define los formularios y validaciones para la gestión de clientes.
"""
from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    """
    Formulario para la gestión de clientes.
    """
    class Meta:
        model = Cliente
        fields = ["nombre", "tipo", "usuarios"]
        widgets = {
            "usuarios": forms.CheckboxSelectMultiple,
            }
        labels = {
            "nombre": "Nombre del Cliente",
            "tipo": "Segmento del Cliente",
            "usuarios": "Usuarios Asociados",
        }

class AsignarUsuariosAClienteForm(forms.ModelForm):
    """
    Formulario para asignar usuarios a un cliente.
    """
    class Meta:
        model = Cliente
        fields = ["usuarios"]
        widgets = {
    """
    Formularios para la aplicación de clientes.
    Define los formularios y validaciones para la gestión de clientes.
    """
    """
    Formulario para la gestión de clientes.
    """
    """
    Formulario para asignar usuarios a un cliente.
    """
        }