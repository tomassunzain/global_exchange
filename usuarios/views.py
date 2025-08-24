"""
Vistas y lógica de negocio para la aplicación de usuarios.

Incluye vistas para registro, login, verificación de cuenta y gestión de sesiones y roles.
"""

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
from .forms import AsignarClientesAUsuarioForm, RegistroForm, LoginForm, UserForm, AsignarRolForm, RoleForm, UserCreateForm
from .models import Role, UserRole
from clientes.models import Cliente

User = get_user_model()


def dashboard_view(request):
    # Estadísticas para el dashboard
    context = {}

    if request.user.is_authenticated:
        from django.db.models import Count

        # Contar usuarios
        total_usuarios = User.objects.count()
        usuarios_activos = User.objects.filter(is_active=True).count()

        # Contar roles
        total_roles = Role.objects.count()

        # Contar clientes
        total_clientes = Cliente.objects.count()

        context.update({
            'total_usuarios': total_usuarios,
            'total_clientes' : total_clientes,
            'usuarios_activos': usuarios_activos,
            'total_roles': total_roles,
            'tasa_usd': 7300,
            'tasa_eur': 8000,
            'tasa_timestamp': '2023-10-10T12:00:00Z'
        })

    return render(request, "dashboard.html", context)


@login_required
@role_required("Admin")
def usuario_create(request):
    """Vista para crear usuarios desde el panel de administración"""
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Usuario {user.email} creado exitosamente.")
            return redirect("usuarios:usuarios_list")
    else:
        form = UserCreateForm()
        # Por defecto, los usuarios creados desde admin están activos
        form.fields['is_active'].initial = True

    return render(request, "usuarios/usuario_form.html", {"form": form, "usuario": None})


@login_required
def usuarios_list(request):
    from django.core.paginator import Paginator

    # Obtener parámetros de búsqueda y filtros
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    role_filter = request.GET.get('role', '')

    # Consulta base
    usuarios = User.objects.all()

    # Aplicar filtros
    if search_query:
        usuarios = usuarios.filter(email__icontains=search_query)

    if status_filter == 'active':
        usuarios = usuarios.filter(is_active=True)
    elif status_filter == 'inactive':
        usuarios = usuarios.filter(is_active=False)

    if role_filter:
        usuarios = usuarios.filter(user_roles__role__name=role_filter).distinct()

    # Ordenar por fecha de creación (más recientes primero)
    usuarios = usuarios.order_by("-date_joined")

    # Paginación
    paginator = Paginator(usuarios, 10)  # 10 usuarios por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Obtener todos los roles para el filtro
    roles = Role.objects.all()

    context = {
        "usuarios": page_obj,
        "page_obj": page_obj,
        "roles": roles,
        "search_query": search_query,
        "status_filter": status_filter,
        "role_filter": role_filter,
        "total_usuarios": usuarios.count(),
    }

    return render(request, "usuarios/usuarios_list.html", context)


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
            return redirect('usuarios:dashboard')
    else:
        form = LoginForm()
    return render(request, 'usuarios/login.html', {'form': form})

def logout_view(request):
    """
    Vista para cerrar la sesión del usuario.

    :param request: HttpRequest.
    :return: Redirección a la página de login.
    """
    logout(request)
    return redirect('usuarios:login')


@login_required
@role_required("Admin")
def roles_list(request):
    """
    Vista para listar los roles (grupos) existentes.

    :param request: HttpRequest.
    :return: HttpResponse con la lista de roles.
    """
    roles = Role.objects.all()
    return render(request, "usuarios/roles_list.html", {"roles": roles})


@login_required
@role_required("Admin")
def rol_create(request):
    if request.method == "POST":
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Rol creado exitosamente.")
            return redirect("usuarios:roles_list")
    else:
        form = RoleForm()
    return render(request, "usuarios/rol_form.html", {"form": form})


@login_required
@role_required("Admin")
def rol_edit(request, role_id):
    """
   Vista para editar los permisos de un rol (grupo).

   :param request: HttpRequest.
   :param group_id: ID del grupo a editar.
   :return: HttpResponse con el formulario de edición o redirección.
   """
    role = get_object_or_404(Role, pk=role_id)
    if request.method == "POST":
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, "Rol actualizado exitosamente.")
            return redirect("usuarios:roles_list")
    else:
        form = RoleForm(instance=role)
    return render(request, "usuarios/rol_form.html", {"form": form, "role": role})


@login_required
@role_required("Admin")
def rol_delete(request, role_id):
    role = get_object_or_404(Role, pk=role_id)

    if request.method == "POST":
        # Contar usuarios afectados antes de eliminar
        users_count = role.user_roles.count()
        affected_users = [ur.user.email for ur in role.user_roles.all()]

        # Eliminar el rol (esto también eliminará las relaciones UserRole por CASCADE)
        role_name = role.name
        role.delete()

        # Mensaje de éxito diferente según si había usuarios asignados
        if users_count > 0:
            messages.success(
                request,
                f'Rol "{role_name}" eliminado exitosamente. '
                f'{users_count} usuario(s) ya no tienen este rol asignado: {", ".join(affected_users[:3])}'
                + (f' y {users_count - 3} más.' if users_count > 3 else '.')
            )
        else:
            messages.success(request, f'Rol "{role_name}" eliminado exitosamente.')

        return redirect("usuarios:roles_list")

    # Para GET request, mostrar página de confirmación
    return render(request, "usuarios/rol_delete_confirm.html", {"role": role})


@login_required
@role_required("Admin")
def asignar_rol_a_usuario(request, user_id):
    """
    Vista para asignar roles (grupos) a un usuario.

    :param request: HttpRequest.
    :param user_id: ID del usuario.
    :return: HttpResponse con el formulario de asignación o redirección.
    """
    usuario = get_object_or_404(User, pk=user_id)

    if request.method == "POST":
        form = AsignarRolForm(request.POST, user=usuario)
        if form.is_valid():
            # Limpiar roles actuales del usuario
            UserRole.objects.filter(user=usuario).delete()

            # Asignar nuevos roles seleccionados
            selected_roles = form.cleaned_data['roles']
            for role_id in selected_roles:
                UserRole.objects.create(user=usuario, role_id=role_id)

            if selected_roles:
                messages.success(request, f"Roles asignados correctamente a {usuario.email}.")
            else:
                messages.info(request, f"Se eliminaron todos los roles de {usuario.email}.")
            return redirect("usuarios:usuarios_list")
    else:
        form = AsignarRolForm(user=usuario)

    return render(request, "usuarios/asignar_rol.html", {
        "form": form,
        "usuario": usuario
    })


@login_required
def ver_usuario_roles(request, user_id):
    """Vista para ver los roles de un usuario específico"""
    usuario = get_object_or_404(User, pk=user_id)
    roles_usuario = UserRole.objects.filter(user=usuario).select_related('role')

    return render(request, "usuarios/usuario_roles.html", {
        "usuario": usuario,
        "roles_usuario": roles_usuario
    })

@login_required
def asignar_clientes_a_usuario(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = AsignarClientesAUsuarioForm(request.POST, usuario=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f"Clientes asignados a {usuario.email}.")
            return redirect("usuarios:usuarios_list")
    else:
        form = AsignarClientesAUsuarioForm(usuario=usuario)
    return render(request, "usuarios/asignar_clientes.html", {"form": form, "usuario": usuario})

