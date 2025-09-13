from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Cliente
from commons.enums import EstadoRegistroEnum
from .forms import AsignarUsuariosAClienteForm, ClienteForm
from usuarios.decorators import role_required

@login_required
@role_required("Admin")
def clientes_list(request):
    """
    Vista que muestra la lista de clientes registrados.
    Args:
        request: HttpRequest
    Returns:
        HttpResponse con la lista de clientes.
    """
        # Filtro para mostrar/ocultar eliminados
    show_deleted = request.GET.get('show_deleted', '0') == '1'

    # Consulta base
    clientes = Cliente.objects.all()
    if not show_deleted:
        clientes = clientes.filter(estado=EstadoRegistroEnum.ACTIVO.value)
    clientes = clientes.order_by("-id")
    return render(request, "clientes/clientes_list.html", {"clientes": clientes, "show_deleted": show_deleted})

@login_required
@role_required("Admin")
def cliente_create(request):
    """
    Vista para crear un nuevo cliente.
    Args:
        request: HttpRequest
    Returns:
        HttpResponse con el formulario o redirección.
    """
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente creado exitosamente.")
            return redirect("clientes:clientes_list")
    else:
        form = ClienteForm()
    return render(request, "clientes/cliente_form.html", {"form": form})

@login_required
@role_required("Admin")
def cliente_edit(request, cliente_id):
    """
    Vista para editar un cliente existente.
    Args:
        request: HttpRequest
        cliente_id: ID del cliente a editar.
    Returns:
        HttpResponse con el formulario de edición o redirección.
    """
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente actualizado.")
            return redirect("clientes:clientes_list")
    else:
        form = ClienteForm(instance=cliente)
    return render(request, "clientes/cliente_form.html", {"form": form, "cliente": cliente})

@login_required
@role_required("Admin")
def cliente_delete(request, cliente_id):
    """
    Vista para eliminar un cliente.
    Args:
        request: HttpRequest
        cliente_id: ID del cliente a eliminar.
    Returns:
        HttpResponse con la confirmación de eliminación.
    """
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == "POST":
        cliente.estado = EstadoRegistroEnum.ELIMINADO.value
        cliente.save()
        messages.success(request, "Cliente eliminado lógicamente.")
        return redirect("clientes:clientes_list")
    return render(request, "clientes/cliente_delete_confirm.html", {"cliente": cliente})

@login_required
@role_required("Admin")
def cliente_restore(request, cliente_id):
    """
    Vista para restaurar un cliente eliminado lógicamente.
    """
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == "POST":
        cliente.estado = EstadoRegistroEnum.ACTIVO.value
        cliente.save()
        messages.success(request, "Cliente restaurado correctamente.")
        return redirect("clientes:clientes_list")
    return render(request, "clientes/cliente_restore_confirm.html", {"cliente": cliente})

@login_required
@role_required("Admin")
def seleccionar_cliente(request, cliente_id):
    """
    Vista para seleccionar un cliente activo.
    Args:
        request: HttpRequest
        cliente_id: ID del cliente a seleccionar.
    Returns:
        HttpResponse redirigiendo al dashboard.
    """
    cliente = get_object_or_404(Cliente, pk=cliente_id, usuarios=request.user)
    request.session["cliente_activo"] = cliente.id
    messages.success(request, f"Ahora estás operando como cliente: {cliente.nombre}")
    return redirect("dashboard")

@login_required
@role_required("Admin")
def asignar_usuarios_a_cliente(request, cliente_id):
    """
    Vista para asignar usuarios a un cliente.
    Args:
        request: HttpRequest
        cliente_id: ID del cliente al que se asignarán usuarios.
    Returns:
        HttpResponse con el formulario o redirección.
    """
    cliente= get_object_or_404(Cliente, pk=cliente_id)
    if request.method == "POST":
        form = AsignarUsuariosAClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f"Usuarios asignados al cliente: {cliente.nombre}.")
            return redirect("clientes:clientes_list")
    else:
        form = AsignarUsuariosAClienteForm(instance=cliente)
    return render(request, "clientes/asignar_usuarios_a_cliente.html", {"form": form, "cliente": cliente})
