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
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from .forms import MonedaForm, TasaCambioForm
from .models import Moneda, TasaCambio
from clientes.models import TasaComision
from usuarios.decorators import role_required
from django.http import JsonResponse
from django.core import serializers

# --- API para lista de cotizaciones (tasas de cambio) ---

def cotizaciones_json(request):
    from .models import TasaCambio
    try:
        cotizaciones = TasaCambio.objects.select_related('moneda').order_by('-fecha_creacion')
        data = []
        for tasa in cotizaciones:
            data.append({
                'id': tasa.id,
                'moneda': tasa.moneda.codigo if tasa.moneda else None,
                'base': getattr(tasa, 'base_codigo', 'PYG'),
                'compra': float(tasa.compra) if tasa.compra else None,
                'venta': float(tasa.venta) if tasa.venta else None,
                'fecha': tasa.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if tasa.fecha_creacion else None,
                'fuente': tasa.fuente,
            })
        return JsonResponse({'cotizaciones': data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# --- API para tasas de descuento por tipo de cliente ---
@login_required
def tasas_comisiones_json(request):
    """
    Devuelve las tasas de descuento vigentes por tipo de cliente en formato JSON.
    """
    tipos = ["MIN", "CORP", "VIP"]
    tasas = {}
    for tipo in tipos:
        tc = TasaComision.vigente_para_tipo(tipo)
        tasas[tipo.lower()] = {
            "tasa_descuento": float(tc.porcentaje) if tc else 0
        }
    return JsonResponse({"tasas": tasas})

@login_required
def monedas_list(request):
    # Mostrar solo monedas activas usando el manager personalizado
    monedas = Moneda.objects.all().order_by('-es_base', 'codigo')
    return render(request, 'monedas/monedas_list.html', {'monedas': monedas})


@login_required
@transaction.atomic
def moneda_create(request):
    if request.method == 'POST':
        form = MonedaForm(request.POST)
        if form.is_valid():
            try:
                obj = form.save()
                messages.success(request, 'Moneda creada exitosamente.')
                return redirect('monedas:monedas_list')
            except Exception as e:
                messages.error(request, f'Error al crear la moneda: {str(e)}')
    else:
        form = MonedaForm()
    return render(request, 'monedas/moneda_form.html', {'form': form})


@login_required
@transaction.atomic
def moneda_edit(request, moneda_id):
    # Usar all_with_inactive para permitir editar monedas inactivas
    moneda = get_object_or_404(Moneda.objects.all_with_inactive(), pk=moneda_id)

    if request.method == 'POST':
        form = MonedaForm(request.POST, instance=moneda)
        if form.is_valid():
            try:
                obj = form.save()
                messages.success(request, 'Moneda actualizada.')
                return redirect('monedas:monedas_list')
            except Exception as e:
                messages.error(request, f'Error al actualizar la moneda: {str(e)}')
    else:
        form = MonedaForm(instance=moneda)
    return render(request, 'monedas/moneda_form.html', {'form': form, 'moneda': moneda})


@login_required
def moneda_delete(request, moneda_id):
    # Usar all_with_inactive para permitir "eliminar" monedas ya inactivas
    moneda = get_object_or_404(Moneda.objects.all_with_inactive(), pk=moneda_id)

    if request.method == 'POST':
        if moneda.codigo == 'PYG':
            messages.error(request, 'No podés eliminar la moneda base PYG.')
            return redirect('monedas:monedas_list')

        # Soft delete
        moneda.delete(soft_delete=True)
        messages.success(request, 'Moneda desactivada (eliminación lógica).')
        return redirect('monedas:monedas_list')

    return render(request, 'monedas/moneda_delete_confirm.html', {'moneda': moneda})


@login_required
def monedas_inactivas(request):
    """Vista para ver y reactivar monedas inactivas"""
    monedas_inactivas = Moneda.objects.all_with_inactive().filter(activa=False).order_by('codigo')

    if request.method == 'POST':
        moneda_id = request.POST.get('moneda_id')
        accion = request.POST.get('accion')

        if moneda_id and accion == 'reactivar':
            moneda = get_object_or_404(Moneda.objects.all_with_inactive(), pk=moneda_id)
            moneda.activa = True
            moneda.save()
            messages.success(request, f'Moneda {moneda.codigo} reactivada.')
            return redirect('monedas:monedas_list')

    return render(request, 'monedas/monedas_inactivas.html', {'monedas': monedas_inactivas})


@login_required
def tasas_list(request):
    """Listado con filtro por moneda y por estado (activa/todas)."""
    moneda_id = request.GET.get('moneda')
    solo_activas = request.GET.get('solo_activas') == '1'

    qs = TasaCambio.objects.select_related('moneda').all().order_by('-fecha_creacion')
    if moneda_id:
        qs = qs.filter(moneda_id=moneda_id)
    if solo_activas:
        qs = qs.filter(activa=True)

    monedas = Moneda.objects.all().filter(activa=True, es_base=False).order_by('codigo')
    ctx = {
        'tasas': qs,
        'monedas': monedas,
        'moneda_id': moneda_id or '',
        'solo_activas': solo_activas,
    }
    return render(request, 'monedas/tasas_list.html', ctx)


@login_required
@transaction.atomic
def tasa_create(request):
    form = TasaCambioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            # Crear instancia y forzar activa=True
            tasa = form.save(commit=False)
            tasa.es_automatica = False
            tasa.activa = True  # ✅ Siempre activa al crear

            tasa.save()  # ✅ El save() del modelo manejará la desactivación de otras

            messages.success(request, 'Tasa de cambio creada correctamente.')
            return redirect('monedas:tasas_list')

        except Exception as e:
            messages.error(request, f'No se pudo crear la tasa: {e}')
    return render(request, 'monedas/tasa_form.html', {'form': form})


@login_required
@transaction.atomic
def tasa_edit(request, tasa_id):
    tasa = get_object_or_404(TasaCambio, pk=tasa_id)
    if request.method == 'POST':
        form = TasaCambioForm(request.POST, instance=tasa)
        if form.is_valid():
            try:
                # Al editar, mantener el estado activo actual
                tasa = form.save(commit=False)
                tasa.save()  # ✅ El save() del modelo mantiene la lógica de activación

                messages.success(request, 'Tasa de cambio actualizada.')
                return redirect('monedas:tasas_list')
            except Exception as e:
                messages.error(request, f'No se pudo actualizar la tasa: {e}')
    else:
        form = TasaCambioForm(instance=tasa)
    return render(request, 'monedas/tasa_form.html', {'form': form, 'tasa': tasa})


@login_required
@transaction.atomic
def tasa_delete(request, tasa_id):
    tasa = get_object_or_404(TasaCambio, pk=tasa_id)
    if request.method == 'POST':
        tasa.delete()
        messages.success(request, 'Tasa de cambio eliminada.')
        return redirect('monedas:tasas_list')
    return render(request, 'monedas/tasa_delete_confirm.html', {'tasa': tasa})


@login_required
@transaction.atomic
def tasa_marcar_activa(request, tasa_id):
    """Acción rápida para activar una tasa y desactivar las demás de la misma moneda."""
    tasa = get_object_or_404(TasaCambio, pk=tasa_id)
    tasa.activa = True
    tasa.save()  # el save del modelo desactiva las demás
    messages.success(request, f'Tasa {tasa.id} marcada como activa para {tasa.moneda.codigo}.')
    return redirect('monedas:tasas_list')
