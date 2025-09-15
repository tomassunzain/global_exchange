
from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Moneda
from .forms import MonedaForm

class MonedaModeloTest(TestCase):
	"""
	Pruebas unitarias para el modelo Moneda.
	"""
	def test_creacion_moneda_valida(self):
		"""
		Verifica que se pueda crear una moneda válida y que sus atributos sean correctos.
		"""
		moneda = Moneda.objects.create(
			codigo='USD', nombre='Dólar estadounidense', simbolo='$', decimales=2, activa=True, es_base=True
		)
		self.assertEqual(moneda.codigo, 'USD')
		self.assertEqual(moneda.nombre, 'Dólar estadounidense')
		self.assertEqual(moneda.simbolo, '$')
		self.assertEqual(moneda.decimales, 2)
		self.assertTrue(moneda.activa)
		self.assertTrue(moneda.es_base)

	def test_codigo_iso_en_mayusculas(self):
		"""
		Verifica que el campo 'codigo' se almacene en mayúsculas si se ingresa correctamente.
		"""
		moneda = Moneda.objects.create(
			codigo='EUR', nombre='Euro', simbolo='€', decimales=2, activa=True, es_base=False
		)
		self.assertEqual(moneda.codigo, 'EUR')

	def test_codigo_iso_invalido(self):
		"""
		Verifica que un código ISO inválido lance un ValidationError.
		"""
		moneda = Moneda(
			codigo='usd$', nombre='Dólar', simbolo='$', decimales=2, activa=True, es_base=False
		)
		with self.assertRaises(ValidationError):
			moneda.full_clean()

	def test_unicidad_moneda_base(self):
		"""
		Verifica que solo pueda existir una moneda base en el sistema.
		"""
		Moneda.objects.create(
			codigo='PYG', nombre='Guaraní', simbolo='₲', decimales=0, activa=True, es_base=True
		)
		moneda2 = Moneda(
			codigo='BRL', nombre='Real', simbolo='R$', decimales=2, activa=True, es_base=True
		)
		with self.assertRaises(Exception):
			moneda2.save()

	def test_str_moneda(self):
		"""
		Verifica la representación en string de una moneda.
		"""
		moneda = Moneda.objects.create(
			codigo='ARS', nombre='Peso argentino', simbolo='$', decimales=2, activa=True, es_base=False
		)
		self.assertEqual(str(moneda), 'ARS - Peso argentino')

class MonedaFormTest(TestCase):
	"""
	Pruebas unitarias para el formulario MonedaForm.
	"""
	def test_formulario_valido(self):
		"""
		Verifica que el formulario sea válido con datos correctos.
		"""
		datos = {
			'codigo': 'CLP',
			'nombre': 'Peso chileno',
			'simbolo': '$',
			'decimales': 0,
			'activa': True,
			'es_base': False,
		}
		form = MonedaForm(data=datos)
		self.assertTrue(form.is_valid())

	def test_formulario_codigo_invalido(self):
		"""
		Verifica que el formulario sea inválido si el código no cumple el formato ISO 4217.
		"""
		datos = {
			'codigo': '123',
			'nombre': 'Moneda inválida',
			'simbolo': '?',
			'decimales': 2,
			'activa': True,
			'es_base': False,
		}
		form = MonedaForm(data=datos)
		self.assertFalse(form.is_valid())
		self.assertIn('codigo', form.errors)

	def test_formulario_decimales_fuera_de_rango(self):
		"""
		Verifica que el formulario sea inválido si la cantidad de decimales está fuera del rango permitido.
		"""
		datos = {
			'codigo': 'MXN',
			'nombre': 'Peso mexicano',
			'simbolo': '$',
			'decimales': 10,
			'activa': True,
			'es_base': False,
		}
		form = MonedaForm(data=datos)
		self.assertFalse(form.is_valid())
		self.assertIn('decimales', form.errors)
