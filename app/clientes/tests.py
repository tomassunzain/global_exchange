"""
 Pruebas unitarias de clientes
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Cliente
from .forms import ClienteForm, AsignarUsuariosAClienteForm

User = get_user_model()

class ClienteModelTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(email="testuser@example.com", password="testpass123")
		self.cliente = Cliente.objects.create(nombre="Empresa X", tipo="CORP")
		self.cliente.usuarios.add(self.user)

	def test_cliente_str(self):
		self.aEqual(str(self.cliente), "Empresa X (Corporativo)")

	def test_cliente_segmentos(self):
		self.assertIn(self.cliente.tipo, dict(Cliente.SEGMENTOS))

	def test_cliente_usuarios(self):
		self.assertIn(self.user, self.cliente.usuarios.all())


class ClienteFormTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(email="formuser@example.com", password="testpass123")

	def test_cliente_form_valid(self):
		data = {"nombre": "Empresa Y", "tipo": "VIP", "usuarios": [self.user.id]}
		form = ClienteForm(data)
		self.assertTrue(form.is_valid())

	def test_cliente_form_invalid(self):
		data = {"nombre": "", "tipo": "VIP"}
		form = ClienteForm(data)
		self.assertFalse(form.is_valid())


class AsignarUsuariosAClienteFormTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(email="asignaruser@example.com", password="testpass123")
		self.cliente = Cliente.objects.create(nombre="Empresa Z", tipo="MIN")

	def test_asignar_usuarios_form(self):
		data = {"usuarios": [self.user.id]}
		form = AsignarUsuariosAClienteForm(data, instance=self.cliente)
		self.assertTrue(form.is_valid())


class ClienteViewsTest(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(email="viewuser@example.com", password="testpass123")
		self.client.force_login(self.user)
		self.cliente = Cliente.objects.create(nombre="Empresa W", tipo="MIN")
		self.cliente.usuarios.add(self.user)

	def test_clientes_list_view(self):
		url = reverse("clientes:clientes_list")
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Empresa W")

	def test_cliente_create_view(self):
		url = reverse("clientes:cliente_create")
		data = {"nombre": "Empresa Nueva", "tipo": "VIP", "usuarios": [self.user.id]}
		response = self.client.post(url, data)
		self.assertEqual(response.status_code, 302)  # Redirige tras crear
		self.assertTrue(Cliente.objects.filter(nombre="Empresa Nueva").exists())

	def test_cliente_edit_view(self):
		url = reverse("clientes:cliente_edit", args=[self.cliente.id])
		data = {"nombre": "Empresa Editada", "tipo": "CORP", "usuarios": [self.user.id]}
		response = self.client.post(url, data)
		self.assertEqual(response.status_code, 302)
		self.cliente.refresh_from_db()
		self.assertEqual(self.cliente.nombre, "Empresa Editada")

	def test_cliente_delete_view(self):
		url = reverse("clientes:cliente_delete", args=[self.cliente.id])
		response = self.client.post(url)
		self.assertEqual(response.status_code, 302)
		self.assertFalse(Cliente.objects.filter(id=self.cliente.id).exists())
