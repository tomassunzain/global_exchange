"""
Modelos y gestores personalizados para la aplicación de usuarios.

Define el modelo de usuario y el gestor de usuarios basado en email.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Gestor de usuarios personalizado.

    Permite crear usuarios usando el email como identificador principal.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Crea un usuario con email y contraseña.

        :param email: Correo electrónico único.
        :param password: Contraseña en texto plano.
        :param extra_fields: Campos adicionales para el usuario.
        :return: Instancia de usuario creada.
        :raises ValueError: Si no se proporciona email.
        """
        if not email:
            raise ValueError("El email es obligatorio.")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_superuser", False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """
        Crea un usuario estándar (no staff, no superuser).

        :param email: Correo electrónico único.
        :param password: Contraseña en texto plano.
        :param extra_fields: Campos adicionales para el usuario.
        :return: Instancia de usuario creada.
        """
        extra_fields.setdefault("is_staff", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, *args, **kwargs):
        """
        Bloquea la creación de superusuarios.

        :raises NotImplementedError: Siempre lanza excepción.
        """
        raise NotImplementedError("No está permitido crear superusuarios en este sistema.")


class User(AbstractUser):
    """
    Modelo de usuario personalizado basado en email.

    El campo 'username' se elimina y se usa 'email' como identificador principal.
    """

    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def save(self, *args, **kwargs):
        """
        Guarda el usuario forzando siempre `is_superuser=False`.

        :param args: Argumentos posicionales.
        :param kwargs: Argumentos de palabra clave.
        """
        self.is_superuser = False
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Representación legible del usuario.

        :return: Email del usuario.
        """
        return self.email
