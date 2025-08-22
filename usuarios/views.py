from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from .decorators import role_required
from .forms import RegistroForm, LoginForm, UserForm
from .models import Role, UserRole

User = get_user_model()

def dashboard_view(request):
    return render(request, "dashboard.html")


@login_required
def usuarios_list(request):
    usuarios = User.objects.all().order_by("-id")
    return render(request, "usuarios/usuarios_list.html", {"usuarios": usuarios})

@login_required
def usuario_edit(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = UserForm(request.POST, instance=usuario)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data["password"]:
                user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "Usuario actualizado.")
            return redirect("usuarios:usuarios_list")
    else:
        form = UserForm(instance=usuario)
    return render(request, "usuarios/usuario_form.html", {"form": form, "usuario": usuario})

@login_required
def usuario_delete(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        usuario.delete()
        messages.success(request, "Usuario eliminado.")
        return redirect("usuarios:usuarios_list")
    return render(request, "usuarios/usuario_delete_confirm.html", {"usuario": usuario})


def enviar_verificacion(user):
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
            enviar_verificacion(user)
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
            return redirect('usuarios:dashboard')
    else:
        form = LoginForm()
    return render(request, 'usuarios/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('usuarios:login')


@login_required
@role_required("Admin")
def roles_list(request):
    roles = Role.objects.all()
    return render(request, "usuarios/roles_list.html", {"roles": roles})


@login_required
def rol_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        if name:
            Role.objects.create(name=name, description=description)
            messages.success(request, "Rol creado.")
            return redirect("usuarios:roles_list")
    return render(request, "usuarios/rol_form.html")


@login_required
@role_required("Admin")
def rol_edit(request, role_id):
    role = get_object_or_404(Role, pk=role_id)
    if request.method == "POST":
        role.name = request.POST.get("name")
        role.description = request.POST.get("description")
        role.save()
        messages.success(request, "Rol actualizado.")
        return redirect("usuarios:roles_list")
    return render(request, "usuarios/rol_form.html", {"role": role})


@login_required
def rol_delete(request, role_id):
    role = get_object_or_404(Role, pk=role_id)
    if request.method == "POST":
        role.delete()
        messages.success(request, "Rol eliminado.")
        return redirect("usuarios:roles_list")
    return render(request, "usuarios/rol_delete_confirm.html", {"role": role})


@login_required
def asignar_rol_a_usuario(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    roles = Role.objects.all()
    if request.method == "POST":
        ids = request.POST.getlist("roles")
        UserRole.objects.filter(user=usuario).delete()
        for rid in ids:
            UserRole.objects.create(user=usuario, role_id=rid)
        messages.success(request, "Roles asignados.")
        return redirect("usuarios:roles_list")
    return render(request, "usuarios/asignar_rol.html", {"usuario": usuario, "roles": roles})