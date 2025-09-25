from django.shortcuts import render, redirect
from decimal import Decimal
import os
import json
import requests
from django.conf import settings
from monedas.models import TasaCambio

def landing_page(request):
    # Si está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect('usuarios:dashboard')

    # Obtener las tasas activas del sistema (últimas por moneda)
    tasas_qs = (
        TasaCambio.objects.select_related('moneda')
        .filter(activa=True)
        .order_by('moneda__codigo')
    )
    tasas_obj = []
    for t in tasas_qs:
        tasas_obj.append({
            'moneda_codigo': t.moneda.codigo,
            'moneda_nombre': t.moneda.nombre,
            'compra': t.compra,
            'venta': t.venta,
            'variacion': t.variacion,
            'fuente': t.fuente,
            'fecha_creacion': t.fecha_creacion,
            'estado': 'Activa' if t.activa else 'Inactiva',
        })
    ultima_actualizacion_tasas = None
    if tasas_obj:
        ultima_actualizacion_tasas = max(t['fecha_creacion'] for t in tasas_obj)
    context = {
        'tasas': tasas_obj,
        'ultima_actualizacion_tasas': ultima_actualizacion_tasas
    }
    return render(request, "landing.html", context)
