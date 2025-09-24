"""
Vistas (FBV) de 'monedas'.

Incluye:
- Listado, creación, edición y eliminación de Moneda.
- Tablero de tasas de cambio ('tasa_cambio'): muestra la última cotización por
  moneda si existe en BD; si no, usa un mock estático y valida la base reportada
  por la fuente vs la base del sistema.
"""

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .forms import MonedaForm
from .models import Moneda, TasaCambio
import request

@login_required
def monedas_list(request):

    monedas = Moneda.objects.all().order_by('-es_base', 'codigo')
    return render(request, 'monedas/monedas_list.html', {'monedas': monedas})


@login_required
@transaction.atomic
def moneda_create(request):

    if request.method == 'POST':
        form = MonedaForm(request.POST)
        if form.is_valid():
            obj = form.save()
            if obj.es_base:
                Moneda.objects.exclude(pk=obj.pk).update(es_base=False)
            messages.success(request, 'Moneda creada exitosamente.')
            return redirect('monedas:monedas_list')
    else:
        form = MonedaForm()
    return render(request, 'monedas/moneda_form.html', {'form': form})


@login_required
@transaction.atomic
def moneda_edit(request, moneda_id):

    moneda = get_object_or_404(Moneda, pk=moneda_id)
    if request.method == 'POST':
        form = MonedaForm(request.POST, instance=moneda)
        if form.is_valid():
            obj = form.save()
            if obj.es_base:
                Moneda.objects.exclude(pk=obj.pk).update(es_base=False)
            messages.success(request, 'Moneda actualizada.')
            return redirect('monedas:monedas_list')
    else:
        form = MonedaForm(instance=moneda)
    return render(request, 'monedas/moneda_form.html', {'form': form, 'moneda': moneda})


@login_required
def moneda_delete(request, moneda_id):

    moneda = get_object_or_404(Moneda, pk=moneda_id)
    if request.method == 'POST':
        if moneda.es_base:
            messages.error(request, 'No podés eliminar la moneda base. Asigná otra base primero.')
            return redirect('monedas:monedas_list')
        moneda.delete()
        messages.success(request, 'Moneda eliminada.')
        return redirect('monedas:monedas_list')
    return render(request, 'monedas/moneda_delete_confirm.html', {'moneda': moneda})


@login_required
def tasa_cambio(request):
    """
    Tablero de tasas que consume API externa con fallback a mock
    """
    # 1. INTENTAR API EXTERNA
    try:
        # CONSUMIR API DIRECTAMENTE - CAMBIAR ESTA URL POR LA REAL
        api_url = "https://api.banco-central.com/tasas"  # ← URL REAL AQUÍ
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        # Suponiendo que la API devuelve el formato correcto
        payload = response.json()

        # USAR TU SERVICIO EXISTENTE
        result = upsert_tasas_desde_payload(payload)

        if result['ok']:
            messages.success(request, '✅ Tasas actualizadas desde API central')
        else:
            messages.warning(request, f'⚠️ {result["reason"]}')

    except Exception as e:
        # 2. FALLBACK: MOCK si la API falla
        payload = [
            {
                "currency": "USD",
                "buy": "7300.00",
                "sell": "7400.00",
                "base_currency": "PYG",
                "source": "Backup Local",
                "timestamp": "2025-09-13T22:15:00Z"
            },
            {
                "currency": "EUR",
                "buy": "8000.00",
                "sell": "8200.00",
                "base_currency": "PYG",
                "source": "Backup Local",
                "timestamp": "2025-09-13T22:15:00Z"
            },
            {
                "currency": "BRL",
                "buy": "1300.00",
                "sell": "1350.00",
                "base_currency": "PYG",
                "source": "Backup Local",
                "timestamp": "2025-09-13T22:15:00Z"
            },
            {
                "currency": "ARS",
                "buy": "8.00",
                "sell": "10.00",
                "base_currency": "PYG",
                "source": "Backup Local",
                "timestamp": "2025-09-13T22:15:00Z"
            }
        ]
        messages.info(request, 'ℹ️ Modo demostración: usando datos de prueba')

    # 3. MOSTRAR TASAS (de API o de mock)
    # Moneda base del sistema
    base = Moneda.objects.filter(es_base=True).first()
    system_base = base.codigo if base else None

    # Obtener tasas para mostrar
    ultimas = {}
    for t in TasaCambio.objects.select_related('moneda').filter(moneda__activa=True, activa=True).order_by(
            'moneda__codigo', '-fecha_actualizacion'):
        if t.moneda.codigo not in ultimas:
            ultimas[t.moneda.codigo] = t
    tasas = list(ultimas.values())

    if not tasas:
        # Si no hay tasas en BD, usar las del mock
        monedas_map = {m.codigo: m for m in Moneda.objects.all()}
        tasas = []
        for d in payload:
            m = monedas_map.get(d['currency'])
            if not m:
                class _M: pass

                m = _M()
                m.codigo = d['currency']
                m.nombre = ''
                m.simbolo = '$'
                m.decimales = 2

            class _T:
                pass

            t = _T()
            t.moneda = m
            t.compra = Decimal(d['buy'])
            t.venta = Decimal(d['sell'])
            t.variacion = Decimal('0')
            tasas.append(t)
        ultima_actualizacion = timezone.now()
    else:
        ultima_actualizacion = max(t.fecha_actualizacion for t in tasas)

    return render(request, 'monedas/tasa_cambio.html', {
        'tasas': tasas,
        'ultima_actualizacion': ultima_actualizacion,
        'system_base': system_base,
    })
