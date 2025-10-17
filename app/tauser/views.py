from django.shortcuts import render
from django.contrib import messages
from transaccion.models import Transaccion
from transaccion.services import confirmar_transaccion, cancelar_transaccion
from monedas.models import TasaCambio
from commons.enums import EstadoTransaccionEnum
from django.utils import timezone


from django.shortcuts import render
from django.contrib import messages
from transaccion.models import Transaccion
from transaccion.services import confirmar_transaccion, cancelar_transaccion, calcular_transaccion
from monedas.models import TasaCambio
from commons.enums import EstadoTransaccionEnum
from django.utils import timezone

def tramitar_transacciones(request):
    datos_transaccion = None
    error = None
    mensaje = None
    transaccion_uuid = request.POST.get("transaccion_uuid", "").strip()

    if request.method == "POST":
        accion = request.POST.get("accion", "buscar")

        if not transaccion_uuid:
            error = "Debe ingresar el código de transacción."
        else:
            try:
                tx = Transaccion.objects.select_related("moneda", "cliente").get(uuid=transaccion_uuid)
            except Transaccion.DoesNotExist:
                tx = None
                error = "No se encontró ninguna transacción con ese código."

            if tx:
                # Buscar tasa actual
                tasa_actual = (
                    TasaCambio.objects.filter(moneda=tx.moneda, activa=True)
                    .latest("fecha_creacion")
                    .compra
                )

                if accion == "buscar":
                    datos_transaccion = {
                        "uuid": tx.uuid,
                        "id": tx.id,
                        "cliente": tx.cliente,
                        "tipo": tx.get_tipo_display(),
                        "moneda": tx.moneda,
                        "tasa": tx.tasa_aplicada,
                        "tasa_recalculada": tasa_actual,
                        "monto_operado": tx.monto_operado,
                        "monto_pyg": tx.monto_pyg,
                        "fecha": tx.fecha.astimezone(timezone.get_current_timezone()),
                        "estado": tx.estado,
                    }

                elif accion == "recalcular":
                    try:
                        # recalcular usando la tasa nueva
                        recalculo = calcular_transaccion(tx.cliente, tx.tipo, tx.moneda, tx.monto_operado)
                        tx.tasa_aplicada = recalculo["tasa_aplicada"]
                        tx.monto_pyg = recalculo["monto_pyg"]
                        tx.save(update_fields=["tasa_aplicada", "monto_pyg"])
                        mensaje = "Transacción recalculada con la nueva tasa."
                        datos_transaccion = {
                            "uuid": tx.uuid,
                            "id": tx.id,
                            "cliente": tx.cliente,
                            "tipo": tx.get_tipo_display(),
                            "moneda": tx.moneda,
                            "tasa": tx.tasa_aplicada,
                            "tasa_recalculada": tx.tasa_aplicada,
                            "monto_operado": tx.monto_operado,
                            "monto_pyg": tx.monto_pyg,
                            "fecha": tx.fecha,
                            "estado": tx.estado,
                        }
                    except Exception as e:
                        error = f"No se pudo recalcular: {e}"

                elif accion == "confirmar":
                    try:
                        confirmar_transaccion(tx)
                        mensaje = f"Transacción #{tx.id} confirmada correctamente."
                    except Exception as e:
                        error = str(e)

                elif accion == "cancelar":
                    try:
                        cancelar_transaccion(tx)
                        mensaje = f"Transacción #{tx.id} cancelada correctamente."
                    except Exception as e:
                        error = str(e)

    return render(request, "tauser/tramitar_transacciones.html", {
        "datos_transaccion": datos_transaccion,
        "error": error,
        "mensaje": mensaje,
        "transaccion_uuid": transaccion_uuid,
    })


def nuevo_tauser(request):
    return render(request, 'tauser/nuevo_tauser.html')


def lista_tausers(request):
    return render(request, 'tauser/lista_tausers.html')
