from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from .models import MedioAcreditacion
from .forms import MedioAcreditacionForm
from clientes.models import Cliente
from commons.enums import EstadoRegistroEnum

def medios_by_client(request):
    clientes = Cliente.objects.filter(usuarios=request.user, estado=EstadoRegistroEnum.ACTIVO.value)
    return render(request, 'medios_acreditacion/medios_by_client.html', {'clientes': clientes})

def medioacreditacion_delete(request, pk):
    medio = get_object_or_404(MedioAcreditacion, pk=pk)
    if request.method == 'POST':
        medio.delete()
        messages.success(request, 'Medio de acreditación eliminado exitosamente.')
        return redirect('medios_acreditacion:medios_by_client')
    return render(request, 'medios_acreditacion/medioacreditacion_confirm_delete.html', {'medio': medio})

def medioacreditacion_create(request):
    cliente_id = request.GET.get('cliente')
    if request.method == 'POST' and not cliente_id:
        cliente_id = request.POST.get('cliente_id')
    cliente = None
    if cliente_id:
        try:
            cliente = Cliente.objects.get(pk=cliente_id, usuarios=request.user)
        except Cliente.DoesNotExist:
            cliente = None
    if request.method == 'POST':
        form = MedioAcreditacionForm(request.POST)
        if form.is_valid() and cliente:
            medio = form.save(commit=False)
            medio.cliente = cliente
            medio.save()
            messages.success(request, 'Medio de acreditación creado exitosamente.')
            return redirect('medios_acreditacion:medios_by_client')
    else:
        form = MedioAcreditacionForm()
    return render(request, 'medios_acreditacion/medioacreditacion_form.html', {'form': form, 'cliente': cliente})

def medioacreditacion_update(request, pk):
    medio = get_object_or_404(MedioAcreditacion, pk=pk)
    cliente = medio.cliente
    if request.method == 'POST':
        form = MedioAcreditacionForm(request.POST, instance=medio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medio de acreditación actualizado exitosamente.')
            return redirect('medios_acreditacion:medios_by_client')
    else:
        form = MedioAcreditacionForm(instance=medio)
    return render(request, 'medios_acreditacion/medioacreditacion_form.html', {'form': form, 'medio': medio, 'cliente': cliente})
