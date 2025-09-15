from django.urls import path
from . import views

app_name = 'monedas'

urlpatterns = [
    path('', views.monedas_list, name='monedas_list'),
    path('nueva/', views.moneda_create, name='moneda_create'),
    path('<int:moneda_id>/editar/', views.moneda_edit, name='moneda_edit'),
    path('<int:moneda_id>/eliminar/', views.moneda_delete, name='moneda_delete'),
    path('dashboard/', views.tasa_cambio, name='dashboard_tasas'),

]
