"""
Configuración de rutas para la aplicación de usuarios.

Define las URLs para registro, login, verificación de email, gestión de roles y sesiones.
"""

from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Registro de usuario
    path('registro/', views.registro, name='registro'),
    # Verificación de email
    path('verificar/<uidb64>/<token>/', views.verificar_email, name='verificar'),
    # Inicio de sesión
    path('login/', views.login_view, name='login'),
    # Cierre de sesión
    path('logout/', views.logout_view, name='logout'),
    # Listado de roles
    path('roles/', views.roles_list, name='roles_list'),
    # Edición de rol
    path('roles/<int:group_id>/editar/', views.rol_editar, name='rol_editar'),
    # Asignación de rol a usuario
    path('usuarios/<int:user_id>/asignar-rol/', views.asignar_rol_a_usuario, name='asignar_rol'),
]
