from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from .services import confirmar_transaccion, cancelar_transaccion
from django.contrib import messages
from .forms import TransaccionForm
from .models import Transaccion
from .services import crear_transaccion

from commons.enums import EstadoTransaccionEnum, TipoTransaccionEnum, TipoMovimientoEnum

def transacciones_list(request):
    transacciones = Transaccion.objects.all().select_related("cliente", "moneda")
    return render(request, "transacciones/transacciones_list.html", {"transacciones": transacciones})

def confirmar_view(request, pk):
    transaccion = get_object_or_404(Transaccion, pk=pk)
    try:
        medio = transaccion.cliente.medioacreditacion_set.first()  # o elegir el medio correcto
        confirmar_transaccion(transaccion, medio)
        messages.success(request, f"Transacción {transaccion.id} confirmada correctamente.")
    except ValidationError as e:
        messages.error(request, str(e))
    return redirect("transacciones:transacciones_list")

def cancelar_view(request, pk):
    transaccion = get_object_or_404(Transaccion, pk=pk)
    try:
        cancelar_transaccion(transaccion)
        messages.success(request, f"Transacción {transaccion.id} cancelada.")
    except ValidationError as e:
        messages.error(request, str(e))
    return redirect("transacciones:transacciones_list")


def transaccion_create(request):
    if request.method == "POST":
        form = TransaccionForm(request.POST)
        if form.is_valid():
            cliente = form.cleaned_data["cliente"]
            tipo = form.cleaned_data["tipo"]
            moneda_operada = form.cleaned_data["moneda"]
            monto_operado = form.cleaned_data["monto_operado"]

            # TODO: calcular tasa, comisión y monto_pyg aquí (puedes delegar a un helper)
            tasa = 7390  # ej. hardcode, luego buscar en TasaCambio
            comision = 100
            monto_pyg = monto_operado * tasa + comision if tipo == "COMPRA" else monto_operado * tasa - comision

            transaccion = crear_transaccion(cliente, tipo, moneda_operada, monto_operado, tasa, comision, monto_pyg)
            messages.success(request, f"Transacción {transaccion.id} creada correctamente.")
            return redirect("transacciones:transacciones_list")
    else:
        form = TransaccionForm()

    return render(request, "transacciones/transaccion_form.html", {"form": form})
