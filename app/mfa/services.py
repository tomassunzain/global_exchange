"""Servicios para generar y verificar OTPs (simulación por terminal)."""
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import MfaOtp, UserMfa
from django.db import transaction
import random
import logging
import sys

logger = logging.getLogger(__name__)


def _random_numeric_code(length=6):
    start = 10 ** (length - 1)
    end = (10 ** length) - 1
    return str(random.randint(start, end))


def generate_otp(user, purpose, method='email', destination=None, length=6, ttl_seconds=None, context=None, max_attempts=None):
    """Genera y persiste un OTP para un usuario. Muestra el código por terminal (simulación).

    Retorna la instancia `MfaOtp` creada (no incluye el código raw en producción).
    """
    if destination is None:
        # intentar leer destino del user.mfa_config si existe
        try:
            cfg = user.mfa_config
            destination = destination or cfg.destination or user.email
            method = method or cfg.method
        except UserMfa.DoesNotExist:
            destination = destination or user.email

    # Apply defaults from settings when parameters are not provided
    if ttl_seconds is None:
        ttl_seconds = getattr(settings, 'MFA_DEFAULT_TTL_SECONDS', 30)
    if max_attempts is None:
        max_attempts = getattr(settings, 'MFA_MAX_ATTEMPTS', 5)

    raw_code = _random_numeric_code(length=length)
    expires_at = timezone.now() + timedelta(seconds=ttl_seconds)

    with transaction.atomic():
        otp = MfaOtp.objects.create(
            user=user,
            purpose=purpose,
            expires_at=expires_at,
            attempts=0,
            max_attempts=max_attempts,
            method=method,
            destination=destination,
            context=context or {},
            code_hash='')
        otp.set_code(raw_code)
        otp.save(update_fields=['code_hash'])

    # Envío simulado: mostrar por terminal (logs)
    logger.info('=' * 60)
    logger.info(f'OTP GENERADO para user={user.email} purpose={purpose} expires_at={expires_at.isoformat()}')
    # Log at WARNING to increase visibility in dev logs
    logger.warning('=' * 60)
    logger.warning(f'OTP GENERADO para user={user.email} purpose={purpose} expires_at={expires_at.isoformat()}')
    logger.warning(f'Código (simulado): {raw_code}')
    logger.warning('=' * 60)
    # Also print directly to stdout and flush so the code is visible in terminal-based dev servers
    # Friendly email-like body (Spanish) printed to stdout/stderr and logged for developer testing
    email_body = (
        f"Hola {user.email},\n\n"
        f"El código que solicitaste para {purpose} es: {raw_code}\n\n"
        "Si no realizaste esta solicitud, por favor ignora este mensaje o contacta al administrador.\n\n"
        f"Este código expirará el {expires_at.isoformat()}\n"
    )

    try:
        print('=' * 60)
        print('----- MENSAJE SIMULADO (correo) -----')
        print(email_body)
        print('----- FIN MENSAJE -----')
        print('=' * 60)
        sys.stdout.flush()
    except Exception:
        pass
    try:
        print('=' * 60, file=sys.stderr)
        print('----- MENSAJE SIMULADO (correo) -----', file=sys.stderr)
        print(email_body, file=sys.stderr)
        print('----- FIN MENSAJE -----', file=sys.stderr)
        print('=' * 60, file=sys.stderr)
        sys.stderr.flush()
    except Exception:
        pass
    # Also log the compact form for quick discovery
    logger.warning(f"OTP PARA {user.email}: {raw_code} (expira: {expires_at.isoformat()})")

    return otp


def verify_otp(user, purpose, raw_code, context_match=None):
    """Verifica el código OTP más reciente para un usuario y propósito.

    Retorna (True, otp) si es válido; en caso contrario lanza ValidationError con detalle.
    """
    otps = MfaOtp.objects.filter(user=user, purpose=purpose, used=False).order_by('-created_at')
    if not otps.exists():
        raise ValidationError('No OTP disponible. Generá uno primero.')

    otp = otps.first()

    # Matchar contexto si se proporcionó
    if context_match and otp.context:
        for k, v in context_match.items():
            if otp.context.get(k) != v:
                raise ValidationError('OTP no corresponde al contexto esperado.')

    if otp.is_expired():
        raise ValidationError('OTP expirado.')

    if otp.attempts >= otp.max_attempts:
        raise ValidationError('Máximo de intentos alcanzado para este OTP.')

    # incrementar intentos y verificar
    otp.attempts += 1
    otp.save(update_fields=['attempts'])

    if otp.verify_code(raw_code):
        otp.used = True
        otp.save(update_fields=['used'])
        return True, otp

    raise ValidationError('Código OTP inválido.')
