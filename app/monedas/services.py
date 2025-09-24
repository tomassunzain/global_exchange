import datetime
from decimal import Decimal
from django.db import transaction
from django.utils.dateparse import parse_datetime
from .models import Moneda, TasaCambio
import requests
from django.conf import settings


def obtener_tasas_desde_api():
    """Consume la API de tu app exchange"""
    try:
        response = requests.get(
            'http://localhost:8000/exchange/rates/',  # URL de tu API exchange
            params={'source': 'api'},  # Para forzar API externa
            timeout=10
        )
        response.raise_for_status()
        return response.json()['rates']  # Ajusta según el formato de respuesta

    except Exception as e:
        # Fallback a mock local
        response = requests.get(
            'http://localhost:8000/exchange/rates/',
            params={'source': 'local'},  # Usar mock
            timeout=5
        )
        return response.json()['rates']
def upsert_tasas_desde_payload(payload: list[dict[str, str]]):
    """
    payload: lista de dicts con keys: currency, buy, sell, base_currency, source, timestamp
    """
    # Moneda base del sistema
    base = Moneda.objects.filter(es_base=True).first()
    system_base = base.codigo if base else None

    if payload:
        api_base = payload[0].get('base_currency')
        if system_base and api_base and api_base != system_base:
            # Levantamos excepción o retornamos estado para avisar en UI
            return {'ok': False, 'reason': f'Base API {api_base} distinta a base sistema {system_base}'}

    cod_to_mon = {m.codigo: m for m in Moneda.objects.all()}
    with transaction.atomic():
        for d in payload:
            cod = d['currency'].upper()
            if cod not in cod_to_mon:
                # Podés omitir crear automáticamente y solo registrar warning
                continue
            m = cod_to_mon[cod]
            compra = Decimal(d['buy'])
            venta  = Decimal(d['sell'])
            ts = parse_datetime(d.get('timestamp'))  # 2025-09-13T22:15:00Z

            # Variación respecto a la última activa
            prev = (TasaCambio.objects
                    .filter(moneda=m, activa=True)
                    .order_by('-fecha_actualizacion')
                    .first())
            variacion = Decimal('0')
            if prev and prev.venta:
                try:
                    variacion = ( (venta - prev.venta) / prev.venta * Decimal('100') ).quantize(Decimal('0.01'))
                except Exception:
                    variacion = Decimal('0')

            # Desactivar la anterior y crear nueva
            TasaCambio.objects.filter(moneda=m, activa=True).update(activa=False)

            TasaCambio.objects.create(
                moneda=m,
                compra=compra,
                venta=venta,
                variacion=variacion,
                base_codigo=d.get('base_currency', system_base or ''),
                fuente=d.get('source', ''),
                ts_fuente=ts,
                activa=True,
            )

    return {'ok': True}


def upsert_tasas_desde_api():
    """Obtiene tasas desde la API y las guarda en BD"""
    # Obtener datos de la API exchange
    datos_api = obtener_tasas_desde_api()

    # Transformar al formato que espera tu servicio
    payload = []
    for tasa in datos_api:
        payload.append({
            'currency': tasa['codigo_moneda'],
            'buy': str(tasa['compra']),
            'sell': str(tasa['venta']),
            'base_currency': 'PYG',
            'source': tasa.get('fuente', 'API Exchange'),
            'timestamp': tasa.get('fecha_actualizacion')
        })

    # Usar tu servicio existente
    return upsert_tasas_desde_payload(payload)