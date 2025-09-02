"""
 Pruebas unitarias de usuarios
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Role, User, UserRole
from .forms import RegistroForm, UserCreateForm, RoleForm

class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(email="user1@example.com", password="pass12345")
        self.assertEqual(user.email, "user1@example.com")
        self.assertFalse(user.is_superuser)

    def test_user_str(self):
        user = User.objects.create_user(email="user2@example.com", password="pass12345")
        self.assertEqual(str(user), "user2@example.com")

class RoleModelTest(TestCase):
    def test_create_role(self):
        role = Role.objects.create(name="Admin", description="Administrador")
        self.assertEqual(str(role), "Admin")

class UserRoleModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user3@example.com", password="pass12345")
        self.role = Role.objects.create(name="Editor", description="Puede editar")

    def test_user_role_str(self):
        user_role = UserRole.objects.create(user=self.user, role=self.role)
        self.assertEqual(str(user_role), f"{self.user.email} → {self.role.name}")

class RegistroFormTest(TestCase):
    def test_valid_form(self):
        data = {
            "email": "nuevo@example.com",
            "password1": "pass12345",
            "password2": "pass12345"
        }
        form = RegistroForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_email(self):
        User.objects.create_user(email="existe@example.com", password="pass12345")
        data = {
            "email": "existe@example.com",
            "password1": "pass12345",
            "password2": "pass12345"
        }
        form = RegistroForm(data)
        self.assertFalse(form.is_valid())

    def test_passwords_do_not_match(self):
        data = {
            "email": "nuevo2@example.com",
            "password1": "pass12345",
            "password2": "diferente"
        }
        form = RegistroForm(data)
        self.assertFalse(form.is_valid())

class UserCreateFormTest(TestCase):
    def test_valid_user_create_form(self):
        data = {
            "email": "admin@example.com",
            "is_active": True,
            "password1": "pass12345",
            "password2": "pass12345"
        }
        form = UserCreateForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_user_create_form(self):
        data = {
            "email": "",
            "is_active": True,
            "password1": "pass12345",
            "password2": "pass12345"
        }
        form = UserCreateForm(data)
        self.assertFalse(form.is_valid())

class RoleFormTest(TestCase):
    def test_valid_role_form(self):
        data = {"name": "Supervisor", "description": "Supervisa usuarios"}
        form = RoleForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_role_form(self):
        data = {"name": "", "description": "Sin nombre"}
        form = RoleForm(data)
        self.assertFalse(form.is_valid())

class UsuariosViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="viewuser@example.com", password="testpass123", is_active=True)
        self.client = Client()
        self.client.force_login(self.user)
        self.role = Role.objects.create(name="Admin", description="Administrador")
        UserRole.objects.create(user=self.user, role=self.role)

    def test_usuarios_list_view(self):
        url = reverse("usuarios:usuarios_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.email)

    def test_usuario_create_view(self):
        url = reverse("usuarios:usuario_create")
        data = {
            "email": "nuevoadmin@example.com",
            "is_active": True,
            "password1": "pass12345",
            "password2": "pass12345"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="nuevoadmin@example.com").exists())

    def test_usuario_edit_view(self):
        url = reverse("usuarios:usuario_edit", args=[self.user.id])
        data = {"email": "editado@example.com", "is_active": True, "password": ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "editado@example.com")

    def test_usuario_delete_view(self):
        url = reverse("usuarios:usuario_delete", args=[self.user.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())
