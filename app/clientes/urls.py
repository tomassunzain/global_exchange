"""
Rutas URL para la aplicación de clientes.
"""
from django.urls import path
from . import views

app_name = 'clientes'
urlpatterns = [
     # Listado de clientes
    path("", views.clientes_list, name="clientes_list"),

    # CRUD
    path("nuevo/", views.cliente_create, name="cliente_create"),
    path("<int:cliente_id>/editar/", views.cliente_edit, name="cliente_edit"),
    path("<int:cliente_id>/eliminar/", views.cliente_delete, name="cliente_delete"),
    path("<int:cliente_id>/restaurar/", views.cliente_restore, name="cliente_restore"),

    # Cambio de cliente activo
    path("seleccionar/<int:cliente_id>/", views.seleccionar_cliente, name="seleccionar_cliente"),

    #Asignar Usuarios a un Cliente
    path("<int:cliente_id>/asignar-usuarios/", views.asignar_usuarios_a_cliente, name="asignar_usuarios"),
]
