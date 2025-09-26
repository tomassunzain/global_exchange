from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.db import transaction as dj_tx
from django.utils import timezone


from decimal import Decimal
from clientes.models import LimitePYG, LimiteMoneda, TasaComision
from transaccion.models import Transaccion, Movimiento
from commons.enums import EstadoTransaccionEnum, TipoTransaccionEnum, TipoMovimientoEnum
from monedas.models import TasaCambio
import json
import os
from django.conf import settings

def calcular_transaccion(cliente, tipo, moneda, monto_operado):
    """
    Calcula tasa, comisión y monto_pyg según la lógica del simulador_complejo.js
    """
    # 1. Segmento del cliente
    segmento = cliente.tipo.upper() if hasattr(cliente, 'tipo') else 'MIN'

    # 2. Buscar tasa de cambio activa para la moneda
    try:
        tasa = TasaCambio.objects.filter(moneda=moneda, activa=True).latest('fecha_creacion')
    except TasaCambio.DoesNotExist:
        raise ValidationError(f"No hay tasa de cambio activa para {moneda}.")

    # 3. Leer comisiones desde el archivo json (mock)
    comisiones_path = os.path.join(settings.BASE_DIR, 'static', 'comisiones.json')
    try:
        with open(comisiones_path, 'r', encoding='utf-8') as f:
            comisiones = json.load(f)
    except Exception:
        comisiones = []

    com = next((c for c in comisiones if c['currency'] == moneda.codigo), None)
    comision_buy = Decimal(str(com['commission_buy'])) if com else Decimal('0')
    comision_sell = Decimal(str(com['commission_sell'])) if com else Decimal('0')

    # 4. Descuento por segmento
    tc = TasaComision.vigente_para_tipo(segmento)
    descuento = Decimal(str(tc.porcentaje)) if tc else Decimal('0')
    
    # 5. Cálculo según tipo
    monto_operado = Decimal(monto_operado)
    pb = tasa.compra + comision_buy
    if tipo == TipoTransaccionEnum.COMPRA:
        # COMPRA: de moneda extranjera a PYG
        tc_compra = pb - (comision_buy - (comision_buy * descuento / 100))
        tasa_aplicada = tc_compra
        comision = comision_buy
        monto_pyg = monto_operado * tc_compra
    elif tipo == TipoTransaccionEnum.VENTA:
        # VENTA: de PYG a moneda extranjera
        tc_venta = pb + comision_sell - (comision_sell * descuento / 100)
        tasa_aplicada = tc_venta
        comision = comision_sell
        monto_pyg = monto_operado / tc_venta
    else:
        raise ValidationError("Tipo de transacción inválido.")

    return {
        'tasa_aplicada': tasa_aplicada,
        'comision': comision,
        'monto_pyg': monto_pyg,
    }

def crear_transaccion(cliente, tipo, moneda, monto_operado, tasa_aplicada, comision, monto_pyg, medio_pago=None):
    """
    Cliente inicia una operación (COMPRA o VENTA).
    Se crea en estado PENDIENTE. No hay movimiento todavía.
    """
    validate_limits(cliente, moneda, monto_operado, monto_pyg)
    
    with dj_tx.atomic():
        t = Transaccion.objects.create(
            cliente=cliente,
            moneda=moneda,
            tipo=tipo,
            monto_operado=monto_operado,
            monto_pyg=monto_pyg,
            tasa_aplicada=tasa_aplicada,
            comision=comision,
            medio_pago=medio_pago,
            estado=EstadoTransaccionEnum.PENDIENTE,
        )
    return t


def confirmar_transaccion(transaccion):
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
            tipo=mov_tipo,
            monto=transaccion.monto_pyg,
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
