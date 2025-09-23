"""
URLs de la app 'monedas'.
- CRUD de Moneda
- Tablero de tasas (dashboard_tasas)
"""

from django.urls import path
from . import views

app_name = 'monedas'

urlpatterns = [
    path('', views.monedas_list, name='monedas_list'),
    path('nueva/', views.moneda_create, name='moneda_create'),
    path('editar/<int:moneda_id>/', views.moneda_edit, name='moneda_edit'),
    path('eliminar/<int:moneda_id>/', views.moneda_delete, name='moneda_delete'),
    path('inactivas/', views.monedas_inactivas, name='monedas_inactivas'),
]
