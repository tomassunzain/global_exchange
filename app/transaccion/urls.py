from django.urls import path
from . import views

app_name = "transacciones"

urlpatterns = [
    path("", views.transacciones_list, name="transacciones_list"),
    path("nueva/", views.transaccion_create, name="transaccion_create"),
    path("<int:pk>/confirmar/", views.confirmar_view, name="confirmar"),
    path("<int:pk>/cancelar/", views.cancelar_view, name="cancelar"),
    path("calcular/", views.calcular_api, name="calcular_api"),
]
