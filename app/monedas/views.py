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
from .forms import MonedaForm
from .models import Moneda


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
