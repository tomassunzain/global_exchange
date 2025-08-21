from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import Group, Permission
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.views import LoginView

from .forms import RegistroForm, LoginForm

User = get_user_model()

def dashboard_view(request):
    return render(request, "dashboard.html")

def _enviar_verificacion(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    url = f"{settings.SITE_URL}/usuarios/verificar/{uid}/{token}/"
    asunto = "Verifica tu cuenta"
    cuerpo = (
        "¡Bienvenido/a!\n\n"
        "Para activar tu cuenta, hace clic en el siguiente enlace:\n"
        f"{url}\n\n"
        "Si no creaste esta cuenta, ignora este mensaje."
    )
    send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [user.email])


def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            user = User.objects.create_user(email=email, password=form.cleaned_data['password1'])
            user.is_active = False  # inactivo hasta verificar
            user.save()
            _enviar_verificacion(user)
            messages.success(request, "Registro exitoso. Revisa tu correo para activar la cuenta.")
            return redirect('usuarios:login')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})


def verificar_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        messages.error(request, "Enlace inválido.")
        return redirect('usuarios:login')

    if default_token_generator.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save()
        messages.success(request, "Cuenta activada correctamente. Ya podes iniciar sesion.")
        return redirect('usuarios:login')
    messages.error(request, "Token invalido o expirado.")
    return redirect('usuarios:login')


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            # verifica que sea user activo
            user = form.get_user()
            if not user.is_active:
                messages.error(request, "Tu cuenta aun no esta verificada.")
                return redirect('usuarios:login')
            login(request, user)
            return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'usuarios/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('usuarios:login')


@login_required
@permission_required('auth.view_group', raise_exception=True)
def roles_list(request):
    grupos = Group.objects.all().prefetch_related('permissions')
    return render(request, 'usuarios/roles_list.html', {'grupos': grupos})


@login_required
@permission_required('auth.change_group', raise_exception=True)
def rol_editar(request, group_id):
    grupo = get_object_or_404(Group, pk=group_id)
    permisos = Permission.objects.select_related('content_type').all()

    if request.method == 'POST':
        ids = request.POST.getlist('permissions')
        grupo.permissions.set(permisos.filter(id__in=ids))
        messages.success(request, "Permisos actualizados.")
        return redirect('usuarios:roles_list')

    return render(request, 'usuarios/rol_editar.html', {'grupo': grupo, 'permisos': permisos})


@login_required
@permission_required('usuarios.change_user', raise_exception=True)
def asignar_rol_a_usuario(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    grupos = Group.objects.all()
    if request.method == 'POST':
        ids = request.POST.getlist('groups')
        usuario.groups.set(grupos.filter(id__in=ids))
        messages.success(request, "Roles asignados.")
        return redirect('usuarios:usuarios_list')
    return render(request, 'usuarios/asignar_rol.html', {'usuario': usuario, 'grupos': grupos})

