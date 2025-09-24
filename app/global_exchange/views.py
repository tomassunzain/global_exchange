
from django.shortcuts import render, redirect
from decimal import Decimal
import os
import json
import requests
from django.conf import settings

def landing_page(request):
    # Si está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect('usuarios:dashboard')
    #cambiar entre api o local
    source = request.GET.get('source', 'local')
    tasas = []
    if source == 'api':
        try:
            url = "http://localhost:9000/api/rates/latest"  
            response = requests.get(url)
            response.raise_for_status()
            tasas = response.json()
        except Exception as e:
            tasas = []
    else:
        json_path = os.path.join(settings.BASE_DIR, 'exchange', 'mock_data', 'mock_exchange_rates.json')
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                tasas = json.load(f)
        except Exception as e:
            tasas = []

    tasas_obj = []
    for d in tasas:
        class MonedaSimple:
            pass
        m = MonedaSimple()
        m.codigo = d.get('currency', '')
        m.nombre = d.get('currency', '')
        m.simbolo = d.get('currency', '')
        m.decimales = 2
        class TasaSimple:
            pass
        t = TasaSimple()
        t.moneda = m
        t.compra = Decimal(d.get('buy', '0'))
        t.venta = Decimal(d.get('sell', '0'))
        t.variacion = Decimal('0')
        tasas_obj.append(t)
    ultima_actualizacion_tasas = None
    if tasas:
        ultima_actualizacion_tasas = max(d.get('timestamp', '') for d in tasas if d.get('timestamp'))
    context = {
        'tasas': tasas_obj,
        'ultima_actualizacion_tasas': ultima_actualizacion_tasas
    }
    return render(request, "landing.html", context)
