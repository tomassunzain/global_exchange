"""
Vistas (FBV) de la app 'payments'.

Gestionan los métodos de pago asociados a clientes:
- Listado de métodos de pago por cliente.
- Creación de un nuevo método de pago.
- Actualización de un método de pago existente.
- Eliminación de un método de pago existente.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import PaymentMethod
from .forms import PaymentMethodForm
from clientes.models import Cliente
from commons.enums import EstadoRegistroEnum

def payment_methods_by_client(request):
    """
    Muestra un listado de clientes asociados al usuario actual,
    junto con sus métodos de pago activos.

    - Filtra clientes activos que pertenecen al usuario.
    - Renderiza la plantilla 'payment_methods_by_client.html' con la lista de clientes.
    """
    clientes = Cliente.objects.filter(usuarios=request.user, estado=EstadoRegistroEnum.ACTIVO.value)
    return render(request, 'payments/payment_methods_by_client.html', {'clientes': clientes})


def payment_method_delete(request, pk):
    """
    Elimina un método de pago existente identificado por su PK.

    - Si el método se elimina con POST, muestra un mensaje de éxito
      y redirige al listado de métodos de pago por cliente.
    - Si se accede con GET, muestra la página de confirmación de eliminación.
    """
    method = get_object_or_404(PaymentMethod, pk=pk)
    if request.method == 'POST':
        method.delete()
        messages.success(request, 'Método de pago eliminado exitosamente.')
        return redirect('payments:payment_methods_by_client')
    return render(request, 'payments/paymentmethod_confirm_delete.html', {'method': method})


def payment_method_create(request):
    """
    Crea un nuevo método de pago para un cliente específico.

    - Obtiene el ID del cliente desde GET o POST.
    - Verifica que el cliente exista y pertenezca al usuario actual.
    - Valida el formulario PaymentMethodForm.
    - Asocia el método de pago al cliente y lo guarda.
    - Muestra mensajes de éxito o renderiza la plantilla del formulario.
    """
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
        form = PaymentMethodForm(request.POST)
        if form.is_valid() and cliente:
            metodo = form.save(commit=False)
            metodo.cliente = cliente
            metodo.save()
            messages.success(request, 'Método de pago creado exitosamente.')
            return redirect('payments:payment_methods_by_client')
    else:
        form = PaymentMethodForm()
    return render(request, 'payments/paymentmethod_form.html', {'form': form, 'cliente': cliente})


def payment_method_update(request, pk):
    """
    Actualiza un método de pago existente identificado por su PK.

    - Obtiene el método de pago y el cliente asociado.
    - Valida el formulario PaymentMethodForm con la instancia existente.
    - Guarda los cambios si el formulario es válido.
    - Muestra mensajes de éxito y redirige al listado de métodos de pago.
    - Renderiza la plantilla del formulario si se accede vía GET o el formulario no es válido.
    """
    method = get_object_or_404(PaymentMethod, pk=pk)
    cliente = method.cliente
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST, instance=method)
        if form.is_valid():
            form.save()
            messages.success(request, 'Método de pago actualizado exitosamente.')
            return redirect('payments:payment_methods_by_client')
    else:
        form = PaymentMethodForm(instance=method)
    return render(request, 'payments/paymentmethod_form.html', {'form': form, 'method': method, 'cliente': cliente})
