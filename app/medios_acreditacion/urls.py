from django.urls import path

from . import views

app_name = 'medios_acreditacion'

urlpatterns = [
    path('medios/', views.medios_by_client, name='medios_by_client'),
    path('medios/create/', views.medioacreditacion_create, name='medioacreditacion_create'),
    path('medios/<int:pk>/edit/', views.medioacreditacion_update, name='medioacreditacion_update'),
    path('medios/<int:pk>/delete/', views.medioacreditacion_delete, name='medioacreditacion_delete'),
]
