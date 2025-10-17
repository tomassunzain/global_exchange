from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from app.usuarios.middleware import MfaRequiredMiddleware
from app.mfa.models import UserMfa

User = get_user_model()

class MfaMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = MfaRequiredMiddleware(lambda req: self.client.get(reverse('dashboard')))

        self.user_with_mfa = User.objects.create_user(username='testmfa', password='password123', email='testmfa@example.com')
        UserMfa.objects.create(user=self.user_with_mfa, mfa_method='email', is_active=True)

        self.user_without_mfa = User.objects.create_user(username='testnomfa', password='password123', email='testnomfa@example.com')

    def test_unauthenticated_user_is_not_redirected(self):
        """Los usuarios no autenticados no deben ser afectados por el middleware."""
        request = self.factory.get(reverse('dashboard'))
        request.user = self.user_with_mfa
        # Simulate logout
        request.user.is_anonymous = True
        
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200) # Should not redirect

    def test_user_without_mfa_can_access_protected_page(self):
        """Los usuarios sin MFA activado deben poder acceder a las páginas."""
        request = self.factory.get(reverse('dashboard'))
        request.user = self.user_without_mfa
        request.session = self.client.session
        
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_user_with_mfa_not_verified_is_redirected(self):
        """Los usuarios con MFA que no han verificado son redirigidos a la página de verificación."""
        request = self.factory.get(reverse('dashboard'))
        request.user = self.user_with_mfa
        request.session = self.client.session
        request.session['mfa_verified'] = False

        response = self.middleware(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login_verify'))

    def test_user_with_mfa_verified_can_access_protected_page(self):
        """Los usuarios con MFA que han verificado pueden acceder a las páginas."""
        request = self.factory.get(reverse('dashboard'))
        request.user = self.user_with_mfa
        request.session = self.client.session
        request.session['mfa_verified'] = True

        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_user_with_mfa_can_access_exempt_url(self):
        """Los usuarios con MFA pueden acceder a URLs exentas como la de verificación."""
        request = self.factory.get(reverse('login_verify'))
        request.user = self.user_with_mfa
        request.session = self.client.session
        request.session['mfa_verified'] = False

        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
