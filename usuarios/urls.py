from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('verificar/<uidb64>/<token>/', views.verificar_email, name='verificar'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # roles
    path('roles/', views.roles_list, name='roles_list'),
    path('roles/<int:group_id>/editar/', views.rol_editar, name='rol_editar'),
    path('usuarios/<int:user_id>/asignar-rol/', views.asignar_rol_a_usuario, name='asignar_rol'),
    path('', views.dashboard_view, name='dashboard'),

]

