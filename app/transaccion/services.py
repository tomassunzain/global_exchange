import logging
import json
import os
from decimal import Decimal, ROUND_DOWN

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction as dj_tx
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from clientes.models import LimitePYG, LimiteMoneda, TasaComision
from monedas.models import TasaCambio
from .models import Transaccion, Movimiento
from commons.enums import EstadoTransaccionEnum, TipoTransaccionEnum, TipoMovimientoEnum

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


# =========================
# Cálculo de transacción
# =========================
def calcular_transaccion(cliente, tipo, moneda, monto_operado):
    """
    Calcula tasa, comisión y monto_pyg.
    """
    # 1) Segmento del cliente (fallback 'MIN')
    segmento = getattr(cliente, "tipo", "MIN").upper()

    # 2) Tasa de cambio activa
    try:
        tasa = (
            TasaCambio.objects
            .filter(moneda=moneda, activa=True)
            .latest("fecha_creacion")
        )
    except TasaCambio.DoesNotExist:
        raise ValidationError(f"No hay tasa de cambio activa para {moneda}.")

    # 3) Comisiones (mock json opcional)
    comisiones_path = os.path.join(settings.BASE_DIR, "static", "comisiones.json")
    try:
        with open(comisiones_path, "r", encoding="utf-8") as f:
            comisiones = json.load(f)
    except Exception:
        comisiones = []

    com = next((c for c in comisiones if c.get("currency") == moneda.codigo), None)
    comision_buy = Decimal(str(com["commission_buy"])) if com else Decimal("0")
    comision_sell = Decimal(str(com["commission_sell"])) if com else Decimal("0")

    # 4) Descuento por segmento
    tc = TasaComision.vigente_para_tipo(segmento)
    descuento_pct = Decimal(str(tc.porcentaje)) if tc else Decimal("0")

    # 5) Cálculo según tipo
    monto_operado = Decimal(monto_operado)

    if tipo == TipoTransaccionEnum.COMPRA:
        # Cliente compra USD/EUR => paga PYG (ingreso PYG para la casa)
        # Tasa base: compra del tablero +/- ajustes
        tasa_base = tasa.compra
        # aplicamos esquema simple: restar la porción de comisión según descuento
        com_final = comision_buy - (comision_buy * descuento_pct / 100)
        tasa_aplicada = tasa_base + com_final  # si tu política es sumar/ajustar
        comision = comision_buy
        monto_pyg = monto_operado * tasa_aplicada

    elif tipo == TipoTransaccionEnum.VENTA:
        # Cliente vende USD/EUR => la casa paga PYG (egreso PYG)
        tasa_base = tasa.venta if hasattr(tasa, "venta") else tasa.compra
        com_final = comision_sell - (comision_sell * descuento_pct / 100)
        tasa_aplicada = tasa_base - com_final  # política inversa en venta
        comision = comision_sell
        monto_pyg = monto_operado * tasa_aplicada

    else:
        raise ValidationError("Tipo de transacción inválido.")

    return {
        "tasa_aplicada": tasa_aplicada,
        "comision": comision,
        "monto_pyg": monto_pyg,
    }


# =========================
# Límites y creación
# =========================
def _check_limit_pyg(cliente, monto_pyg):
    """Límite por operación en PYG."""
    try:
        lim = LimitePYG.objects.get(cliente=cliente)
    except LimitePYG.DoesNotExist:
        return  # sin límite configurado

    if monto_pyg > lim.max_por_operacion:
        raise ValidationError(
            f"Operación en PYG ({monto_pyg}) excede el límite por operación ({lim.max_por_operacion})."
        )


def _sum_operado_en_periodo(cliente, moneda, desde):
    """Suma en MONEDA extranjera (no PYG) desde fecha dada."""
    return (
        Transaccion.objects.filter(
            cliente=cliente,
            moneda=moneda,  # <- FIX: antes usaba 'moneda_operada' (no existe en tu modelo)
            fecha__gte=desde,
            estado__in=[EstadoTransaccionEnum.PENDIENTE, EstadoTransaccionEnum.PAGADA],
        ).aggregate(total=Sum("monto_operado"))["total"]
        or 0
    )


def _check_limit_moneda(cliente, moneda, monto_operado):
    """Límites en la moneda extranjera (por operación y acumulados)."""
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
    Validaciones antes de crear transacción:
      1) Límite PYG por operación
      2) Límite por moneda extranjera (operación + mensual)
      3) Límites diarios/mensuales en PYG por tipo de cliente (CLIENT_LIMITS)
    """
    from commons.limits import CLIENT_LIMITS

    _check_limit_pyg(cliente, monto_pyg)
    _check_limit_moneda(cliente, moneda_operada, monto_operado)

    # límites por tipo de cliente
    tipo_map = {"MIN": "minorista", "CORP": "corporativo", "VIP": "vip"}
    tipo_cliente = tipo_map.get(getattr(cliente, "tipo", "MIN"), "minorista")
    limites = CLIENT_LIMITS.get(tipo_cliente, CLIENT_LIMITS["minorista"])

    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    estados_validos = [EstadoTransaccionEnum.PENDIENTE, EstadoTransaccionEnum.PAGADA]

    total_diario = (
        Transaccion.objects.filter(
            cliente=cliente,
            moneda=moneda_operada,
            fecha__date=hoy,
            estado__in=estados_validos,
        ).aggregate(total=Sum("monto_pyg"))["total"]
        or 0
    )
    total_mensual = (
        Transaccion.objects.filter(
            cliente=cliente,
            moneda=moneda_operada,
            fecha__date__gte=inicio_mes,
            fecha__date__lte=hoy,
            estado__in=estados_validos,
        ).aggregate(total=Sum("monto_pyg"))["total"]
        or 0
    )

    limite_diario = Decimal(str(limites["diario"]))
    limite_mensual = Decimal(str(limites["mensual"]))
    total_diario = Decimal(total_diario)
    total_mensual = Decimal(total_mensual)
    monto_pyg = Decimal(monto_pyg)

    if total_diario + monto_pyg > limite_diario:
        raise ValidationError(
            f"Límite diario alcanzado | total_diario: {total_diario} + monto_pyg: {monto_pyg} > limite_diario: {limite_diario}"
        )
    if total_mensual + monto_pyg > limite_mensual:
        raise ValidationError(
            f"Límite mensual alcanzado | total_mensual: {total_mensual} + monto_pyg: {monto_pyg} > limite_mensual: {limite_mensual}"
        )


def crear_transaccion(
    cliente, tipo, moneda, monto_operado, tasa_aplicada, comision, monto_pyg, medio_pago=None
):
    """
    Crea la transacción en estado PENDIENTE (sin movimientos aún).
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


# =========================
# Confirmar / Cancelar
# =========================
def confirmar_transaccion(transaccion: Transaccion):
    """
    Confirmar manualmente (fuera de Stripe).
    Crea movimiento y marca PAGADA.
    """
    if transaccion.estado != EstadoTransaccionEnum.PENDIENTE:
        raise ValidationError("Solo transacciones pendientes pueden confirmarse.")

    with dj_tx.atomic():
        transaccion.estado = EstadoTransaccionEnum.PAGADA
        transaccion.save(update_fields=["estado"])

        # Mapear a INGRESO/EGRESO en PYG según tipo de operación
        mov_tipo = (
            TipoMovimientoEnum.DEBITO
            if transaccion.tipo == TipoTransaccionEnum.COMPRA
            else TipoMovimientoEnum.CREDITO
        )

        Movimiento.objects.create(
            transaccion=transaccion,
            cliente=transaccion.cliente,
            tipo=mov_tipo,
            monto=transaccion.monto_pyg,
        )

    return transaccion


def cancelar_transaccion(transaccion: Transaccion):
    """Cancela una transacción pendiente."""
    if transaccion.estado != EstadoTransaccionEnum.PENDIENTE:
        raise ValidationError("Solo transacciones pendientes pueden cancelarse.")

    transaccion.estado = EstadoTransaccionEnum.CANCELADA
    transaccion.save(update_fields=["estado"])
    return transaccion


# =========================
# Stripe helpers
# =========================
def requiere_pago_tarjeta(tx: Transaccion) -> bool:
    """
    True cuando el flujo es 'el cliente paga a la casa de cambio en PYG'.
    Por defecto: COMPRA => Stripe OK. VENTA => no Stripe.
    """
    return str(tx.tipo) == str(TipoTransaccionEnum.COMPRA)


def crear_checkout_para_transaccion(tx: Transaccion) -> str:
    """
    Crea una Session de Checkout en PYG (zero-decimal).
    Para COMPRA: cobra el total en PYG (monto_pyg + comisión si corresponde).
    """
    if not requiere_pago_tarjeta(tx):
        raise ValueError("Esta transacción no requiere pago por tarjeta.")

    # Política de cobro: monto en PYG + comisión (ajustá si no querés cobrar comisión en Stripe)
    monto_pyg_total = (tx.monto_pyg or 0) + (tx.comision or 0)
    monto = Decimal(monto_pyg_total)
    if monto <= 0:
        raise ValueError("El monto a cobrar debe ser mayor a 0.")

    unit_amount = int(monto.quantize(Decimal("1"), rounding=ROUND_DOWN))  # PYG zero-decimal

    success_url = (
        f"{settings.SITE_URL}"
        f"{reverse('transacciones:pago_success')}"
        f"?session_id={{CHECKOUT_SESSION_ID}}&tx_id={tx.id}"
    )
    cancel_url = (
        f"{settings.SITE_URL}"
        f"{reverse('transacciones:pago_cancel')}"
        f"?tx_id={tx.id}"
    )

    nombre_producto = f"Transacción #{tx.id} - {tx.get_tipo_display()}"
    descripcion = (
        f"{tx.get_tipo_display()} {tx.monto_operado} {tx.moneda.codigo} "
        f"@ {tx.tasa_aplicada} | Cliente: {tx.cliente}"
    )

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "pyg",
                    "unit_amount": unit_amount,
                    "product_data": {"name": nombre_producto, "description": descripcion},
                },
                "quantity": 1,
            }
        ],
        metadata={
            "transaccion_id": str(tx.id),
            "cliente_id": str(tx.cliente_id),
            "tipo": str(tx.tipo),
            "moneda": tx.moneda.codigo,
            "monto_operado": str(tx.monto_operado),
            "tasa": str(tx.tasa_aplicada),
            "monto_pyg": str(tx.monto_pyg),
            "comision": str(tx.comision),
        },
        success_url=success_url,
        cancel_url=cancel_url,
    )

    changed = False
    if hasattr(tx, "stripe_session_id"):
        tx.stripe_session_id = session.id
        changed = True
    if hasattr(tx, "stripe_status"):
        tx.stripe_status = "checkout_created"
        changed = True
    if changed:
        tx.save(
            update_fields=[
                f for f in ["stripe_session_id", "stripe_status"] if hasattr(tx, f)
            ]
        )

    logger.info(f"[STRIPE] Checkout creada para tx #{tx.id}: {session.id}")
    return session.url


def verificar_pago_stripe(session_id: str) -> dict:
    """
    Verifica el estado de un pago en Stripe.
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "payment_status": session.payment_status,  # 'paid', 'unpaid', 'no_payment_required'
            "status": session.status,                  # 'complete', 'open', 'expired'
            "amount_total": session.amount_total,
            "customer_email": (
                session.customer_details.email if getattr(session, "customer_details", None) else None
            ),
            "payment_intent": session.payment_intent,
        }
    except stripe.error.StripeError as e:
        logger.error(f"[STRIPE] Error al verificar pago: {str(e)}")
        raise Exception(f"Error al verificar pago: {str(e)}")
