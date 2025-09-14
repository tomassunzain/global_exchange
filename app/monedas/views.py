from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect

from .forms import MonedaForm
from .models import Moneda


@login_required
def monedas_list(request):
    monedas = Moneda.objects.all().order_by('-por_defecto', 'codigo')
    return render(request, 'monedas/monedas_list.html', {'monedas': monedas})


@login_required
@transaction.atomic
def moneda_create(request):
    if request.method == 'POST':
        form = MonedaForm(request.POST)
        if form.is_valid():
            obj = form.save()
            # Si se marca por defecto, desmarcar las demás
            if obj.por_defecto:
                Moneda.objects.exclude(pk=obj.pk).update(por_defecto=False)
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
            if obj.por_defecto:
                Moneda.objects.exclude(pk=obj.pk).update(por_defecto=False)
            messages.success(request, 'Moneda actualizada.')
            return redirect('monedas:monedas_list')
    else:
        form = MonedaForm(instance=moneda)
    return render(request, 'monedas/moneda_form.html', {'form': form, 'moneda': moneda})


@login_required
def moneda_delete(request, moneda_id):
    moneda = get_object_or_404(Moneda, pk=moneda_id)
    if request.method == 'POST':
        if moneda.por_defecto:
            messages.error(request, 'No podés eliminar la moneda por defecto. Asigná otra primero.')
            return redirect('monedas:monedas_list')
        moneda.delete()
        messages.success(request, 'Moneda eliminada.')
        return redirect('monedas:monedas_list')
    return render(request, 'monedas/moneda_delete_confirm.html', {'moneda': moneda})
