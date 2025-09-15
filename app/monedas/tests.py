"""
Tests de la app 'monedas' para Global Exchange.

Cubre:
- Modelo Moneda (normalización, unicidad de base).
- Vistas de CRUD (crear base única, evitar borrar base).
- Vista 'tasa_cambio' (tablero: usa últimas tasas o mock si no hay datos).
- Filtro de template 'money'.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db import IntegrityError, connection
from django.test import TestCase, Client, skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone

from .models import Moneda, TasaCambio
from .templatetags.monedas_extra import money  # si usaste 'monedas_extras', importá de ese nombre


class BaseTestCase(TestCase):
    def setUp(self):
        # Usuario para autenticación (las vistas requieren login)
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email="admin@example.com",
            password="pass12345"
        )
        self.client = Client()
        self.client.login(email="admin@example.com", password="pass12345")

        # Moneda base del sistema
        self.pyg = Moneda.objects.create(
            codigo="PYG", nombre="Guaraní paraguayo", simbolo="₲",
            decimales=0, activa=True, es_base=True
        )


class MonedaModelTests(BaseTestCase):
    def test_codigo_se_normaliza_a_mayusculas(self):
        usd = Moneda.objects.create(
            codigo="usd", nombre="Dólar estadounidense", simbolo="$",
            decimales=2, activa=True, es_base=False
        )
        self.assertEqual(usd.codigo, "USD")

    def test_str(self):
        self.assertEqual(str(self.pyg), "PYG - Guaraní paraguayo")

    @skipUnlessDBFeature('supports_partial_indexes')
    def test_unicidad_moneda_base_en_bd(self):
        """
        Verifica que la restricción parcial (es_base=True) impide dos bases.
        Este test se salta si la BD no soporta índices parciales.
        """
        with self.assertRaises(IntegrityError):
            Moneda.objects.create(
                codigo="USD", nombre="Dólar", simbolo="$",
                decimales=2, activa=True, es_base=True
            )


class MonedaViewsTests(BaseTestCase):
    def test_list_status_ok(self):
        url = reverse('monedas:monedas_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Monedas")
        self.assertContains(resp, "PYG")

    def test_crear_moneda_y_marcar_como_base_desmarca_anterior(self):
        url = reverse('monedas:moneda_create')
        data = {
            "codigo": "USD",
            "nombre": "Dólar estadounidense",
            "simbolo": "$",
            "decimales": 2,
            "activa": True,
            "es_base": True,
        }
        resp = self.client.post(url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        usd = Moneda.objects.get(codigo="USD")
        self.pyg.refresh_from_db()
        self.assertTrue(usd.es_base)
        self.assertFalse(self.pyg.es_base)  # la view desmarca la anterior

    def test_no_permite_eliminar_moneda_base(self):
        url = reverse('monedas:moneda_delete', args=[self.pyg.id])
        resp = self.client.post(url, follow=True)
        # redirige a la lista con mensaje de error
        self.assertEqual(resp.status_code, 200)
        messages = list(get_messages(resp.wsgi_request))
        self.assertTrue(any("moneda base" in str(m) for m in messages))
        # sigue existiendo
        self.assertTrue(Moneda.objects.filter(id=self.pyg.id).exists())


class MoneyFilterTests(TestCase):
    def test_money_formatea_con_decimales_y_miles(self):
        # 1234.567 con 2 decimales → "1.234,57" (formato estilo es-PY)
        s = money(Decimal("1234.567"), 2)
        self.assertEqual(s, "1.234,57")

    def test_money_cero_decimales(self):
        s = money(Decimal("7400.00"), 0)
        self.assertEqual(s, "7.400")


class TasaCambioViewTests(BaseTestCase):
    def test_dashboard_con_mock_cuando_no_hay_datos(self):
        url = reverse('monedas:dashboard_tasas')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Debe mostrar monedas del mock (USD/EUR) y la base del sistema
        self.assertContains(resp, "USD")
        self.assertContains(resp, "EUR")
        self.assertContains(resp, "Base del sistema:")  # badge

    def test_dashboard_toma_ultima_por_moneda(self):
        # Creamos monedas operables
        usd = Moneda.objects.create(
            codigo="USD", nombre="Dólar", simbolo="$", decimales=0, activa=True
        )
        eur = Moneda.objects.create(
            codigo="EUR", nombre="Euro", simbolo="€", decimales=0, activa=True
        )
        # Dos tasas para USD con timestamps diferentes
        t1 = TasaCambio.objects.create(moneda=usd, compra=7000, venta=7100, variacion=0, activa=True)
        # forzamos que t1 sea más vieja
        TasaCambio.objects.filter(pk=t1.pk).update(fecha_actualizacion=timezone.now() - timezone.timedelta(hours=1))
        t2 = TasaCambio.objects.create(moneda=usd, compra=7300, venta=7400, variacion=0, activa=True)
        # para eur, 8000/8200
        TasaCambio.objects.create(moneda=eur, compra=8000, venta=8200, variacion=0, activa=True)

        url = reverse('monedas:dashboard_tasas')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # Debe aparecer solo una fila de USD (la última). Comprobamos por texto del código.
        usd_count = resp.content.decode('utf-8').count("USD")
        self.assertGreaterEqual(usd_count, 1)  # aparece USD
        # y debe ser la última tasa: venta 7400 → formateada con 0 decimales = "7.400"
        self.assertIn("7.400", resp.content.decode('utf-8'))
