from django.urls import path
from . import views

app_name = 'tauser'

urlpatterns = [
    path('tramitar-transacciones/', views.tramitar_transacciones, name='tramitar_transacciones'),
    path('nuevo/', views.nuevo_tauser, name='nuevo_tauser'),
    path('lista/', views.lista_tausers, name='lista_tausers'),
]