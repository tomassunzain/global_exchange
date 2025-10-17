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
from mfa.services import generate_otp, verify_otp
from django.urls import reverse
from django.contrib.auth.decorators import login_required

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


@login_required
def transaccion_create(request):
    if request.method == "POST":
        form = TransaccionForm(request.POST)
        if form.is_valid():
            cliente = form.cleaned_data["cliente"]
            tipo = form.cleaned_data["tipo"]
            moneda_operada = form.cleaned_data["moneda"]
            monto_operado = form.cleaned_data["monto_operado"]
            medio_pago = form.cleaned_data["medio_pago"]
            email_mfa = form.cleaned_data.get("email_mfa")

            try:
                calculo = calcular_transaccion(cliente, tipo, moneda_operada, monto_operado)
                
                # Si es COMPRA (débito), iniciar flujo MFA en lugar de crear la transacción directamente
                if tipo == TipoTransaccionEnum.COMPRA:
                    # Guardar datos de la transacción pendiente en la sesión
                    request.session['pending_transaction'] = {
                        'cliente_id': cliente.pk,
                        'tipo': tipo,
                        'moneda_id': moneda_operada.pk,
                        'monto_operado': str(monto_operado),
                        'tasa_aplicada': str(calculo['tasa_aplicada']),
                        'comision': str(calculo['comision']),
                        'monto_pyg': str(calculo['monto_pyg']),
                        'medio_pago_id': medio_pago.pk if medio_pago else None,
                        'email_mfa': email_mfa,
                    }

                    # Generar OTP forzando el método de email
                    generate_otp(
                        user=request.user,
                        purpose='transaction_debit',
                        force_method='email',
                        override_destination=email_mfa,
                        context={'cliente_id': cliente.pk, 'monto': str(calculo['monto_pyg'])}
                    )
                    
                    messages.info(request, f"Se ha enviado un código de verificación a {email_mfa} para confirmar la transacción.")
                    return redirect('transacciones:verify_transaction_otp')

                # Para VENTAS (crédito), el flujo sigue como antes
                else:
                    transaccion = crear_transaccion(
                        cliente, tipo, moneda_operada, monto_operado,
                        calculo['tasa_aplicada'], calculo['comision'], calculo['monto_pyg'],
                        medio_pago
                    )
                    messages.success(request, f"Transacción de venta {transaccion.id} creada correctamente.")
                    return redirect("transacciones:transacciones_list")

            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error inesperado: {e}")

        # Si hay error en el form, vuelve a mostrar el formulario con mensajes
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

@login_required
def verify_transaction_otp(request):
    """
    Maneja la verificación del OTP para una transacción de débito pendiente.
    """
    pending_tx = request.session.get('pending_transaction')
    if not pending_tx:
        messages.error(request, "No hay ninguna transacción pendiente para verificar.")
        return redirect('transacciones:transaccion_create')

    if request.method == 'POST':
        action = request.POST.get('action', 'verify')
        
        if action == 'resend':
            try:
                generate_otp(
                    user=request.user,
                    purpose='transaction_debit',
                    force_method='email',
                    override_destination=pending_tx['email_mfa'],
                    context={'cliente_id': pending_tx['cliente_id'], 'monto': pending_tx['monto_pyg']}
                )
                messages.success(request, f"Se ha reenviado un nuevo código a {pending_tx['email_mfa']}.")
            except ValidationError as e:
                messages.error(request, str(e))
            return render(request, 'transacciones/verify_otp.html')

        # Por defecto, la acción es 'verify'
        otp_code = request.POST.get('otp_code')
        if not otp_code:
            messages.error(request, "Por favor, ingresa el código de verificación.")
            return render(request, 'transacciones/verify_otp.html')

        try:
            # Verificar el OTP
            is_valid, _ = verify_otp(
                user=request.user,
                purpose='transaction_debit',
                raw_code=otp_code,
                context_match={'cliente_id': pending_tx['cliente_id'], 'monto': pending_tx['monto_pyg']}
            )

            if is_valid:
                # Si el OTP es válido, crear la transacción real
                cliente = Cliente.objects.get(pk=pending_tx['cliente_id'])
                moneda = Moneda.objects.get(pk=pending_tx['moneda_id'])
                medio_pago = None
                if pending_tx.get('medio_pago_id'):
                    from payments.models import PaymentMethod
                    medio_pago = PaymentMethod.objects.get(pk=pending_tx['medio_pago_id'])

                transaccion = crear_transaccion(
                    cliente=cliente,
                    tipo=pending_tx['tipo'],
                    moneda=moneda,
                    monto_operado=Decimal(pending_tx['monto_operado']),
                    tasa_aplicada=Decimal(pending_tx['tasa_aplicada']),
                    comision=Decimal(pending_tx['comision']),
                    monto_pyg=Decimal(pending_tx['monto_pyg']),
                    medio_pago=medio_pago
                )
                
                # Limpiar la sesión
                del request.session['pending_transaction']
                
                messages.success(request, f"Transacción {transaccion.id} creada y confirmada exitosamente.")
                # Aquí es donde se redirigiría al checkout final
                # return redirect(f'/create-checkout-session/{transaccion.id}')
                return redirect('transacciones:transacciones_list')

        except ValidationError as e:
            messages.error(request, str(e))

    return render(request, 'transacciones/verify_otp.html')