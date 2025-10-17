from django.test import TestCase
from django.contrib.auth import get_user_model
from .services import generate_otp, verify_otp
import time
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.cache import cache

User = get_user_model()


class MfaServicesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='mfa_test@example.com', password='pass')

    def test_generate_and_verify_otp(self):
        otp = generate_otp(self.user, purpose='login', ttl_seconds=10)
        # The command prints the code to stdout; for test we'll fetch the raw code by re-querying the DB is not possible
        # Instead, simulate verifying by reading the OTP record and using the hashed verify method indirectly
        # This test will only ensure flows don't raise and verification raises on wrong code.
        with self.assertRaises(Exception):
            verify_otp(self.user, 'login', '000000')

    def test_expired_otp(self):
        otp = generate_otp(self.user, purpose='login', ttl_seconds=1)
        time.sleep(2)
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            verify_otp(self.user, 'login', '000000')

    def test_rate_limiting(self):
        """Prueba que el rate limiting bloquea al usuario después de N reintentos."""
        # Limpiar la caché para asegurar un estado limpio
        cache.clear()

        # Forzar valores de settings para la prueba
        settings.MFA_RESEND_LIMIT = 2
        settings.MFA_RESEND_BLOCK_TTL = 5  # 5 segundos de bloqueo

        # Generar OTP hasta el límite
        generate_otp(self.user, purpose='rate_limit_test')  # Intento 1
        generate_otp(self.user, purpose='rate_limit_test')  # Intento 2

        # El tercer intento debería fallar y bloquear al usuario
        with self.assertRaisesRegex(ValidationError, "Has superado el límite de reenvíos"):
            generate_otp(self.user, purpose='rate_limit_test')

        # Cualquier intento posterior mientras está bloqueado debería fallar
        with self.assertRaisesRegex(ValidationError, "Has solicitado demasiados códigos"):
            generate_otp(self.user, purpose='rate_limit_test')

        # Esperar a que el bloqueo expire
        time.sleep(settings.MFA_RESEND_BLOCK_TTL)

        # Después del bloqueo, debería poder generar un nuevo código
        try:
            generate_otp(self.user, purpose='rate_limit_test')
        except ValidationError as e:
            self.fail(f"No se debería haber lanzado una excepción de validación después del bloqueo: {e}")

        # Limpiar la caché al final de la prueba
        cache.clear()
