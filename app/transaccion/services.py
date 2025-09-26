from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.db import transaction as dj_tx
from django.utils import timezone

from clientes.models import LimitePYG, LimiteMoneda
from transaccion.models import Transaccion, Movimiento
from commons.enums import EstadoTransaccionEnum, TipoTransaccionEnum, TipoMovimientoEnum

def crear_transaccion(cliente, tipo, moneda, monto_operado, tasa_aplicada, comision, monto_pyg):
    """
    Cliente inicia una operación (COMPRA o VENTA).
    Se crea en estado PENDIENTE. No hay movimiento todavía.
    """
    with dj_tx.atomic():
        t = Transaccion.objects.create(
            cliente=cliente,
            moneda=moneda,
            tipo=tipo,
            monto_operado=monto_operado,
            monto_pyg=monto_pyg,
            tasa_aplicada=tasa_aplicada,
            comision=comision,
        )
    return t


def confirmar_transaccion(transaccion, medio):
    """
    La casa de cambio confirma que el pago se recibió (PYG o divisa entregada).
    Esto crea el movimiento en PYG y marca la transacción como PAGADA.
    """
    if transaccion.estado != EstadoTransaccionEnum.PENDIENTE:
        raise ValidationError("Solo transacciones pendientes pueden confirmarse.")

    with dj_tx.atomic():
        transaccion.estado = EstadoTransaccionEnum.PAGADA
        transaccion.save(update_fields=["estado"])

        mov_tipo = TipoMovimientoEnum.DEBITO if transaccion.tipo == TipoTransaccionEnum.COMPRA else TipoMovimientoEnum.CREDITO

        Movimiento.objects.create(
            transaccion=transaccion,
            cliente=transaccion.cliente,
            medio=medio,
            tipo=mov_tipo,
            monto_pyg=transaccion.monto_pyg,
        )

    return transaccion

def cancelar_transaccion(transaccion):
    """
    Cancela una transacción pendiente (antes del pago).
    """
    if transaccion.estado != EstadoTransaccionEnum.PENDIENTE:
        raise ValidationError("Solo transacciones pendientes pueden cancelarse.")

    transaccion.estado = EstadoTransaccionEnum.CANCELADA
    transaccion.save(update_fields=["estado"])
    return transaccion

def _check_limit_pyg(cliente, monto_pyg):
    """
    Límite por operación en PYG.
    """
    try:
        lim = LimitePYG.objects.get(cliente=cliente)
    except LimitePYG.DoesNotExist:
        return  # sin límite configurado => permitir

    if monto_pyg > lim.max_por_operacion:
        raise ValidationError(
            f"Operación en PYG ({monto_pyg}) excede el límite por operación ({lim.max_por_operacion})."
        )


def _sum_operado_en_periodo(cliente, moneda, desde):
    return (
        Transaccion.objects.filter(
            cliente=cliente,
            moneda_operada=moneda,
            fecha__gte=desde,
            estado__in=[EstadoTransaccionEnum.PENDIENTE, EstadoTransaccionEnum.PAGADA],
        ).aggregate(total=Sum("monto_operado"))["total"]
        or 0
    )


def _check_limit_moneda(cliente, moneda, monto_operado):
    """
    Límite por operación en la MONEDA extranjera.
    Adicional: valida diario/mensual si están configurados.
    """
    try:
        lim = LimiteMoneda.objects.get(cliente=cliente, moneda=moneda)
    except LimiteMoneda.DoesNotExist:
        return

    if monto_operado > lim.max_por_operacion:
        raise ValidationError(
            f"Operación {monto_operado} {moneda} excede el límite por operación ({lim.max_por_operacion} {moneda})."
        )

    if lim.max_mensual:
        now = timezone.now().astimezone(timezone.get_current_timezone())
        inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total_mes = _sum_operado_en_periodo(cliente, moneda, inicio_mes)
        if total_mes + monto_operado > lim.max_mensual:
            raise ValidationError(
                f"Límite mensual en {moneda} excedido: mes {total_mes} + {monto_operado} > {lim.max_mensual}."
            )


def validate_limits(cliente, moneda_operada, monto_operado, monto_pyg):
    """
    Se llama ANTES de crear la transacción/movimientos.
    Aplica DOS validaciones:
      1) PYG por operación
      2) Moneda extranjera (por operación + opcional diario/mensual)
    """
    _check_limit_pyg(cliente, monto_pyg)
    _check_limit_moneda(cliente, moneda_operada, monto_operado)
