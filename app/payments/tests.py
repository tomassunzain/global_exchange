

from django.test import TestCase, Client
from django.urls import reverse
from .models import PaymentMethod
from clientes.models import Cliente
from django.contrib.auth import get_user_model

User = get_user_model()

class PaymentMethodModelTest(TestCase):
	"""
	Pruebas unitarias para el modelo PaymentMethod.
	"""
	def setUp(self):
		self.user = User.objects.create_user(email="test@test.com", password="1234")
		self.cliente = Cliente.objects.create(nombre="Cliente Test", tipo="MIN")
		self.cliente.usuarios.add(self.user)

	def test_create_payment_method(self):
		pm = PaymentMethod.objects.create(cliente=self.cliente, name="Tarjeta", description="Pago con tarjeta")
		self.assertEqual(str(pm), "Tarjeta")
		self.assertEqual(pm.cliente, self.cliente)


class PaymentMethodViewsTest(TestCase):
	"""
	Pruebas unitarias para las vistas de métodos de pago.
	"""
	def setUp(self):
		self.client = Client()
		self.user = User.objects.create_user(email="test@test.com", password="1234")
		self.cliente = Cliente.objects.create(nombre="Cliente Test", tipo="MIN")
		self.cliente.usuarios.add(self.user)
		self.client.login(email="test@test.com", password="1234")
		self.pm1 = PaymentMethod.objects.create(cliente=self.cliente, name="Tarjeta", description="Pago con tarjeta")
		self.pm2 = PaymentMethod.objects.create(cliente=self.cliente, name="Efectivo", description="Pago en efectivo")

	def test_list_methods_by_client(self):
		response = self.client.get(reverse('payments:paymentmethod_list'))
		self.assertContains(response, self.cliente.nombre)
		self.assertContains(response, self.pm1.name)
		self.assertContains(response, self.pm2.name)

	def test_create_payment_method_view(self):
		url = reverse('payments:paymentmethod_create') + f'?cliente={self.cliente.id}'
		response = self.client.post(url, {
			'name': 'Cheque',
			'description': 'Pago con cheque',
		})
		self.assertEqual(PaymentMethod.objects.filter(name='Cheque').count(), 1)

	def test_delete_view(self):
		response = self.client.post(reverse('payments:paymentmethod_delete', args=[self.pm1.pk]))
		self.assertEqual(PaymentMethod.objects.filter(pk=self.pm1.pk).count(), 0)

	def test_update_view(self):
		url = reverse('payments:paymentmethod_update', args=[self.pm2.pk])
		response = self.client.post(url, {
			'name': 'Efectivo Editado',
			'description': 'Editado',
		})
		self.pm2.refresh_from_db()
		self.assertEqual(self.pm2.name, 'Efectivo Editado')
