from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        crea usuario con email y pass
        siempre is_superuser=False y is_staff=False.
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
        extra_fields.setdefault("is_staff", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, *args, **kwargs):
        """
        impedir superuser
        """
        raise NotImplementedError("No esta permitido crear superusuarios en este sistema.")

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def save(self, *args, **kwargs):
        # nunca superusuario
        self.is_superuser = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    def has_role(self, role_name: str) -> bool:
        return self.user_roles.filter(role__name=role_name).exists()

    def has_any_role(self, *role_names) -> bool:
        return self.user_roles.filter(role__name__in=role_names).exists()

    def get_roles(self) -> list[str]:
        return list(self.user_role.values_list("role__name", flat=True))

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "role")

    def __str__(self):
        return f"{self.user.email} → {self.role.name}"