from decimal import Decimal
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from .services import confirmar_transaccion, cancelar_transaccion
from django.contrib import messages
from .forms import TransaccionForm
from .models import Transaccion
from .services import crear_transaccion
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .services import calcular_transaccion
from clientes.models import Cliente
from monedas.models import Moneda

from commons.enums import EstadoTransaccionEnum, TipoTransaccionEnum, TipoMovimientoEnum

def transacciones_list(request):
    order = request.GET.get('order')
    dir = request.GET.get('dir')
    cliente_id = request.GET.get('cliente')
    transacciones = Transaccion.objects.all().select_related("cliente", "moneda")
    if cliente_id:
        transacciones = transacciones.filter(cliente_id=cliente_id)
    if order == 'fecha':
        if dir == 'asc':
            transacciones = transacciones.order_by('fecha')
        else:
            transacciones = transacciones.order_by('-fecha')
    clientes = Cliente.objects.all()
    return render(request, "transacciones/transacciones_list.html", {"transacciones": transacciones, "clientes": clientes, "cliente_id": cliente_id})

def confirmar_view(request, pk):
    transaccion = get_object_or_404(Transaccion, pk=pk)
    try:
        confirmar_transaccion(transaccion)
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
            medio_pago = form.cleaned_data["medio_pago"]

            from .services import calcular_transaccion
            try:
                calculo = calcular_transaccion(cliente, tipo, moneda_operada, monto_operado)
                transaccion = crear_transaccion(
                    cliente, tipo, moneda_operada, monto_operado,
                    calculo['tasa_aplicada'], calculo['comision'], calculo['monto_pyg'],
                    medio_pago
                )
                messages.success(request, f"Transacción {transaccion.id} creada correctamente.")
                return redirect("transacciones:transacciones_list")
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error en el cálculo: {e}")
        # Si hay error, vuelve a mostrar el formulario con mensajes
        return render(request, "transacciones/transaccion_form.html", {"form": form})
    else:
        form = TransaccionForm()

    return render(request, "transacciones/transaccion_form.html", {"form": form})



@csrf_exempt
def calcular_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            cliente = Cliente.objects.get(pk=int(data["cliente"]))
            tipo = data["tipo"]
            moneda = Moneda.objects.get(pk=int(data["moneda"]))
            monto = Decimal(str(data["monto_operado"]))

            calculo = calcular_transaccion(cliente, tipo, moneda, monto)
            return JsonResponse({
                "tasa_aplicada": str(calculo["tasa_aplicada"]),
                "comision": str(calculo["comision"]),
                "monto_pyg": str(calculo["monto_pyg"])
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)