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
        # VENTA: de moneda extranjera a PYG
        tc_venta = pb + comision_sell - (comision_sell * descuento / 100)
        tasa_aplicada = tc_venta
        comision = comision_sell
        monto_pyg = monto_operado * tc_venta
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


def confirmar_transaccion_con_otp(transaccion, user, raw_code, context_match=None):
    """
    Verifica un OTP para la transacción (purpose='transaction_debit') y si es válido
    procede a confirmar la transacción (crear movimiento y marcar PAGADA).

    Esta función no realiza redirecciones ni I/O; lanza ValidationError en caso de fallo.
    """
    from django.core.exceptions import ValidationError
    from mfa.services import verify_otp

    # Solo confirmar si está pendiente
    if transaccion.estado != EstadoTransaccionEnum.PENDIENTE:
        raise ValidationError("Solo transacciones pendientes pueden confirmarse.")

    # Verificar OTP
    ok, otp = verify_otp(user, 'transaction_debit', raw_code, context_match=context_match)
    if not ok:
        raise ValidationError('OTP inválido para la transacción.')

    # Si OK, delegar en confirmar_transaccion existente para crear movimiento y marcar PAGADA
    return confirmar_transaccion(transaccion)

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
    Aplica validaciones:
      1) PYG por operación
      2) Moneda extranjera (por operación + opcional diario/mensual)
      3) Límites diarios y mensuales por tipo de cliente (CLIENT_LIMITS)
    """
    from django.db.models import Sum
    from django.utils import timezone
    from commons.limits import CLIENT_LIMITS
    from transaccion.models import Transaccion

    _check_limit_pyg(cliente, monto_pyg)
    _check_limit_moneda(cliente, moneda_operada, monto_operado)

    # --- Validación de límites diarios y mensuales por tipo de cliente ---
    # Mapeo de tipo de cliente a clave de CLIENT_LIMITS
    tipo_map = {
        'MIN': 'minorista',
        'CORP': 'corporativo',
        'VIP': 'vip',
    }
    tipo_cliente = tipo_map.get(getattr(cliente, 'tipo', 'MIN'), 'minorista')
    limites = CLIENT_LIMITS.get(tipo_cliente, CLIENT_LIMITS['minorista'])

    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)

    estados_validos = [EstadoTransaccionEnum.PENDIENTE, EstadoTransaccionEnum.PAGADA]
    # Suma de transacciones del día (PYG) por moneda y estado válido
    total_diario = Transaccion.objects.filter(
        cliente=cliente,
        moneda=moneda_operada,
        fecha__date=hoy,
        estado__in=estados_validos
    ).aggregate(total=Sum('monto_pyg'))['total'] or 0

    # Suma de transacciones del mes (PYG) por moneda y estado válido
    total_mensual = Transaccion.objects.filter(
        cliente=cliente,
        moneda=moneda_operada,
        fecha__date__gte=inicio_mes,
        fecha__date__lte=hoy,
        estado__in=estados_validos
    ).aggregate(total=Sum('monto_pyg'))['total'] or 0

    from decimal import Decimal
    limite_diario = Decimal(str(limites['diario']))
    limite_mensual = Decimal(str(limites['mensual']))
    total_diario = Decimal(total_diario)
    total_mensual = Decimal(total_mensual)
    monto_pyg = Decimal(monto_pyg)

    if total_diario + monto_pyg > limite_diario:
        raise ValidationError(f"Límite diario alcanzado | total_diario: {total_diario} + monto_pyg: {monto_pyg} > limite_diario: {limite_diario}")
    if total_mensual + monto_pyg > limite_mensual:
        raise ValidationError(f"Límite mensual alcanzado | total_mensual: {total_mensual} + monto_pyg: {monto_pyg} > limite_mensual: {limite_mensual}")
