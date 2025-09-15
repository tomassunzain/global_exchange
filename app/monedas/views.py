from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect

from .forms import MonedaForm
from .models import Moneda

@login_required
def monedas_list(request):
    """
    Vista que muestra la lista de todas las monedas ordenadas por si son base y su código.
    """
    monedas = Moneda.objects.all().order_by('-es_base', 'codigo')
    return render(request, 'monedas/monedas_list.html', {'monedas': monedas})

@login_required
@transaction.atomic
def moneda_create(request):
    """
    Vista para crear una nueva moneda. Si la moneda es base, actualiza las demás monedas para que no lo sean.
    """
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
    """
    Vista para editar una moneda existente. Si la moneda es base, actualiza las demás monedas para que no lo sean.
    """
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
    """
    Vista para eliminar una moneda. No permite eliminar la moneda base.
    """
    moneda = get_object_or_404(Moneda, pk=moneda_id)
    if request.method == 'POST':
        if moneda.es_base:
            messages.error(request, 'No podés eliminar la moneda base. Asigná otra base primero.')
            return redirect('monedas:monedas_list')
        moneda.delete()
        messages.success(request, 'Moneda eliminada.')
        return redirect('monedas:monedas_list')
    return render(request, 'monedas/moneda_delete_confirm.html', {'moneda': moneda})
