from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
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
    class Meta:
        model = Cliente
        fields = ["usuarios"]
        widgets = {
            "usuarios": forms.CheckboxSelectMultiple
        }